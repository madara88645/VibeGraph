import os
import sys
import unittest

import networkx as nx

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyst.exporter import GraphExporter


def _edge_cycle_flags(json_output):
    return {(e["source"], e["target"]): e["data"]["is_cycle_edge"] for e in json_output["edges"]}


class TestGraphExportCycleDetection(unittest.TestCase):
    """Regression tests for the is_cycle_edge flag emitted by GraphExporter."""

    def test_simple_two_node_cycle_flags_both_edges(self):
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        graph.add_edge("B", "A")

        out = GraphExporter().export_to_react_flow(graph)
        flags = _edge_cycle_flags(out)

        self.assertTrue(flags[("A", "B")])
        self.assertTrue(flags[("B", "A")])

    def test_three_node_cycle_flags_all_edges(self):
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")
        graph.add_edge("C", "A")

        out = GraphExporter().export_to_react_flow(graph)
        flags = _edge_cycle_flags(out)

        self.assertTrue(all(flags.values()))
        self.assertEqual(len(flags), 3)

    def test_acyclic_chain_has_no_cycle_edges(self):
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")
        graph.add_edge("C", "D")

        out = GraphExporter().export_to_react_flow(graph)
        flags = _edge_cycle_flags(out)

        self.assertFalse(any(flags.values()))

    def test_self_loop_is_not_flagged_as_cycle_edge(self):
        # A self-loop node forms a strongly connected component of size 1,
        # so it must never be reported as a cycle edge (u == v is excluded).
        graph = nx.DiGraph()
        graph.add_edge("A", "A")
        graph.add_edge("A", "B")

        out = GraphExporter().export_to_react_flow(graph)
        flags = _edge_cycle_flags(out)

        self.assertFalse(flags[("A", "A")])
        self.assertFalse(flags[("A", "B")])

    def test_disjoint_cycle_and_chain_only_cycle_edges_flagged(self):
        graph = nx.DiGraph()
        # Cycle: X <-> Y
        graph.add_edge("X", "Y")
        graph.add_edge("Y", "X")
        # Separate acyclic chain: P -> Q
        graph.add_edge("P", "Q")

        out = GraphExporter().export_to_react_flow(graph)
        flags = _edge_cycle_flags(out)

        self.assertTrue(flags[("X", "Y")])
        self.assertTrue(flags[("Y", "X")])
        self.assertFalse(flags[("P", "Q")])

    def test_cycle_broken_by_node_budget_truncation_is_not_flagged(self):
        # Build a hub with 15 bidirectional leaves (each degree 2, same as
        # the cycle pair below) plus a separate two-node cycle "cyc_a" <->
        # "cyc_b" (also degree 2 each). Truncation ranks by degree desc,
        # tie-broken by ascending node-id string -- digit-named leaf ids
        # sort before the letter-named cycle ids, so with more numeric
        # leaves than budget slots remain, the cycle pair is reliably elided.
        graph = nx.DiGraph()
        for i in range(1, 16):
            leaf = str(i)
            graph.add_edge("0", leaf)
            graph.add_edge(leaf, "0")

        graph.add_edge("cyc_a", "cyc_b")
        graph.add_edge("cyc_b", "cyc_a")

        out = GraphExporter().export_to_react_flow(graph, max_nodes=10)

        kept_ids = {n["id"] for n in out["nodes"]}
        self.assertNotIn("cyc_a", kept_ids)
        self.assertNotIn("cyc_b", kept_ids)

        # No edge referencing the elided cycle nodes should be emitted at all,
        # confirming cycle detection ran on the *filtered* subgraph rather
        # than leaking membership from the full (pre-truncation) graph.
        flags = _edge_cycle_flags(out)
        self.assertNotIn(("cyc_a", "cyc_b"), flags)
        self.assertNotIn(("cyc_b", "cyc_a"), flags)
        # Every surviving hub<->leaf pair is itself a bidirectional (thus
        # cyclic) edge, so all retained edges are correctly still flagged.
        self.assertTrue(all(flags.values()))

    def test_cycle_surviving_node_budget_truncation_is_flagged(self):
        # Two high-degree hub nodes ("A", "B") form a cycle between each
        # other while both also connecting to many low-degree leaves, so
        # both hubs survive truncation and the cycle edge must still be
        # flagged post-filtering.
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        graph.add_edge("B", "A")
        for i in range(20):
            leaf = f"leaf{i}"
            graph.add_node(leaf, type="function")
            graph.add_edge("A", leaf)

        out = GraphExporter().export_to_react_flow(graph, max_nodes=2)

        kept_ids = {n["id"] for n in out["nodes"]}
        self.assertEqual(kept_ids, {"A", "B"})

        flags = _edge_cycle_flags(out)
        self.assertTrue(flags[("A", "B")])
        self.assertTrue(flags[("B", "A")])


if __name__ == "__main__":
    unittest.main()
