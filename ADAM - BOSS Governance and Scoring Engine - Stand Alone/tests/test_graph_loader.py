"""Graph loader tests — statement splitting and InMemoryGraph apply."""

from __future__ import annotations

from boss_core.graph_client import InMemoryGraph
from boss_graph.loader import _split_statements, apply_schema, seed_graph


class TestSplitStatements:
    def test_single_statement(self) -> None:
        out = list(_split_statements("CREATE (:Framework {key: 'NIST'});"))
        assert out == ["CREATE (:Framework {key: 'NIST'})"]

    def test_multiple_statements(self) -> None:
        text = (
            "CREATE (:Framework {key: 'GDPR'});\n"
            "CREATE (:Framework {key: 'DORA'});\n"
            "MATCH (n) RETURN n;\n"
        )
        out = list(_split_statements(text))
        assert len(out) == 3
        assert out[0].startswith("CREATE (:Framework {key: 'GDPR'}")

    def test_ignores_blank_lines(self) -> None:
        text = "\n\nCREATE (:X);\n\n\nCREATE (:Y);\n"
        out = list(_split_statements(text))
        assert out == ["CREATE (:X)", "CREATE (:Y)"]

    def test_strips_line_comments(self) -> None:
        text = "// this is a comment\nCREATE (:NodeA);\n// another comment\nCREATE (:NodeB);\n"
        out = list(_split_statements(text))
        assert out == ["CREATE (:NodeA)", "CREATE (:NodeB)"]

    def test_multiline_statement(self) -> None:
        text = "CREATE (:Framework {\n  key: 'NIST',\n  publisher: 'NIST'\n});\n"
        out = list(_split_statements(text))
        assert len(out) == 1
        assert "publisher: 'NIST'" in out[0]

    def test_tail_without_trailing_semicolon(self) -> None:
        text = "CREATE (:X);\nMATCH (n) RETURN n"
        out = list(_split_statements(text))
        assert out == ["CREATE (:X)", "MATCH (n) RETURN n"]


class TestInMemoryApply:
    def test_apply_schema_idempotent(self) -> None:
        graph = InMemoryGraph()
        count_1 = apply_schema(graph)
        count_2 = apply_schema(graph)
        # Must apply same number of statements both times; no errors.
        assert count_1 == count_2
        assert count_1 > 0

    def test_seed_graph_idempotent(self) -> None:
        graph = InMemoryGraph()
        apply_schema(graph)
        count_1 = seed_graph(graph)
        count_2 = seed_graph(graph)
        assert count_1 == count_2
        assert count_1 > 0

    def test_graph_reports_healthy(self) -> None:
        graph = InMemoryGraph()
        apply_schema(graph)
        seed_graph(graph)
        assert graph.healthcheck() is True
