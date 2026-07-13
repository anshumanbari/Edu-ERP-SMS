"""
Start the FastAPI dev server (wraps the exact command documented in
CLAUDE.md's Commands section: `uvicorn app.main:app --reload`).

Usage:
    python -m scripts.development.start
    python -m scripts.development.start --port 8080 --no-reload
"""
import argparse
import sys

from scripts._shared.common import run_module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start the FastAPI development server.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000).")
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload (use for a production-like local run).",
    )
    args = parser.parse_args(argv)

    uvicorn_args = ["app.main:app", "--host", args.host, "--port", str(args.port)]
    if not args.no_reload:
        uvicorn_args.append("--reload")

    result = run_module("uvicorn", uvicorn_args)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
