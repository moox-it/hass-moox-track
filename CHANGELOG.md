# Changelog

All notable changes to MOOX Track for Home Assistant will be documented in this file.

## [2.0.2] - 2025-11-28

### Improved
- **Automatic reconnection**: When the server is unavailable or there are connection issues, the integration continuously retries in the background for up to 12 hours. No action is needed—it will reconnect automatically when connectivity is restored.
- **Session management**: Automatic session recovery when the session expires, with smart retry logic.
- **Connection resilience**: Exponential backoff for retries to avoid overloading the server during connectivity issues.
- **Cached data usage**: The integration continues to display the last known device positions while reconnecting.

### Fixed
- Improved handling of concurrent API requests during session expiration.
- Grace period state now persists across Home Assistant restarts.

## [2.0.1] - 2025-11-26

### Fixed
- Minor bug fixes and stability improvements.

## [2.0] - 2025-11-13

### Added
- Initial release with full GPS tracking support.
- Real-time device tracking with 40+ sensors.
- Dual geofencing (MOOX app + Home Assistant zones).
- Event and alarm detection.
- OBD-II data support for compatible devices.

---

For more information, visit [moox.it](https://moox.it) or open an issue on [GitHub](https://github.com/moox-it/hass-moox-track/issues).
