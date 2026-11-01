"""Preview Home Assistant entities for a typed command without executing it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.input_handler import handle_typed_input
from app.ha.entity_index import EntityIndex
from app.ha.ha_client import (
    HomeAssistantAPIError,
    HomeAssistantClient,
    HomeAssistantConfigurationError,
)
from app.llm.llm_client import create_ollama_client


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for read-only target previews."""

    parser = argparse.ArgumentParser(
        description="Preview Home Assistant entity matches without executing a command."
    )
    parser.add_argument("text", help="Typed request to extract and resolve.")
    parser.add_argument("--model", help="Override the configured local Ollama model.")
    parser.add_argument("--ollama-base-url", help="Override the local Ollama base URL.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Print a JSON intent and entity-resolution preview with no side effects."""

    args = build_parser().parse_args(argv)
    try:
        llm_client = create_ollama_client(
            model=args.model,
            base_url=args.ollama_base_url,
        )
        intent = handle_typed_input(args.text, llm_client)
        ha_client = HomeAssistantClient.from_environment()
        index = EntityIndex.from_states(ha_client.list_states())
        preview = index.preview(intent)
    except (HomeAssistantConfigurationError, HomeAssistantAPIError, RuntimeError) as exc:
        print(f"Resolution preview failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {"intent": intent.model_dump(), "resolution_preview": preview.as_dict()},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
