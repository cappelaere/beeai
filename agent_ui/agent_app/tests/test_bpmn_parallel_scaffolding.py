"""Token and join helpers for future parallel execution (engine-agnostic; no BPMN runtime)."""

import unittest

from agent_app.bpmn_engine import _make_engine_state, normalize_engine_state
from agent_app.bpmn_parallel import (
    active_branch_ids,
    active_element_ids,
    append_token,
    clear_pending_join,
    ensure_active_tokens,
    get_pending_join,
    is_join_satisfied,
    mark_branch_arrived_at_join,
    register_pending_join,
    remove_tokens_by_branch_ids,
    replace_token_at_index,
    replace_token_by_branch_id,
    token_dict,
    tokens_at_element,
    tokens_at_join,
)


class BpmnParallelScaffoldingTests(unittest.TestCase):
    def test_append_token_preserves_order(self):
        eng: dict = {}
        append_token(eng, "t1", "b1")
        append_token(eng, "t2", "b2")
        append_token(eng, "t3", "b3")
        self.assertEqual(active_branch_ids(eng), ["b1", "b2", "b3"])
        self.assertEqual(active_element_ids(eng), ["t1", "t2", "t3"])

    def test_append_multiple_tokens(self):
        eng = _make_engine_state(current_node_ids=["a"])
        eng["active_tokens"] = [{"current_element_id": "a", "branch_id": "b1"}]
        append_token(eng, "task_x", "b2")
        self.assertEqual(len(eng["active_tokens"]), 2)
        self.assertEqual(eng["active_tokens"][1]["branch_id"], "b2")

    def test_remove_tokens_by_branch_ids_removes_only_matching(self):
        eng = {
            "active_tokens": [
                {"current_element_id": "x", "branch_id": "b1"},
                {"current_element_id": "y", "branch_id": "b2"},
                {"current_element_id": "z", "branch_id": "b1"},
            ]
        }
        n = remove_tokens_by_branch_ids(eng, {"b1"})
        self.assertEqual(n, 2)
        self.assertEqual(len(eng["active_tokens"]), 1)
        self.assertEqual(eng["active_tokens"][0]["branch_id"], "b2")

    def test_remove_tokens_by_branch_ids_drops_non_dict_tokens(self):
        """Malformed list entries are discarded (documented); normalize_engine_state should run on load."""
        eng = {
            "active_tokens": [
                {"current_element_id": "a", "branch_id": "b1"},
                "not-a-dict",
                {"current_element_id": "c", "branch_id": "b2"},
            ]
        }
        n = remove_tokens_by_branch_ids(eng, {"b1"})
        self.assertEqual(n, 2)
        self.assertEqual(len(eng["active_tokens"]), 1)
        self.assertEqual(eng["active_tokens"][0]["branch_id"], "b2")

    def test_remove_tokens_by_branch_ids_empty_set_still_drops_non_dict(self):
        eng = {
            "active_tokens": [
                token_dict("a", "b1"),
                None,
                token_dict("c", "b2"),
            ]
        }
        n = remove_tokens_by_branch_ids(eng, set())
        self.assertEqual(n, 1)
        self.assertEqual(len(eng["active_tokens"]), 2)

    def test_tokens_at_join_returns_all_matching_tokens(self):
        eng = normalize_engine_state(
            {
                "active_tokens": [
                    {"current_element_id": "join1", "branch_id": "b1"},
                    {"current_element_id": "join1", "branch_id": "b2"},
                    {"current_element_id": "task_y", "branch_id": "b3"},
                ]
            }
        )
        at_join = tokens_at_join(eng, "join1")
        self.assertEqual(len(at_join), 2)
        branches = {t["branch_id"] for t in at_join}
        self.assertEqual(branches, {"b1", "b2"})
        self.assertEqual(len(tokens_at_element(eng, "join1")), 2)

    def test_register_pending_join_sets_expected_shape(self):
        eng = _make_engine_state()
        register_pending_join(eng, "join_gw", "fork_1", ["b1", "b2"])
        pj = get_pending_join(eng, "join_gw")
        self.assertIsNotNone(pj)
        assert pj is not None
        self.assertEqual(pj["fork_id"], "fork_1")
        self.assertEqual(pj["join_element_id"], "join_gw")
        self.assertEqual(pj["expected_branch_ids"], ["b1", "b2"])
        self.assertEqual(pj["arrived_branch_ids"], [])

    def test_mark_branch_arrived_is_idempotent(self):
        eng = _make_engine_state()
        register_pending_join(eng, "j1", "f", ["b1"])
        self.assertTrue(mark_branch_arrived_at_join(eng, "j1", "b1"))
        self.assertTrue(mark_branch_arrived_at_join(eng, "j1", "b1"))
        pj = get_pending_join(eng, "j1")
        assert pj is not None
        self.assertEqual(pj["arrived_branch_ids"], ["b1"])

    def test_join_satisfied_when_all_expected_branches_arrive(self):
        eng = _make_engine_state()
        register_pending_join(eng, "join_gw", "fork_1", ["b1", "b2"])
        self.assertFalse(is_join_satisfied(eng, "join_gw"))
        mark_branch_arrived_at_join(eng, "join_gw", "b1")
        self.assertFalse(is_join_satisfied(eng, "join_gw"))
        mark_branch_arrived_at_join(eng, "join_gw", "b2")
        self.assertTrue(is_join_satisfied(eng, "join_gw"))
        self.assertTrue(mark_branch_arrived_at_join(eng, "join_gw", "b2"))

    def test_clear_pending_join_removes_entry(self):
        eng = _make_engine_state()
        register_pending_join(eng, "j1", "f", ["a"])
        self.assertTrue(clear_pending_join(eng, "j1"))
        self.assertIsNone(get_pending_join(eng, "j1"))
        self.assertFalse(is_join_satisfied(eng, "j1"))
        self.assertFalse(clear_pending_join(eng, "j1"))

    def test_replace_token_at_index(self):
        eng = {"active_tokens": [token_dict("a", "b1"), token_dict("b", "b2")]}
        replace_token_at_index(eng, 0, "a2", "b1")
        self.assertEqual(eng["active_tokens"][0]["current_element_id"], "a2")
        replace_token_at_index(eng, 99, "x", "y")
        self.assertEqual(len(eng["active_tokens"]), 2)

    def test_replace_token_by_branch_id(self):
        eng = {"active_tokens": [token_dict("t1", "b1"), token_dict("t2", "b2")]}
        self.assertTrue(replace_token_by_branch_id(eng, "b2", "t2_new"))
        self.assertEqual(eng["active_tokens"][1]["current_element_id"], "t2_new")
        self.assertEqual(eng["active_tokens"][1]["branch_id"], "b2")
        self.assertTrue(replace_token_by_branch_id(eng, "b2", "end", "b2_renamed"))
        self.assertEqual(eng["active_tokens"][1]["branch_id"], "b2_renamed")
        self.assertFalse(replace_token_by_branch_id(eng, "missing", "x"))

    def test_malformed_engine_state_safe(self):
        eng: dict = {}
        append_token(eng, "e", "b")
        self.assertEqual(len(ensure_active_tokens(eng)), 1)
        eng2: dict = {"active_tokens": "not-a-list"}
        remove_tokens_by_branch_ids(eng2, {"b"})
        self.assertEqual(eng2["active_tokens"], [])
        eng3: dict = {}
        register_pending_join(eng3, "j", "f", ["1"])
        self.assertIsNotNone(get_pending_join(eng3, "j"))

    def test_token_dict_empty_strings_to_none(self):
        self.assertIsNone(token_dict("", "")["current_element_id"])
        self.assertIsNone(token_dict("", "")["branch_id"])

    def test_join_bookkeeping_all_arrived(self):
        eng = _make_engine_state()
        register_pending_join(eng, "join_gw", "fork_1", ["b1", "b2"])
        self.assertFalse(mark_branch_arrived_at_join(eng, "join_gw", "b1"))
        self.assertTrue(mark_branch_arrived_at_join(eng, "join_gw", "b2"))


if __name__ == "__main__":
    unittest.main()
