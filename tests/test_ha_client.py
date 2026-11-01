"""Tests for read-only Home Assistant API access."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ha.ha_client import (
    HomeAssistantAPIError,
    HomeAssistantClient,
    HomeAssistantConfigurationError,
    HomeAssistantSettings,
    load_home_assistant_settings,
)


class DummyResponse:
    """Minimal response double for Home Assistant client tests."""

    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        """Simulate a successful HTTP response."""

    def json(self) -> object:
        """Return the configured JSON payload."""

        return self._payload


class DummySession:
    """Record read-only client requests and return queued responses."""

    def __init__(self, responses: list[DummyResponse]) -> None:
        self._responses = iter(responses)
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, *, headers: dict[str, str], timeout: float) -> DummyResponse:
        """Record a GET call and return the next configured response."""

        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        return next(self._responses)


def test_client_pings_and_lists_states_without_service_calls() -> None:
    session = DummySession(
        [
            DummyResponse({"message": "API running."}),
            DummyResponse([{"entity_id": "light.living_room_lamp", "state": "off"}]),
        ]
    )
    client = HomeAssistantClient(
        HomeAssistantSettings(
            base_url="http://192.168.4.154/",
            token="test-token",
            timeout_seconds=7.0,
        ),
        session=session,  # type: ignore[arg-type]
    )

    assert client.ping() == {"message": "API running."}
    assert client.list_states() == [
        {"entity_id": "light.living_room_lamp", "state": "off"}
    ]
    assert session.calls == [
        {
            "url": "http://192.168.4.154/api/",
            "headers": {"Authorization": "Bearer test-token"},
            "timeout": 7.0,
        },
        {
            "url": "http://192.168.4.154/api/states",
            "headers": {"Authorization": "Bearer test-token"},
            "timeout": 7.0,
        },
    ]


def test_client_rejects_unexpected_states_payload() -> None:
    client = HomeAssistantClient(
        HomeAssistantSettings(base_url="http://ha.local", token="test-token"),
        session=DummySession([DummyResponse({"not": "a list"})]),  # type: ignore[arg-type]
    )

    with pytest.raises(HomeAssistantAPIError, match="not an array"):
        client.list_states()


def test_default_client_bypasses_environment_proxies() -> None:
    client = HomeAssistantClient(
        HomeAssistantSettings(base_url="http://ha.local", token="test-token")
    )

    assert client._session.trust_env is False


def test_settings_require_base_url_and_token(monkeypatch) -> None:
    monkeypatch.delenv("HA_BASE_URL", raising=False)
    monkeypatch.delenv("HA_LONG_LIVED_TOKEN", raising=False)

    with pytest.raises(HomeAssistantConfigurationError, match="HA_BASE_URL"):
        load_home_assistant_settings(Path("missing-test.env"))
