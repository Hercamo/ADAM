"""Idempotent loader for the BOSS Data Graph.

Reads `schema.cypher` and `seed.cypher` from this package and executes
each statement via a :class:`boss_core.graph_client.GraphClient`.

Usage
-----

As a library::

    from boss_core.graph_client import Neo4jGraph
    from boss_graph.loader import apply_schema, seed_graph

    client = Neo4jGraph("bolt://neo4j:7687", "neo4j", "neo4j")
    apply_schema(client)
    seed_graph(client)

As a CLI (after ``pip install -e .``)::

    python -m boss_graph.loader --uri bolt://localhost:7687 \
        --user neo4j --password neo4j --database neo4j

All operations are idempotent: re-running the loader is safe.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Iterator
from importlib.resources import files
from pathlib import Path

from boss_core.graph_client import GraphClient, InMemoryGraph, Neo4jGraph

_LOGGER = logging.getLogger("boss_graph.loader")


def _split_statements(cypher_text: str) -> Iterator[str]:
    """Split a Cypher script on top-level semicolons.

    Line comments starting with ``//`` are preserved inside the emitted
    statement (Cypher parses them natively), but empty statements are
    filtered out.
    """
    buffer: list[str] = []
    for raw_line in cypher_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if buffer:
                buffer.append("")
            continue
        if stripped.startswith("//"):
            # Keep comments attached to the next statement for context.
            continue
        buffer.append(raw_line)
        if stripped.endswith(";"):
            joined = "\n".join(buffer).strip()
            if joined.endswith(";"):
                joined = joined[:-1].rstrip()
            if joined:
                yield joined
            buffer.clear()
    tail = "\n".join(buffer).strip()
    if tail:
        yield tail


def _read_resource(name: str) -> str:
    """Read a .cypher file shipped inside the boss_graph package."""
    resource = files("boss_graph").joinpath(name)
    return resource.read_text(encoding="utf-8")


def apply_schema(client: GraphClient) -> int:
    """Apply schema.cypher idempotently. Returns statements executed."""
    return _apply(client, _read_resource("schema.cypher"), label="schema")


def seed_graph(client: GraphClient) -> int:
    """Apply seed.cypher idempotently. Returns statements executed."""
    return _apply(client, _read_resource("seed.cypher"), label="seed")


def apply_file(client: GraphClient, path: str | Path) -> int:
    """Apply any Cypher file from disk (useful for custom overlays)."""
    text = Path(path).read_text(encoding="utf-8")
    return _apply(client, text, label=str(path))


def _apply(client: GraphClient, cypher_text: str, *, label: str) -> int:
    count = 0
    for statement in _split_statements(cypher_text):
        _LOGGER.debug("executing %s statement: %s", label, statement[:80])
        client.run(statement)
        count += 1
    _LOGGER.info("boss_graph.%s applied: %d statements", label, count)
    return count


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="boss_graph.loader",
        description="Idempotent loader for the BOSS Data Graph.",
    )
    parser.add_argument(
        "--uri",
        default="bolt://localhost:7687",
        help="Neo4j bolt URI (default: bolt://localhost:7687)",
    )
    parser.add_argument("--user", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", default="neo4j", help="Neo4j password")
    parser.add_argument("--database", default="neo4j", help="Target database name")
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Apply only schema constraints and indexes.",
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Apply only the seed data (schema must already exist).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use the in-memory fallback graph (no Neo4j required).",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    client: GraphClient
    if args.dry_run:
        client = InMemoryGraph()
    else:
        client = Neo4jGraph(args.uri, args.user, args.password, database=args.database)

    try:
        if not args.seed_only:
            apply_schema(client)
        if not args.schema_only:
            seed_graph(client)
    finally:
        client.close()
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
