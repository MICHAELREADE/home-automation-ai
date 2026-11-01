"""Read-only client for the Home Assistant REST API."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

import requests


class HomeAssistantConfigurationError(ValueError):
    """Raised when required Home Assistant configuration is missing."""


class HomeAssistantAPIError(RuntimeError):
    """Raised when a Home Assistant API request cannot be completed."""


@dataclass(frozen=True)
class HomeAssistantSettings:
    """Connection details required by the Home Assistant REST API client."""

    base_url: str
    token: str
    timeout_seconds: float = 10.0


class HomeAssistantClient:
    """Provide read-only access to Home Assistant API status and entity states."""

    def __init__(
        self,
        settings: HomeAssistantSettings,
        *,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize a client using explicit connection settings."""

        self._settings = settings
        self._session = session or requests.Session()
        if session is None:
            # Home Assistant is expected to be on the local network. Do not send
            # its token or traffic through proxy settings inherited by the process.
            self._session.trust_env = False

    @classmethod
    def from_environment(cls, env_file: Path | None = None) -> "HomeAssistantClient":
        """Create a client from environment variables and an optional local `.env` file."""

        return cls(load_home_assistant_settings(env_file))

    def ping(self) -> dict[str, Any]:
        """Return the API status payload without changing Home Assistant state."""

        payload = self._get("/api/")
        if not isinstance(payload, dict):
            raise HomeAssistantAPIError("Home Assistant API status response was not an object.")
        return payload

    def list_states(self) -> list[dict[str, Any]]:
        """Return the current state records known to Home Assistant."""

        payload = self._get("/api/states")
        if not isinstance(payload, list):
            raise HomeAssistantAPIError("Home Assistant states response was not an array.")
        return payload

    def _get(self, path: str) -> Any:
        """Issue an authenticated GET request and decode its JSON response."""

        url = f"{self._settings.base_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {self._settings.token}"}
        try:
            response = self._session.get(
                url,
                headers=headers,
                timeout=self._settings.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise HomeAssistantAPIError(f"Home Assistant request failed: {exc}") from exc
        except ValueError as exc:
            raise HomeAssistantAPIError("Home Assistant returned invalid JSON.") from exc


def load_home_assistant_settings(
    env_file: Path | None = None,
) -> HomeAssistantSettings:
    """Load validated Home Assistant settings without overwriting shell variables."""

    _load_env_file(env_file or Path.cwd() / ".env")
    base_url = os.getenv("HA_BASE_URL")
    token = os.getenv("HA_LONG_LIVED_TOKEN")
    timeout_value = os.getenv("HA_API_TIMEOUT_SECONDS", "10")

    if not base_url:
        raise HomeAssistantConfigurationError("HA_BASE_URL is required.")
    if not token:
        raise HomeAssistantConfigurationError("HA_LONG_LIVED_TOKEN is required.")
    try:
        timeout_seconds = float(timeout_value)
    except ValueError as exc:
        raise HomeAssistantConfigurationError(
            "HA_API_TIMEOUT_SECONDS must be a number."
        ) from exc
    if timeout_seconds <= 0:
        raise HomeAssistantConfigurationError(
            "HA_API_TIMEOUT_SECONDS must be greater than zero."
        )

    return HomeAssistantSettings(
        base_url=base_url.rstrip("/"),
        token=token,
        timeout_seconds=timeout_seconds,
    )


def _load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE entries from a local `.env` file if it exists."""

    if not path.is_file():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", maxsplit=1)
        os.environ.setdefault(key.strip(), value.strip())
