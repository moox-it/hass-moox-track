"""MOOX API Client for MOOX Track.

This client communicates directly with the MOOX Track server API,
ensuring full compatibility with MOOX Track platform and Home Assistant.

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
from datetime import datetime
from typing import Any, Callable
from collections.abc import Awaitable

import aiohttp
from aiohttp import ClientSession, ClientTimeout


class MooxAuthenticationException(Exception):
    """Exception raised for authentication errors."""


class MooxException(Exception):
    """Exception raised for MOOX API errors."""


DeviceModel = dict[str, Any]
PositionModel = dict[str, Any]
GeofenceModel = dict[str, Any]
EventModel = dict[str, Any]
ServerModel = dict[str, Any]
SubscriptionData = dict[str, Any]


class MooxClient:
    """MOOX API client for communication with MOOX Track server.
    
    This client implements best practices for resilient HTTP communication:
    - Explicit timeouts for all requests to prevent hanging
    - Retry logic with exponential backoff for transient errors
    - Proper error handling distinguishing temporary vs permanent failures
    - WebSocket connection management with timeout and cleanup
    """

    CONNECT_TIMEOUT = 10.0
    TOTAL_TIMEOUT = 30.0
    WS_CONNECT_TIMEOUT = 10.0
    WS_RECEIVE_TIMEOUT = 60.0

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
        """Initialize the MOOX API client.
        
        Args:
            client_session: aiohttp client session
            host: MOOX server hostname
            port: MOOX server port
            username: Username for authentication
            password: Password for authentication
            ssl: Use SSL/TLS
            verify_ssl: Verify SSL certificates
        """
        self._session = client_session
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._ssl = ssl
        self._verify_ssl = verify_ssl
        self._base_url = f"{'https' if ssl else 'http'}://{host}:{port}/api"
        self._authenticated = False
        self._ws_session: aiohttp.ClientWebSocketResponse | None = None
        self._ws_handler: Callable[[SubscriptionData], Awaitable[None]] | None = None
        self._ws_task: asyncio.Task | None = None
        self._timeout = ClientTimeout(
            connect=self.CONNECT_TIMEOUT,
            total=self.TOTAL_TIMEOUT,
        )

    @property
    def base_url(self) -> str:
        """Return the base URL for the MOOX API."""
        return self._base_url

    async def _authenticate(self) -> None:
        """Authenticate with the MOOX server using username/password."""
        if self._authenticated:
            return

        try:
            auth_payloads = (
                {"email": self._username, "password": self._password},
                {"username": self._username, "password": self._password},
            )
            last_error: str | None = None
            last_timeout: tuple[MooxException, asyncio.TimeoutError] | None = None
            for payload in auth_payloads:
                try:
                    async with self._session.post(
                        f"{self._base_url}/session",
                        json=payload,
                        ssl=self._verify_ssl if self._ssl else False,
                        timeout=self._timeout,
                    ) as response:
                        if response.status in (200, 204):
                            self._authenticated = True
                            return
                        if response.status in (400, 401):
                            last_error = await response.text()
                            continue
                        text = await response.text()
                        raise MooxException(
                            f"Authentication failed with status {response.status}: {text}"
                        )
                except asyncio.TimeoutError as err:
                    last_timeout = (
                        MooxException(f"Authentication timeout: {err}"),
                        err,
                    )
                    continue
            if last_timeout and last_error is None:
                raise last_timeout[0] from last_timeout[1]
            raise MooxAuthenticationException(
                "Invalid username or password"
                if last_error is None
                else f"Invalid username or password: {last_error}"
            )
        except aiohttp.ClientError as err:
            raise MooxException(f"Connection error during authentication: {err}") from err

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        retries: int = 2,
    ) -> Any:
        """Make an authenticated request to the MOOX API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without /api prefix)
            params: URL parameters
            retries: Number of retry attempts for transient errors
            
        Returns:
            JSON response from the API
            
        Raises:
            MooxAuthenticationException: If authentication fails
            MooxException: If the API request fails
        """
        url = f"{self._base_url}/{endpoint}"
        last_exception: Exception | None = None
        
        for attempt in range(retries):
            await self._authenticate()
            try:
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    ssl=self._verify_ssl if self._ssl else False,
                    timeout=self._timeout,
                ) as response:
                    if response.status == 401:
                        self._authenticated = False
                        if attempt == 0:
                            continue
                        raise MooxAuthenticationException("Authentication required")
                    if response.status < 200 or response.status >= 300:
                        text = await response.text()
                        if 400 <= response.status < 500:
                            raise MooxException(
                                f"API request failed with status {response.status}: {text}"
                            )
                        if response.status >= 500 and attempt < retries - 1:
                            last_exception = MooxException(
                                f"Server error {response.status}: {text}"
                            )
                            await asyncio.sleep(min(2 ** attempt, 10))
                            continue
                        raise MooxException(
                            f"API request failed with status {response.status}: {text}"
                        )
                    return await response.json()
            except asyncio.TimeoutError as err:
                if attempt < retries - 1:
                    last_exception = MooxException(f"Request timeout: {err}")
                    await asyncio.sleep(min(2 ** attempt, 10))
                    continue
                raise MooxException(f"Request timeout after {retries} attempts: {err}") from err
            except aiohttp.ClientConnectorError as err:
                if attempt < retries - 1:
                    last_exception = MooxException(f"Connection error: {err}")
                    await asyncio.sleep(min(2 ** attempt, 10))
                    continue
                raise MooxException(f"Connection error after {retries} attempts: {err}") from err
            except aiohttp.ClientError as err:
                raise MooxException(f"Client error: {err}") from err
        
        if last_exception:
            raise last_exception
        raise MooxAuthenticationException("Authentication required")

    async def get_devices(self) -> list[DeviceModel]:
        """Get all devices from the MOOX server.
        
        Returns:
            List of device objects
        """
        return await self._request("GET", "devices")

    async def get_positions(self) -> list[PositionModel]:
        """Get all positions from the MOOX server.
        
        Returns:
            List of position objects
        """
        return await self._request("GET", "positions")

    async def get_geofences(self) -> list[GeofenceModel]:
        """Get all geofences from the MOOX server.
        
        Note: This endpoint (/api/geofences) is consistent across all MOOX Server versions.
        The geofence objects returned here are matched with geofenceIds found in
        position or device API responses (location varies by MOOX Server version).
        
        Returns:
            List of geofence objects
        """
        return await self._request("GET", "geofences")

    async def get_server(self) -> ServerModel:
        """Get server information.
        
        Returns:
            Server information object
        """
        return await self._request("GET", "server")

    async def get_reports_events(
        self,
        devices: list[int],
        start_time: datetime | None,
        end_time: datetime,
        event_types: list[str],
    ) -> list[EventModel]:
        """Get events from the MOOX server.
        
        Args:
            devices: List of device IDs
            start_time: Start time for event query (optional)
            end_time: End time for event query (required)
            event_types: List of event types to filter
            
        Returns:
            List of event objects
        """
        # According to OpenAPI spec:
        # - deviceId: array with explode: true (deviceId=1&deviceId=2)
        # - type: array with explode: false (type=val1,val2), optional
        # - from/to: required, ISO 8601 format
        params: dict[str, Any] = {
            "deviceId": devices,  # aiohttp will explode this automatically
            "to": end_time.isoformat() + "Z",
        }
        
        if event_types:
            params["type"] = ",".join(event_types)  # explode: false format
        
        if start_time:
            params["from"] = start_time.isoformat() + "Z"
            
        try:
            return await self._request("GET", "reports/events", params=params)
        except MooxException:
            return []

    async def subscribe(
        self, handler: Callable[[SubscriptionData], Awaitable[None]]
    ) -> None:
        """Subscribe to real-time updates via WebSocket.
        
        Args:
            handler: Async callback function to handle subscription data
            
        Note:
            WebSocket support provides real-time device updates.
            This method is available but not actively used in the current implementation.
            The integration uses polling instead for reliability.
        """
        await self._authenticate()
        self._ws_handler = handler

        ws_url = f"{'wss' if self._ssl else 'ws'}://{self._host}:{self._port}/api/socket"
        
        try:
            ws_timeout = ClientTimeout(
                connect=self.WS_CONNECT_TIMEOUT,
                total=self.WS_RECEIVE_TIMEOUT,
            )
            try:
                self._ws_session = await self._session.ws_connect(
                    ws_url,
                    ssl=self._verify_ssl if self._ssl else False,
                    timeout=ws_timeout,
                )
            except aiohttp.WSServerHandshakeError as err:
                if err.status == 401:
                    auth = aiohttp.BasicAuth(self._username, self._password)
                    self._ws_session = await self._session.ws_connect(
                        ws_url,
                        auth=auth,
                        ssl=self._verify_ssl if self._ssl else False,
                        timeout=ws_timeout,
                    )
                else:
                    raise
            
            self._ws_task = asyncio.create_task(self._ws_listen())
            await self._ws_task
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise MooxException(f"WebSocket connection failed: {err}") from err
        finally:
            self._ws_task = None

    async def _ws_listen(self) -> None:
        """Listen for WebSocket messages and dispatch to handler."""
        if not self._ws_session or not self._ws_handler:
            return

        try:
            async for msg in self._ws_session:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    await self._ws_handler(data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    raise MooxException(f"WebSocket error: {msg.data}")
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                    break
        except asyncio.CancelledError:
            raise
        except Exception as err:
            raise MooxException(f"WebSocket error: {err}") from err
        finally:
            await self.close_websocket()

    async def close_websocket(self) -> None:
        """Close the WebSocket connection."""
        if self._ws_session and not self._ws_session.closed:
            await self._ws_session.close()
        self._ws_session = None
        
        current_task = asyncio.current_task()
        if self._ws_task and not self._ws_task.done() and self._ws_task is not current_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        self._ws_task = None

