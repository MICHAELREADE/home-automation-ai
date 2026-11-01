"""Verify read-only Home Assistant API connectivity."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ha.ha_client import (
    HomeAssistantAPIError,
    HomeAssistantClient,
    HomeAssistantConfigurationError,
)


def main() -> int:
    """Print API status and state count without changing any Home Assistant entity."""

    try:
        client = HomeAssistantClient.from_environment()
        status = client.ping()
        states = client.list_states()
    except (HomeAssistantConfigurationError, HomeAssistantAPIError) as exc:
        print(f"Home Assistant connectivity check failed: {exc}", file=sys.stderr)
        return 1

    print(f"Home Assistant API: {status.get('message', 'connected')}")
    print(f"Entity states returned: {len(states)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
