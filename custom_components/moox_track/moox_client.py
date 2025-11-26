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

MAX_LOGIN_RETRIES = 10
LOGIN_RETRY_DELAY = 30.0
LOGIN_BACKOFF_MULTIPLIER = 1.5


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
        self._consecutive_login_failures = 0
        self._last_login_attempt: datetime | None = None

    @property
    def base_url(self) -> str:
        """Return the base URL for the MOOX API."""
        return self._base_url

    @property
    def login_failures_exceeded(self) -> bool:
        """Return True if max login retry attempts have been exceeded."""
        return self._consecutive_login_failures >= MAX_LOGIN_RETRIES

    def reset_login_failures(self) -> None:
        """Reset the login failure counter."""
        self._consecutive_login_failures = 0
        self._last_login_attempt = None

    async def _wait_for_login_retry(self) -> None:
        """Wait before attempting re-login with exponential backoff."""
        if self._last_login_attempt is None:
            return

        elapsed = (datetime.now() - self._last_login_attempt).total_seconds()
        base_delay = LOGIN_RETRY_DELAY * (
            LOGIN_BACKOFF_MULTIPLIER ** min(self._consecutive_login_failures, 5)
        )
        if elapsed < base_delay:
            await asyncio.sleep(base_delay - elapsed)

    async def _authenticate(self) -> None:
        """Authenticate with the MOOX server."""
        if self._authenticated:
            return

        async with self._auth_lock:
            if self._authenticated:
                return

            if self.login_failures_exceeded:
                raise MooxAuthenticationException(
                    f"Max login attempts ({MAX_LOGIN_RETRIES}) exceeded"
                )

            await self._wait_for_login_retry()
            self._last_login_attempt = datetime.now()

            try:
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
                        self._authenticated = True
                        self._consecutive_login_failures = 0
                        return

                    if response.status == 400:
                        text = await response.text()
                        try:
                            error_data = json.loads(text)
                            if isinstance(error_data, dict) and str(
                                error_data.get("error", "")
                            ) == "ERROR_004":
                                self._consecutive_login_failures += 1
                                raise MooxAuthenticationException(
                                    error_data.get("message", "Invalid email or password")
                                )
                        except (json.JSONDecodeError, ValueError):
                            pass
                        self._consecutive_login_failures += 1
                        raise MooxAuthenticationException(
                            f"Authentication failed: {text}"
                        )

                    if response.status >= 500:
                        raise MooxConnectionException(
                            f"Server error: {response.status}"
                        )

                    text = await response.text()
                    raise MooxException(
                        f"Authentication failed: {response.status}: {text}"
                    )

            except asyncio.TimeoutError as err:
                raise MooxConnectionException(
                    f"Authentication timeout: {err}"
                ) from err
            except (
                aiohttp.ClientConnectorError,
                aiohttp.ServerConnectionError,
            ) as err:
                raise MooxConnectionException(f"Connection error: {err}") from err
            except aiohttp.ClientError as err:
                raise MooxException(f"Client error: {err}") from err

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

        for attempt in range(retries):
            try:
                await self._authenticate()
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    ssl=self._verify_ssl if self._ssl else False,
                    timeout=self._timeout,
                ) as response:
                    if 200 <= response.status < 300:
                        try:
                            return await response.json()
                        except (ValueError, aiohttp.ContentTypeError) as err:
                            raise MooxException(
                                f"Invalid JSON response: {err}"
                            ) from err

                    text = await response.text()

                    if response.status == 400:
                        try:
                            error_data = json.loads(text)
                            if isinstance(error_data, dict) and str(
                                error_data.get("error", "")
                            ) == "ERROR_004":
                                was_authenticated = self._authenticated
                                self._authenticated = False
                                if was_authenticated:
                                    raise MooxSessionExpiredException("Session expired")
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
        raise MooxException("Request failed without specific error")

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
