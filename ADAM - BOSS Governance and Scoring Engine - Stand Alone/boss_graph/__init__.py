"""BOSS Data Graph — schema, seed, and loader modules.

The package ships two Cypher files next to this module:

* ``schema.cypher`` — uniqueness constraints and indexes
  (``CREATE CONSTRAINT ... IF NOT EXISTS``).
* ``seed.cypher`` — idempotent ``MERGE`` statements that seed the
  framework catalog, priority tiers, escalation tiers, dimensions,
  regulations, and the 5-Director Constitution.

The companion ``loader`` module applies both files over any object
that satisfies :class:`boss_core.graph_client.GraphClient`, including
the in-memory fallback for offline tests.

A read-only ``graphql_view.graphql`` is also shipped as reference for
downstream GraphQL gateways (Strawberry, neo4j-graphql-js, Hasura).
"""

from boss_graph.loader import (
    apply_file,
    apply_schema,
    seed_graph,
)

__all__ = ["apply_file", "apply_schema", "seed_graph"]
