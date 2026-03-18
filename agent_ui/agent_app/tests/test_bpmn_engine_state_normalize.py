"""Unit tests for normalize_engine_state (BPMN-PAR-001)."""

from django.test import TestCase

from agent_app.bpmn_engine import BPMN_ENGINE_VERSION, _make_engine_state, normalize_engine_state


class NormalizeEngineStateTests(TestCase):
    def test_legacy_completed_and_current_only(self):
        eng = normalize_engine_state({"completed_node_ids": ["a"], "current_node_ids": ["b"]})
        self.assertEqual(eng["engine_version"], BPMN_ENGINE_VERSION)
        self.assertEqual(eng["completed_node_ids"], ["a"])
        self.assertEqual(eng["current_node_ids"], ["b"])
        self.assertEqual(eng["pending_joins"], {})
        self.assertEqual(len(eng["active_tokens"]), 1)
        self.assertEqual(eng["active_tokens"][0]["current_element_id"], "b")
        self.assertIsNone(eng["active_tokens"][0]["branch_id"])
        self.assertIsNone(eng["failed_node_id"])
        self.assertEqual(eng["condition_failure_metadata"], {})

    def test_missing_engine_version_set(self):
        eng = normalize_engine_state({"current_node_ids": ["x"]})
        self.assertEqual(eng["engine_version"], BPMN_ENGINE_VERSION)

    def test_active_tokens_missing_uses_current_node_ids(self):
        eng = normalize_engine_state({"current_node_ids": ["task1"]})
        self.assertEqual(len(eng["active_tokens"]), 1)
        self.assertEqual(eng["active_tokens"][0]["current_element_id"], "task1")

    def test_active_tokens_not_list_rebuilt_from_current(self):
        eng = normalize_engine_state({"active_tokens": "bad", "current_node_ids": ["c"]})
        self.assertEqual(eng["active_tokens"][0]["current_element_id"], "c")

    def test_active_tokens_non_dict_entries_replaced_with_defaults_then_fallback(self):
        eng = normalize_engine_state(
            {
                "active_tokens": [None, 42, "x"],
                "current_node_ids": ["fallback"],
            }
        )
        self.assertEqual(len(eng["active_tokens"]), 1)
        self.assertEqual(eng["active_tokens"][0]["current_element_id"], "fallback")

    def test_active_tokens_empty_list_uses_current_first(self):
        eng = normalize_engine_state({"active_tokens": [], "current_node_ids": ["only"]})
        self.assertEqual(len(eng["active_tokens"]), 1)
        self.assertEqual(eng["active_tokens"][0]["current_element_id"], "only")

    def test_multi_token_preserved(self):
        eng = normalize_engine_state(
            {
                "active_tokens": [
                    {"current_element_id": "j1", "branch_id": "b1"},
                    {"current_element_id": "t2", "branch_id": "b2"},
                ],
                "current_node_ids": ["j1"],
            }
        )
        self.assertEqual(len(eng["active_tokens"]), 2)
        self.assertEqual(eng["active_tokens"][0]["branch_id"], "b1")
        self.assertEqual(eng["active_tokens"][1]["current_element_id"], "t2")

    def test_tokens_strip_extra_keys(self):
        eng = normalize_engine_state(
            {"active_tokens": [{"current_element_id": "a", "branch_id": None, "fork_id": "f1"}]}
        )
        self.assertEqual(set(eng["active_tokens"][0].keys()), {"current_element_id", "branch_id"})

    def test_pending_joins_missing(self):
        eng = normalize_engine_state({"current_node_ids": ["z"]})
        self.assertEqual(eng["pending_joins"], {})

    def test_pending_joins_not_dict(self):
        eng = normalize_engine_state({"pending_joins": [], "current_node_ids": ["z"]})
        self.assertEqual(eng["pending_joins"], {})

    def test_pending_joins_partial_entry(self):
        eng = normalize_engine_state(
            {
                "pending_joins": {
                    "join_gw": {"fork_id": "fork1", "expected_branch_ids": ["b1", "b2"]}
                },
                "current_node_ids": ["z"],
            }
        )
        pj = eng["pending_joins"]["join_gw"]
        self.assertEqual(pj["fork_id"], "fork1")
        self.assertEqual(pj["join_element_id"], "join_gw")
        self.assertEqual(pj["expected_branch_ids"], ["b1", "b2"])
        self.assertEqual(pj["arrived_branch_ids"], [])

    def test_pending_joins_malformed_value_skipped(self):
        eng = normalize_engine_state(
            {
                "pending_joins": {"join_ok": {"fork_id": "f"}, "join_bad": "not-a-dict"},
                "current_node_ids": ["z"],
            }
        )
        self.assertIn("join_ok", eng["pending_joins"])
        self.assertNotIn("join_bad", eng["pending_joins"])

    def test_pending_joins_unrecoverable_dict_uses_minimal_shape(self):
        eng = normalize_engine_state(
            {
                "pending_joins": {
                    "j1": {
                        "fork_id": "f",
                        "expected_branch_ids": object(),
                    }
                },
                "current_node_ids": ["z"],
            }
        )
        self.assertIn("j1", eng["pending_joins"])
        pj = eng["pending_joins"]["j1"]
        self.assertEqual(pj["join_element_id"], "j1")
        self.assertEqual(pj["expected_branch_ids"], [])

    def test_failure_metadata_coerced(self):
        eng = normalize_engine_state(
            {
                "current_node_ids": ["z"],
                "failed_node_id": "  n1  ",
                "failure_reason": "missing_binding",
                "last_successful_node_id": "prev",
                "condition_failure_metadata": {"edge": "e1"},
            }
        )
        self.assertEqual(eng["failed_node_id"], "n1")
        self.assertEqual(eng["failure_reason"], "missing_binding")
        self.assertEqual(eng["last_successful_node_id"], "prev")
        self.assertEqual(eng["condition_failure_metadata"], {"edge": "e1"})

    def test_failure_empty_strings_to_none(self):
        eng = normalize_engine_state(
            {
                "current_node_ids": ["z"],
                "failed_node_id": "",
                "failure_reason": "   ",
                "condition_failure_metadata": "not-a-dict",
            }
        )
        self.assertIsNone(eng["failed_node_id"])
        self.assertIsNone(eng["failure_reason"])
        self.assertEqual(eng["condition_failure_metadata"], {})

    def test_none_raw_returns_fresh_state(self):
        eng = normalize_engine_state(None)
        self.assertEqual(eng, _make_engine_state())

    def test_make_engine_state_includes_all_normalized_keys(self):
        eng = _make_engine_state(current_node_ids=["a"])
        self.assertIn("pending_joins", eng)
        self.assertIn("failed_node_id", eng)
        self.assertEqual(eng["pending_joins"], {})
        self.assertIn("subprocess_stack", eng)
        self.assertIn("subprocess_transitions", eng)
        self.assertEqual(eng["subprocess_stack"], [])
        self.assertEqual(eng["subprocess_transitions"], [])

    def test_subprocess_stack_normalized(self):
        eng = normalize_engine_state(
            {
                "current_node_ids": ["x"],
                "subprocess_stack": [
                    {
                        "subprocess_id": "sp1",
                        "name": "My SP",
                        "entered_at": "2026-01-01T00:00:00Z",
                        "parent_branch_id": "b1",
                    }
                ],
                "subprocess_transitions": [
                    {"subprocess_id": "sp1", "action": "entered", "at": "t0"},
                    {"subprocess_id": "sp1", "action": "completed", "at": "t1"},
                ],
            }
        )
        self.assertEqual(len(eng["subprocess_stack"]), 1)
        self.assertEqual(eng["subprocess_stack"][0]["subprocess_id"], "sp1")
        self.assertEqual(eng["subprocess_stack"][0]["name"], "My SP")
        self.assertEqual(len(eng["subprocess_transitions"]), 2)
