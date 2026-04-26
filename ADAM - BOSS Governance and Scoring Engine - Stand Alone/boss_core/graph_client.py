"""Neo4j client abstraction for the BOSS Data Graph.

Production uses the official `neo4j` driver. For unit tests and offline
environments, `InMemoryGraph` provides a minimal key-value substitute
that satisfies the same interface so the service starts without Neo4j.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol


class GraphClient(Protocol):
    """Minimal graph client contract used by the engine."""

    def run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]: ...
    def close(self) -> None: ...
    def healthcheck(self) -> bool: ...


@dataclass
class InMemoryGraph:
    """In-memory fallback. Accepts Cypher but only records the calls."""

    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        self.calls.append((cypher, params or {}))
        if cypher.strip().upper().startswith("RETURN 1"):
            return [{"ok": 1}]
        return []

    def close(self) -> None:
        return None

    def healthcheck(self) -> bool:
        return True


class Neo4jGraph:
    """Thin wrapper around neo4j.GraphDatabase.driver."""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j") -> None:
        from neo4j import GraphDatabase

        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self._driver.session(database=self._database) as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]

    def close(self) -> None:
        self._driver.close()

    def healthcheck(self) -> bool:
        try:
            rows = self.run("RETURN 1 AS ok")
            return bool(rows and rows[0].get("ok") == 1)
        except Exception:  # pragma: no cover - depends on live Neo4j
            return False


def batch_run(client: GraphClient, statements: Iterable[str]) -> None:
    """Execute a sequence of Cypher statements in order."""
    for stmt in statements:
        stmt = stmt.strip()
        if stmt:
            client.run(stmt)
