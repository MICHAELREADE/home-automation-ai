"""CLI entrypoint for Phase A.1 intent extraction."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from app.core.input_handler import handle_typed_input
from app.llm.llm_client import LLMClient, create_ollama_client


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for typed intent extraction."""

    parser = argparse.ArgumentParser(
        description="Extract structured intent JSON from typed smart home input."
    )
    parser.add_argument("text", help="Typed request to send to the intent extractor.")
    parser.add_argument(
        "--backend",
        choices=("ollama",),
        default="ollama",
        help="Local LLM backend to use. Defaults to ollama.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the default model name for the selected backend.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override the backend base URL for the selected backend.",
    )
    return parser


def create_client(args: argparse.Namespace) -> LLMClient:
    """Create the configured client for the selected backend."""

    if args.backend == "ollama":
        return create_ollama_client(
            model=args.model if args.model else None,
            base_url=args.base_url if args.base_url else None,
        )
    raise ValueError(f"Unsupported backend: {args.backend}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Phase A.1 CLI and print extracted intent as JSON."""

    parser = build_parser()
    args = parser.parse_args(argv)
    client = create_client(args)
    result = handle_typed_input(args.text, client)
    print(json.dumps(result.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
