"""MOOX API Client for MOOX Track.

Copyright 2025 MOOX SRLS
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, TypedDict

import aiohttp
from aiohttp import ClientSession, ClientTimeout

LOGIN_RETRY_DELAY = 30.0
LOGIN_BACKOFF_MULTIPLIER = 1.5
MAX_BACKOFF_EXPONENT = 5
AUTH_INTERNAL_RETRIES = 3


class MooxException(Exception):
    """Base exception for MOOX API errors."""


class MooxAuthenticationException(MooxException):
    """Invalid credentials - requires user intervention."""


class MooxSessionExpiredException(MooxException):
    """Session expired - will re-authenticate automatically."""


class MooxConnectionException(MooxException):
    """Transient connection error - will retry automatically."""


class DeviceModel(TypedDict, total=False):
    """Device object from the API."""

    id: int
    name: str
    model: str
    status: str
    attributes: dict[str, Any]


class PositionModel(TypedDict, total=False):
    """Position object from the API."""

    deviceId: int
    latitude: float
    longitude: float
    altitude: float
    accuracy: float
    course: float
    speed: float
    attributes: dict[str, Any]


class GeofenceModel(TypedDict, total=False):
    """Geofence object from the API."""

    id: int
    name: str
    area: str
    attributes: dict[str, Any]


class EventModel(TypedDict, total=False):
    """Event object from the API."""

    deviceId: int
    type: str
    eventTime: str
    attributes: dict[str, Any]


class ServerModel(TypedDict, total=False):
    """Server information from the API."""

    id: int
    registration: str
    version: str
    attributes: dict[str, Any]


class MooxClient:
    """MOOX API client for communication with MOOX Track server."""

    CONNECT_TIMEOUT = 10.0
    TOTAL_TIMEOUT = 30.0

    def __init__(
        self,
        client_session: ClientSession,
        host: str,
        port: int,
        username: str,
        password: str,
        ssl: bool = True,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the MOOX API client."""
        self._session = client_session
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._ssl = ssl
        self._verify_ssl = verify_ssl
        self._base_url = f"{'https' if ssl else 'http'}://{host}:{port}/api"
        self._authenticated = False
        self._auth_lock = asyncio.Lock()
        self._ws_session: aiohttp.ClientWebSocketResponse | None = None
        self._ws_task: asyncio.Task[None] | None = None
        self._timeout = ClientTimeout(
            connect=self.CONNECT_TIMEOUT,
            total=self.TOTAL_TIMEOUT,
        )
        self._login_attempt_count = 0
        self._last_login_attempt: datetime | None = None
        self._ever_authenticated = False
        self._session_expiration_in_progress = False

    def _mark_session_authenticated(self) -> None:
        """Mark the current session as authenticated."""
        self._authenticated = True
        self._ever_authenticated = True
        self._session_expiration_in_progress = False
        self._login_attempt_count = 0

    def _clear_auth_state_for_reauth(self) -> None:
        """Clear auth state for re-authentication while preserving history."""
        self._authenticated = False
        self._session_expiration_in_progress = True
        self._clear_session_cookies()

    def _reset_for_credential_failure(self) -> None:
        """Full reset after confirmed credential failure."""
        self._authenticated = False
        self._ever_authenticated = False
        self._session_expiration_in_progress = False
        self._clear_session_cookies()

    def _clear_session_cookies(self) -> None:
        """Clear session cookies."""
        try:
            self._session.cookie_jar.clear()
        except Exception:
            pass

    @property
    def base_url(self) -> str:
        """Return the base URL for the MOOX API."""
        return self._base_url

    @property
    def ever_authenticated(self) -> bool:
        """Return True if credentials have ever worked."""
        return self._ever_authenticated

    async def _wait_for_login_retry(self) -> None:
        """Wait with exponential backoff before retry."""
        if self._last_login_attempt is None:
            return

        elapsed = (datetime.now() - self._last_login_attempt).total_seconds()
        exponent = max(self._login_attempt_count - 2, 0)
        base_delay = LOGIN_RETRY_DELAY * (
            LOGIN_BACKOFF_MULTIPLIER ** min(exponent, MAX_BACKOFF_EXPONENT)
        )
        if elapsed < base_delay:
            await asyncio.sleep(base_delay - elapsed)

    async def _authenticate(
        self, *, skip_rate_limit: bool = False, is_reauth: bool = False
    ) -> None:
        """Authenticate with the MOOX server."""
        if self._authenticated:
            return

        async with self._auth_lock:
            if self._authenticated:
                return

            self._login_attempt_count += 1

            if not skip_rate_limit:
                await self._wait_for_login_retry()
            self._last_login_attempt = datetime.now()

            last_error: Exception | None = None
            for auth_attempt in range(AUTH_INTERNAL_RETRIES):
                try:
                    if is_reauth or auth_attempt > 0:
                        self._clear_session_cookies()

                    payload = {
                        "email": self._username,
                        "password": self._password,
                        "remember_me": "true",
                    }

                    async with self._session.post(
                        f"{self._base_url}/session",
                        json=payload,
                        ssl=self._verify_ssl if self._ssl else False,
                        timeout=self._timeout,
                    ) as response:
                        if response.status == 200:
                            self._mark_session_authenticated()
                            return

                        if response.status == 400:
                            text = await response.text()
                            try:
                                error_data = json.loads(text)
                                if isinstance(error_data, dict) and str(
                                    error_data.get("error", "")
                                ) == "ERROR_004":
                                    if not self._ever_authenticated:
                                        self._reset_for_credential_failure()
                                    else:
                                        self._authenticated = False
                                        self._clear_session_cookies()
                                    raise MooxAuthenticationException(
                                        error_data.get(
                                            "message", "Invalid email or password"
                                        )
                                    )
                            except (json.JSONDecodeError, ValueError):
                                pass
                            last_error = MooxException(
                                f"Authentication failed: {text}"
                            )
                            if auth_attempt < AUTH_INTERNAL_RETRIES - 1:
                                await asyncio.sleep(min(2**auth_attempt, 5))
                                continue
                            self._authenticated = False
                            self._session_expiration_in_progress = False
                            self._clear_session_cookies()
                            raise last_error

                        if response.status >= 500:
                            last_error = MooxConnectionException(
                                f"Server error: {response.status}"
                            )
                            if auth_attempt < AUTH_INTERNAL_RETRIES - 1:
                                await asyncio.sleep(min(2**auth_attempt, 5))
                                continue
                            raise last_error

                        text = await response.text()
                        last_error = MooxException(
                            f"Authentication failed: {response.status}: {text}"
                        )
                        if auth_attempt < AUTH_INTERNAL_RETRIES - 1:
                            await asyncio.sleep(min(2**auth_attempt, 5))
                            continue
                        raise last_error

                except MooxAuthenticationException:
                    raise
                except asyncio.TimeoutError as err:
                    last_error = MooxConnectionException(f"Timeout: {err}")
                    if auth_attempt < AUTH_INTERNAL_RETRIES - 1:
                        await asyncio.sleep(min(2**auth_attempt, 5))
                        continue
                    raise MooxConnectionException(
                        f"Authentication timeout after {AUTH_INTERNAL_RETRIES} attempts"
                    ) from err
                except (
                    aiohttp.ClientConnectorError,
                    aiohttp.ServerConnectionError,
                ) as err:
                    last_error = MooxConnectionException(f"Connection error: {err}")
                    if auth_attempt < AUTH_INTERNAL_RETRIES - 1:
                        await asyncio.sleep(min(2**auth_attempt, 5))
                        continue
                    raise MooxConnectionException(
                        f"Connection error after {AUTH_INTERNAL_RETRIES} attempts"
                    ) from err
                except aiohttp.ClientError as err:
                    raise MooxException(f"Client error: {err}") from err

            if last_error:
                raise last_error
            raise MooxException("Authentication failed")

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        retries: int = 3,
    ) -> Any:
        """Make an authenticated request to the MOOX API."""
        url = f"{self._base_url}/{endpoint}"
        last_exception: Exception | None = None

        request_had_valid_session = self._authenticated or self._ever_authenticated

        is_reauth_attempt = False
        needs_reauth = False
        for attempt in range(retries):
            try:
                await self._authenticate(
                    skip_rate_limit=is_reauth_attempt or needs_reauth,
                    is_reauth=is_reauth_attempt or needs_reauth,
                )
                is_reauth_attempt = False
                needs_reauth = False

                async with self._session.request(
                    method,
                    url,
                    params=params,
                    ssl=self._verify_ssl if self._ssl else False,
                    timeout=self._timeout,
                ) as response:
                    if 200 <= response.status < 300:
                        self._session_expiration_in_progress = False
                        try:
                            return await response.json()
                        except (ValueError, aiohttp.ContentTypeError) as err:
                            raise MooxException(f"Invalid JSON response: {err}") from err

                    text = await response.text()

                    if response.status == 400:
                        try:
                            error_data = json.loads(text)
                            if isinstance(error_data, dict) and str(
                                error_data.get("error", "")
                            ) == "ERROR_004":
                                session_was_valid = (
                                    request_had_valid_session
                                    or self._authenticated
                                    or self._ever_authenticated
                                    or self._session_expiration_in_progress
                                )

                                if session_was_valid:
                                    self._clear_auth_state_for_reauth()
                                    needs_reauth = True
                                    if attempt < retries - 1:
                                        is_reauth_attempt = True
                                        await asyncio.sleep(min(2**attempt, 10))
                                        continue
                                    raise MooxSessionExpiredException(
                                        "Session expired after max retries"
                                    )

                                self._reset_for_credential_failure()
                                raise MooxAuthenticationException(
                                    error_data.get("message", "Invalid credentials")
                                )
                        except (json.JSONDecodeError, ValueError):
                            pass
                        raise MooxException(f"API error 400: {text}")

                    if response.status >= 500:
                        if attempt < retries - 1:
                            last_exception = MooxConnectionException(
                                f"Server error {response.status}"
                            )
                            await asyncio.sleep(min(2**attempt, 10))
                            continue
                        raise MooxConnectionException(
                            f"Server error after {retries} attempts"
                        )

                    raise MooxException(f"API error {response.status}: {text}")

            except MooxSessionExpiredException:
                self._authenticated = False
                needs_reauth = True
                if attempt < retries - 1:
                    is_reauth_attempt = True
                    last_exception = MooxSessionExpiredException("Session expired")
                    await asyncio.sleep(min(2**attempt, 10))
                    continue
                raise
            except MooxAuthenticationException:
                raise
            except asyncio.TimeoutError as err:
                if attempt < retries - 1:
                    last_exception = MooxConnectionException(f"Timeout: {err}")
                    await asyncio.sleep(min(2**attempt, 10))
                    continue
                raise MooxConnectionException(
                    f"Timeout after {retries} attempts"
                ) from err
            except aiohttp.ClientConnectorError as err:
                if attempt < retries - 1:
                    last_exception = MooxConnectionException(f"Connection error: {err}")
                    await asyncio.sleep(min(2**attempt, 10))
                    continue
                raise MooxConnectionException(
                    f"Connection error after {retries} attempts"
                ) from err
            except MooxConnectionException:
                if attempt < retries - 1:
                    await asyncio.sleep(min(2**attempt, 10))
                    continue
                raise
            except aiohttp.ClientError as err:
                if isinstance(err, aiohttp.ServerConnectionError):
                    if attempt < retries - 1:
                        last_exception = MooxConnectionException(
                            f"Server connection error: {err}"
                        )
                        await asyncio.sleep(min(2**attempt, 10))
                        continue
                    raise MooxConnectionException(
                        f"Server connection error after {retries} attempts"
                    ) from err
                raise MooxException(f"Client error: {err}") from err

        if last_exception:
            raise last_exception
        raise MooxException("Request failed")

    async def get_devices(self) -> list[DeviceModel]:
        """Get all devices from the MOOX server."""
        return await self._request("GET", "devices")

    async def get_positions(self) -> list[PositionModel]:
        """Get all positions from the MOOX server."""
        return await self._request("GET", "positions")

    async def get_geofences(self) -> list[GeofenceModel]:
        """Get all geofences from the MOOX server."""
        return await self._request("GET", "geofences")

    async def get_server(self) -> ServerModel:
        """Get server information."""
        return await self._request("GET", "server")

    async def get_reports_events(
        self,
        devices: list[int],
        start_time: datetime | None,
        end_time: datetime,
        event_types: list[str],
    ) -> list[EventModel]:
        """Get events from the MOOX server."""
        if not devices:
            return []

        params: dict[str, Any] = {
            "deviceId": devices,
            "to": end_time.isoformat() + "Z",
        }

        if event_types:
            valid_event_types = [str(et) for et in event_types if et is not None]
            if valid_event_types:
                params["type"] = ",".join(valid_event_types)

        if start_time:
            params["from"] = start_time.isoformat() + "Z"

        try:
            return await self._request("GET", "reports/events", params=params)
        except MooxException:
            return []

    async def close_websocket(self) -> None:
        """Close the WebSocket connection if open."""
        if self._ws_session and not self._ws_session.closed:
            await self._ws_session.close()
        self._ws_session = None

        current_task = asyncio.current_task()
        if (
            self._ws_task
            and not self._ws_task.done()
            and self._ws_task is not current_task
        ):
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        self._ws_task = None
