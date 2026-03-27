"""
Workflow context unit tests: parse BPMN and bindings, get_first_task_id / get_next_task_id,
normalize_bindings.
"""

import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import yaml
from django.test import TestCase

from agent_app.services import workflow_service
from agent_app.workflow_context import (
    get_first_task_id,
    get_next_task_id,
    get_timer_boundary_for_task,
    join_gateway_for_parallel_fork,
    normalize_bindings,
    parse_bpmn_xml,
    parse_workflow_python,
    traverse_until_executable,
    validate_bpmn_bindings_context,
    validate_bpmn_boundary_events,
    validate_bpmn_embedded_subprocesses,
    validate_bpmn_for_save,
    validate_bpmn_intermediate_catch_events,
    validate_exclusive_gateway_semantics,
    validate_parallel_fork_join_correlation,
    validate_parallel_gateway_topology,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class ParseBpmnAndBindingsTests(TestCase):
    """Load fixture BPMN XML and bindings YAML; assert get_workflow_context-like structure and task ids."""

    def test_parse_bpmn_returns_elements_and_flows(self):
        bpmn_path = FIXTURES_DIR / "sample.bpmn"
        xml = bpmn_path.read_text()
        result = parse_bpmn_xml(xml)
        self.assertNotIn("parse_error", result)
        self.assertIn("elements", result)
        self.assertIn("task1", result["elements"])
        self.assertIn("task2", result["elements"])
        self.assertEqual(result["elements"]["task1"]["type"], "serviceTask")

    def test_parse_bindings_returns_service_tasks_dict(self):
        bindings_path = FIXTURES_DIR / "sample_bindings.yaml"
        data = yaml.safe_load(bindings_path.read_text())
        self.assertIn("serviceTasks", data)
        self.assertIn("task1", data["serviceTasks"])
        self.assertEqual(data["serviceTasks"]["task1"]["handler"], "task1")

    def test_get_first_task_id_from_parsed_fixture(self):
        xml = (FIXTURES_DIR / "sample.bpmn").read_text()
        bpmn = parse_bpmn_xml(xml)
        first = get_first_task_id(bpmn)
        self.assertEqual(first, "task1")

    def test_get_next_task_id_sequence_from_fixture(self):
        xml = (FIXTURES_DIR / "sample.bpmn").read_text()
        bpmn = parse_bpmn_xml(xml)
        self.assertEqual(get_next_task_id(bpmn, "task1"), "task2")
        self.assertIsNone(get_next_task_id(bpmn, "task2"))


class BpmnXmlGatewayFixtureTests(TestCase):
    """Tests that load real BPMN XML fixtures with exclusive gateways, default flow, and conditions."""

    def test_parse_gateway_with_default_returns_elements_and_conditions(self):
        xml = (FIXTURES_DIR / "gateway_with_default.bpmn").read_text()
        bpmn = parse_bpmn_xml(xml)
        self.assertNotIn("parse_error", bpmn)
        self.assertIn("gw1", bpmn["elements"])
        self.assertEqual(bpmn["elements"]["gw1"]["type"], "exclusiveGateway")
        self.assertEqual(bpmn["elements"]["gw1"].get("default_flow_id"), "flow_b")
        flows = bpmn.get("sequence_flows") or {}
        self.assertIn("flow_a", flows)
        self.assertIn("flow_b", flows)
        self.assertIn("state.x == 1", flows.get("flow_a", {}).get("condition", ""))
        first = get_first_task_id(bpmn)
        self.assertEqual(first, "task1")

    def test_parse_gateway_invalid_condition_fails_validation(self):
        xml = (FIXTURES_DIR / "gateway_invalid_condition.bpmn").read_text()
        bpmn = parse_bpmn_xml(xml)
        self.assertNotIn("parse_error", bpmn)
        errors = validate_exclusive_gateway_semantics(bpmn)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("unparsable" in e or "single identifier" in e for e in errors))

    def test_parse_gateway_negative_condition_has_condition_text(self):
        xml = (FIXTURES_DIR / "gateway_negative_condition.bpmn").read_text()
        bpmn = parse_bpmn_xml(xml)
        self.assertNotIn("parse_error", bpmn)
        flows = bpmn.get("sequence_flows") or {}
        cond = flows.get("flow_cond", {}).get("condition", "")
        self.assertIn("state.x", cond)
        self.assertIn("-1", cond)


class ParallelGatewayTopologyTests(TestCase):
    """validate_parallel_gateway_topology: fork (1 in, 2+ out) vs join (2+ in, 1 out)."""

    def test_parallel_gateway_fork_valid(self):
        bpmn = {
            "elements": {
                "fork1": {
                    "type": "parallelGateway",
                    "incoming": ["s"],
                    "outgoing": ["a", "b"],
                }
            }
        }
        self.assertEqual(validate_parallel_gateway_topology(bpmn), [])

    def test_parallel_gateway_fork_three_outgoing_valid(self):
        bpmn = {
            "elements": {
                "f": {
                    "type": "parallelGateway",
                    "incoming": ["x"],
                    "outgoing": ["a", "b", "c"],
                }
            }
        }
        self.assertEqual(validate_parallel_gateway_topology(bpmn), [])

    def test_parallel_gateway_join_valid(self):
        bpmn = {
            "elements": {
                "join1": {
                    "type": "parallelGateway",
                    "incoming": ["a", "b"],
                    "outgoing": ["next"],
                }
            }
        }
        self.assertEqual(validate_parallel_gateway_topology(bpmn), [])

    def test_parallel_gateway_join_three_incoming_valid(self):
        bpmn = {
            "elements": {
                "j": {
                    "type": "parallelGateway",
                    "incoming": ["a", "b", "c"],
                    "outgoing": ["x"],
                }
            }
        }
        self.assertEqual(validate_parallel_gateway_topology(bpmn), [])

    def test_parallel_gateway_missing_incoming_invalid(self):
        bpmn = {
            "elements": {"gw": {"type": "parallelGateway", "incoming": [], "outgoing": ["a", "b"]}}
        }
        err = validate_parallel_gateway_topology(bpmn)
        self.assertEqual(len(err), 1)
        self.assertIn("parallelGateway 'gw'", err[0])
        self.assertIn("missing_incoming", err[0])

    def test_parallel_gateway_missing_outgoing_invalid(self):
        bpmn = {
            "elements": {"gw": {"type": "parallelGateway", "incoming": ["a", "b"], "outgoing": []}}
        }
        err = validate_parallel_gateway_topology(bpmn)
        self.assertEqual(len(err), 1)
        self.assertIn("missing_outgoing", err[0])

    def test_parallel_gateway_both_join_and_fork_invalid(self):
        bpmn = {
            "elements": {
                "gw": {
                    "type": "parallelGateway",
                    "incoming": ["a", "b"],
                    "outgoing": ["x", "y"],
                }
            }
        }
        err = validate_parallel_gateway_topology(bpmn)
        self.assertEqual(len(err), 1)
        self.assertIn("ambiguous_join_and_fork", err[0])

    def test_parallel_gateway_one_in_one_out_invalid(self):
        bpmn = {
            "elements": {
                "gw": {
                    "type": "parallelGateway",
                    "incoming": ["s"],
                    "outgoing": ["e"],
                }
            }
        }
        err = validate_parallel_gateway_topology(bpmn)
        self.assertEqual(len(err), 1)
        self.assertIn("pass_through", err[0])

    def test_parallel_gateway_fork_fewer_than_two_outgoing(self):
        """1 in, 0 out → missing_outgoing (not a fork)."""
        bpmn = {"elements": {"gw": {"type": "parallelGateway", "incoming": ["s"], "outgoing": []}}}
        err = validate_parallel_gateway_topology(bpmn)
        self.assertIn("missing_outgoing", err[0])

    def test_parallel_gateway_join_fewer_than_two_incoming(self):
        """1 in, 1 out already invalid; 0 in covered by missing_incoming."""
        bpmn = {
            "elements": {"gw": {"type": "parallelGateway", "incoming": ["s"], "outgoing": ["e"]}}
        }
        err = validate_parallel_gateway_topology(bpmn)
        self.assertIn("pass_through", err[0])

    def test_parallel_gateway_non_parallel_ignored(self):
        bpmn = {
            "elements": {
                "gw": {"type": "exclusiveGateway", "incoming": ["a"], "outgoing": ["b"]},
            }
        }
        self.assertEqual(validate_parallel_gateway_topology(bpmn), [])

    def test_parallel_gateway_degree_rules_exhaustive_small_grid(self):
        """Only fork (1 in, 2+ out) and join (2+ in, 1 out) accept; grid documents all pairs."""
        for ni in range(5):
            for no in range(5):
                inc = [f"x{ni}_{j}" for j in range(ni)]
                out = [f"y{no}_{j}" for j in range(no)]
                bpmn = {
                    "elements": {
                        "gw": {
                            "type": "parallelGateway",
                            "incoming": inc,
                            "outgoing": out,
                        }
                    }
                }
                errs = validate_parallel_gateway_topology(bpmn)
                ok_fork = ni == 1 and no >= 2
                ok_join = ni >= 2 and no == 1
                if ok_fork or ok_join:
                    self.assertEqual(
                        errs, [], msg=f"expected valid for incoming={ni} outgoing={no}"
                    )
                else:
                    self.assertEqual(
                        len(errs),
                        1,
                        msg=f"expected one error for incoming={ni} outgoing={no}",
                    )


class SaveWorkflowParallelGatewayTests(TestCase):
    """save_workflow blocks on validate_bpmn_for_save before writing BPMN."""

    @patch("agent_app.workflow_registry.workflow_registry", new_callable=MagicMock)
    @patch("agent_app.workflow_context.parse_bpmn_xml")
    def test_save_workflow_rejects_invalid_parallel_gateway_topology(self, mock_parse, mock_reg):
        mock_parse.return_value = {
            "elements": {
                "start": {"type": "startEvent", "outgoing": ["gw"]},
                "gw": {
                    "type": "parallelGateway",
                    "incoming": ["start"],
                    "outgoing": ["end"],
                },
                "end": {"type": "endEvent", "incoming": ["gw"], "outgoing": []},
            }
        }
        tmp = Path(tempfile.mkdtemp(prefix="beeai_par_save_"))
        wid = "wf_par_save_test"
        try:
            wf_dir = tmp / "workflows" / wid
            wf_dir.mkdir(parents=True)
            (wf_dir / "metadata.yaml").write_text(
                f"id: {wid}\nname: Test\nicon: x\ncategory: test\n",
                encoding="utf-8",
            )
            mock_reg.get.return_value = {"metadata": SimpleNamespace(current_version_path=None)}
            orig_root = workflow_service.REPO_ROOT
            workflow_service.REPO_ROOT = tmp
            with self.assertRaises(ValueError) as ctx:
                workflow_service.save_workflow(
                    workflow_id=wid,
                    metadata_updates={},
                    file_updates={"workflow.bpmn": "<xml/>"},
                    bindings_json=None,
                    version_info={},
                    user_id=1,
                )
            msg = str(ctx.exception)
            self.assertIn("parallelGateway", msg)
            self.assertIn("pass_through", msg)
            self.assertFalse((wf_dir / "workflow.bpmn").exists())
        finally:
            workflow_service.REPO_ROOT = orig_root
            shutil.rmtree(tmp, ignore_errors=True)


def _sf(*keys):
    return {k: {} for k in keys}


class JoinGatewayParallelForkCorrelationTests(TestCase):
    """PAR-009: fork–join correlation beyond strictly linear single-hop branches."""

    def test_join_gateway_for_parallel_fork_allows_multi_task_branch_paths(self):
        bpmn = {
            "elements": {
                "task0": {"type": "serviceTask", "outgoing": ["forkGW"]},
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["task0"],
                    "outgoing": ["taskA1", "taskB"],
                },
                "taskA1": {"type": "serviceTask", "outgoing": ["taskA2"]},
                "taskA2": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "taskB": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "joinGW": {
                    "type": "parallelGateway",
                    "incoming": ["taskA2", "taskB"],
                    "outgoing": ["taskAfter"],
                },
                "taskAfter": {"type": "serviceTask", "outgoing": []},
            },
            "sequence_flows": _sf("t0", "ffa", "ffb", "a1", "a2", "jb", "jc"),
        }
        self.assertEqual(join_gateway_for_parallel_fork(bpmn, "forkGW"), "joinGW")
        self.assertEqual(validate_parallel_fork_join_correlation(bpmn), [])

    def test_join_gateway_for_parallel_fork_allows_safe_exclusive_convergence(self):
        bpmn = {
            "elements": {
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["t0"],
                    "outgoing": ["taskA", "taskB"],
                },
                "taskA": {"type": "serviceTask", "outgoing": ["xgw"]},
                "xgw": {
                    "type": "exclusiveGateway",
                    "incoming": ["taskA"],
                    "outgoing": ["taskAhi", "taskAlo"],
                },
                "taskAhi": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "taskAlo": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "taskB": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "joinGW": {
                    "type": "parallelGateway",
                    "incoming": ["taskAhi", "taskAlo", "taskB"],
                    "outgoing": ["end"],
                },
                "end": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": _sf("f1", "f2", "f3", "f4", "f5", "f6", "f7"),
        }
        self.assertEqual(join_gateway_for_parallel_fork(bpmn, "forkGW"), "joinGW")

    def test_join_gateway_for_parallel_fork_rejects_branch_reaching_different_joins(self):
        bpmn = {
            "elements": {
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["s"],
                    "outgoing": ["t1", "t2"],
                },
                "t1": {"type": "serviceTask", "outgoing": ["j1"]},
                "t2": {"type": "serviceTask", "outgoing": ["j2"]},
                "j1": {
                    "type": "parallelGateway",
                    "incoming": ["t1", "u1"],
                    "outgoing": ["e1"],
                },
                "j2": {
                    "type": "parallelGateway",
                    "incoming": ["t2", "u2"],
                    "outgoing": ["e2"],
                },
                "u1": {"type": "serviceTask", "outgoing": ["j1"]},
                "u2": {"type": "serviceTask", "outgoing": ["j2"]},
                "e1": {"type": "endEvent", "outgoing": []},
                "e2": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": _sf("a", "b", "c", "d", "e", "f"),
        }
        with self.assertRaises(ValueError) as ctx:
            join_gateway_for_parallel_fork(bpmn, "forkGW")
        self.assertIn("different joins", str(ctx.exception).lower())

    def test_join_gateway_for_parallel_fork_rejects_mixed_end_and_join_paths(self):
        bpmn = {
            "elements": {
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["s"],
                    "outgoing": ["t1", "t2"],
                },
                "t1": {"type": "serviceTask", "outgoing": ["endOnly"]},
                "t2": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "endOnly": {"type": "endEvent", "outgoing": []},
                "joinGW": {
                    "type": "parallelGateway",
                    "incoming": ["t2", "x"],
                    "outgoing": ["e"],
                },
                "x": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "e": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": _sf("a", "b", "c", "d"),
        }
        with self.assertRaises(ValueError) as ctx:
            join_gateway_for_parallel_fork(bpmn, "forkGW")
        self.assertIn("mixed", str(ctx.exception).lower())

    def test_join_gateway_for_parallel_fork_rejects_nested_parallel_fork(self):
        bpmn = {
            "elements": {
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["s"],
                    "outgoing": ["t1", "t2"],
                },
                "t1": {"type": "serviceTask", "outgoing": ["innerFork"]},
                "innerFork": {
                    "type": "parallelGateway",
                    "incoming": ["t1"],
                    "outgoing": ["a", "b"],
                },
                "a": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "b": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "t2": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "joinGW": {
                    "type": "parallelGateway",
                    "incoming": ["a", "b", "t2"],
                    "outgoing": ["end"],
                },
                "end": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": _sf("x", "y", "z", "w", "v"),
        }
        with self.assertRaises(ValueError) as ctx:
            join_gateway_for_parallel_fork(bpmn, "forkGW")
        self.assertIn("nested", str(ctx.exception).lower())

    def test_join_gateway_exclusive_rejects_mix_end_and_join_under_same_gateway(self):
        bpmn = {
            "elements": {
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["s"],
                    "outgoing": ["taskA", "taskB"],
                },
                "taskA": {"type": "serviceTask", "outgoing": ["xgw"]},
                "xgw": {
                    "type": "exclusiveGateway",
                    "incoming": ["taskA"],
                    "outgoing": ["joinGW", "endEarly"],
                },
                "joinGW": {
                    "type": "parallelGateway",
                    "incoming": ["taskA", "taskB"],
                    "outgoing": ["e"],
                },
                "endEarly": {"type": "endEvent", "outgoing": []},
                "taskB": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "e": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": _sf("a", "b", "c", "d", "e"),
        }
        with self.assertRaises(ValueError) as ctx:
            join_gateway_for_parallel_fork(bpmn, "forkGW")
        self.assertIn("mix", str(ctx.exception).lower())

    def test_join_gateway_fork_only_still_none(self):
        bpmn = {
            "elements": {
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["s"],
                    "outgoing": ["e1", "e2"],
                },
                "e1": {"type": "endEvent", "outgoing": []},
                "e2": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": _sf("a", "b"),
        }
        self.assertIsNone(join_gateway_for_parallel_fork(bpmn, "forkGW"))

    def test_validate_bpmn_for_save_reports_fork_join_correlation(self):
        bpmn = {
            "elements": {
                "start": {"type": "startEvent", "outgoing": ["forkGW"]},
                "forkGW": {
                    "type": "parallelGateway",
                    "incoming": ["start"],
                    "outgoing": ["t1", "t2"],
                },
                "t1": {"type": "serviceTask", "outgoing": ["endOnly"]},
                "t2": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "endOnly": {"type": "endEvent", "outgoing": []},
                "joinGW": {
                    "type": "parallelGateway",
                    "incoming": ["t2", "u"],
                    "outgoing": ["e"],
                },
                "u": {"type": "serviceTask", "outgoing": ["joinGW"]},
                "e": {"type": "endEvent", "outgoing": []},
            },
            "sequence_flows": _sf("s", "a", "b", "c", "d"),
        }
        errs = validate_bpmn_for_save(bpmn, bindings=None)
        par = [x for x in errs if "parallelForkJoin" in x or "forkGW" in x]
        self.assertTrue(any("mixed" in e.lower() for e in par))


class NormalizeBindingsTests(TestCase):
    """normalize_bindings adds workflow_id/executor when missing and returns serviceTasks as dict."""

    def test_adds_workflow_id_when_missing(self):
        out = normalize_bindings({"serviceTasks": {"t1": {"handler": "t1"}}}, workflow_id="wf1")
        self.assertEqual(out.get("workflow_id"), "wf1")

    def test_adds_executor_when_missing(self):
        out = normalize_bindings(
            {"serviceTasks": {"t1": {"handler": "t1"}}},
            workflow_id="w",
            executor="workflows.w.workflow.Workflow",
        )
        self.assertEqual(out.get("executor"), "workflows.w.workflow.Workflow")

    def test_service_tasks_remain_dict(self):
        out = normalize_bindings(
            {"workflow_id": "w", "serviceTasks": {"a": {"handler": "a"}}},
            workflow_id="w",
        )
        self.assertIsInstance(out["serviceTasks"], dict)
        self.assertEqual(out["serviceTasks"]["a"]["handler"], "a")

    def test_does_not_overwrite_existing_workflow_id(self):
        out = normalize_bindings(
            {"workflow_id": "existing", "serviceTasks": {}},
            workflow_id="new",
        )
        self.assertEqual(out.get("workflow_id"), "existing")


class ValidateBpmnBindingsContextTests(TestCase):
    """validate_bpmn_bindings_context returns valid/errors/warnings for consistent BPMN and bindings."""

    def test_valid_context_returns_valid_true(self):
        xml = (FIXTURES_DIR / "sample.bpmn").read_text()
        bpmn = parse_bpmn_xml(xml)
        bindings = {
            "workflow_id": "test_workflow",
            "serviceTasks": {"task1": {"handler": "task1"}, "task2": {"handler": "task2"}},
        }
        code = {"handler_names": ["task1", "task2"]}
        context = {
            "workflow": {"id": "test_workflow"},
            "bpmn": bpmn,
            "bindings": bindings,
            "code": code,
        }
        result = validate_bpmn_bindings_context(context)
        self.assertTrue(result.get("valid"))
        self.assertEqual(result.get("errors"), [])


class ParseWorkflowPythonTests(TestCase):
    """parse_workflow_python extracts state class, workflow class, handler names, state fields."""

    def test_extracts_state_class_and_fields(self):
        code = """
from pydantic import BaseModel, Field

class MyState(BaseModel):
    x: str = Field(description="X input")
    y: int = Field(default=0)

class MyWorkflow:
    async def step_one(self, state):
        pass
"""
        result = parse_workflow_python(code)
        self.assertEqual(result["state_class_name"], "MyState")
        self.assertIn("x", result["state_field_names"])
        self.assertIn("y", result["state_field_names"])
        self.assertEqual(result["state_field_descriptions"].get("x"), "X input")
        self.assertIn("step_one", result["handler_names"])


_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"


class BoundaryEventsParseAndValidateTests(TestCase):
    """PAR-014: boundary timer/error parsing and validate_bpmn_boundary_events."""

    def _good_timer_boundary_xml(self) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="{_NS}" targetNamespace="http://t">
  <bpmn:process id="P1" isExecutable="true">
    <bpmn:startEvent id="start"/>
    <bpmn:sequenceFlow id="f0" sourceRef="start" targetRef="task1"/>
    <bpmn:serviceTask id="task1"/>
    <bpmn:sequenceFlow id="f1" sourceRef="task1" targetRef="task2"/>
    <bpmn:serviceTask id="task2"/>
    <bpmn:sequenceFlow id="f2" sourceRef="task2" targetRef="end"/>
    <bpmn:endEvent id="end"/>
    <bpmn:boundaryEvent id="b_timer" attachedToRef="task1" cancelActivity="true">
      <bpmn:timerEventDefinition>
        <bpmn:timeDuration>PT5M</bpmn:timeDuration>
      </bpmn:timerEventDefinition>
    </bpmn:boundaryEvent>
    <bpmn:sequenceFlow id="fb" sourceRef="b_timer" targetRef="alt"/>
    <bpmn:serviceTask id="alt"/>
    <bpmn:sequenceFlow id="fa" sourceRef="alt" targetRef="endAlt"/>
    <bpmn:endEvent id="endAlt"/>
  </bpmn:process>
</bpmn:definitions>"""

    def test_parse_populates_timer_boundary(self):
        bpmn = parse_bpmn_xml(self._good_timer_boundary_xml())
        self.assertNotIn("parse_error", bpmn)
        tb = get_timer_boundary_for_task(bpmn, "task1")
        self.assertIsNotNone(tb)
        self.assertEqual(tb.get("boundary_id"), "b_timer")
        self.assertEqual(tb.get("target_element_id"), "alt")
        self.assertEqual(tb.get("duration_iso"), "PT5M")
        self.assertEqual(validate_bpmn_boundary_events(bpmn), [])

    def test_non_interrupting_boundary_rejected(self):
        xml = self._good_timer_boundary_xml().replace(
            'cancelActivity="true"', 'cancelActivity="false"'
        )
        bpmn = parse_bpmn_xml(xml)
        errs = validate_bpmn_boundary_events(bpmn)
        self.assertTrue(any("non-interrupting" in e for e in errs))

    def test_double_outgoing_from_boundary_rejected(self):
        xml = self._good_timer_boundary_xml()
        xml = xml.replace(
            '<bpmn:sequenceFlow id="fa" sourceRef="alt"',
            '<bpmn:sequenceFlow id="fb2" sourceRef="b_timer" targetRef="task2"/>\n    <bpmn:sequenceFlow id="fa" sourceRef="alt"',
        )
        bpmn = parse_bpmn_xml(xml)
        errs = validate_bpmn_boundary_events(bpmn)
        self.assertTrue(any("exactly one outgoing" in e for e in errs))

    def test_boundary_on_invalid_attach_type_rejected(self):
        xml = self._good_timer_boundary_xml().replace(
            'attachedToRef="task1"', 'attachedToRef="end"'
        )
        bpmn = parse_bpmn_xml(xml)
        errs = validate_bpmn_boundary_events(bpmn)
        self.assertTrue(
            any("endEvent" in e or "scriptTask" in e or "may have boundaries" in e for e in errs)
        )

    def test_error_boundary_parse_and_validate(self):
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="{_NS}" targetNamespace="http://t">
  <bpmn:process id="P1" isExecutable="true">
    <bpmn:startEvent id="start"/>
    <bpmn:sequenceFlow id="f0" sourceRef="start" targetRef="task1"/>
    <bpmn:serviceTask id="task1"/>
    <bpmn:sequenceFlow id="f1" sourceRef="task1" targetRef="end"/>
    <bpmn:endEvent id="end"/>
    <bpmn:boundaryEvent id="b_err" attachedToRef="task1">
      <bpmn:errorEventDefinition/>
    </bpmn:boundaryEvent>
    <bpmn:sequenceFlow id="fe" sourceRef="b_err" targetRef="recover"/>
    <bpmn:serviceTask id="recover"/>
    <bpmn:sequenceFlow id="fr" sourceRef="recover" targetRef="endR"/>
    <bpmn:endEvent id="endR"/>
  </bpmn:process>
</bpmn:definitions>"""
        bpmn = parse_bpmn_xml(xml)
        self.assertNotIn("parse_error", bpmn)
        bucket = (bpmn.get("boundary_by_task") or {}).get("task1") or {}
        self.assertIn("error", bucket)
        self.assertEqual(bucket["error"].get("target_element_id"), "recover")
        self.assertEqual(validate_bpmn_boundary_events(bpmn), [])

    def test_validate_bpmn_for_save_includes_boundary_checks(self):
        bpmn = parse_bpmn_xml(self._good_timer_boundary_xml())
        self.assertEqual(validate_bpmn_for_save(bpmn), [])

    def test_intermediate_catch_timer_parse_traverse_validate(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D" targetNamespace="t">
  <bpmn:process id="P" isExecutable="true">
    <bpmn:startEvent id="st"><bpmn:outgoing>f0</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="f0" sourceRef="st" targetRef="t1"/>
    <bpmn:serviceTask id="t1"><bpmn:incoming>f0</bpmn:incoming><bpmn:outgoing>f1</bpmn:outgoing></bpmn:serviceTask>
    <bpmn:sequenceFlow id="f1" sourceRef="t1" targetRef="ic"/>
    <bpmn:intermediateCatchEvent id="ic"><bpmn:incoming>f1</bpmn:incoming><bpmn:outgoing>f2</bpmn:outgoing>
      <bpmn:timerEventDefinition><bpmn:timeDuration>PT5M</bpmn:timeDuration></bpmn:timerEventDefinition>
    </bpmn:intermediateCatchEvent>
    <bpmn:sequenceFlow id="f2" sourceRef="ic" targetRef="t2"/>
    <bpmn:serviceTask id="t2"><bpmn:incoming>f2</bpmn:incoming><bpmn:outgoing>f3</bpmn:outgoing></bpmn:serviceTask>
    <bpmn:sequenceFlow id="f3" sourceRef="t2" targetRef="en"/>
    <bpmn:endEvent id="en"><bpmn:incoming>f3</bpmn:incoming></bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>"""
        bpmn = parse_bpmn_xml(xml)
        self.assertNotIn("parse_error", bpmn)
        ic = bpmn["elements"]["ic"]
        self.assertEqual(ic.get("catch_kind"), "timer")
        self.assertEqual(ic.get("catch_duration_iso"), "PT5M")
        r = traverse_until_executable(bpmn, "st", set())
        self.assertEqual(r, "t1")
        self.assertEqual(traverse_until_executable(bpmn, "t1", set()), "t1")
        r2 = traverse_until_executable(bpmn, "t1", set(), from_completed=True)
        self.assertEqual(r2, "ic")
        self.assertEqual(validate_bpmn_intermediate_catch_events(bpmn), [])

    def test_intermediate_catch_validation_unsupported_signal(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D" targetNamespace="t">
  <bpmn:process id="P" isExecutable="true">
    <bpmn:startEvent id="st"><bpmn:outgoing>f0</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="f0" sourceRef="st" targetRef="ic"/>
    <bpmn:intermediateCatchEvent id="ic"><bpmn:incoming>f0</bpmn:incoming><bpmn:outgoing>f1</bpmn:outgoing>
      <bpmn:signalEventDefinition/></bpmn:intermediateCatchEvent>
    <bpmn:sequenceFlow id="f1" sourceRef="ic" targetRef="t2"/>
    <bpmn:serviceTask id="t2"><bpmn:incoming>f1</bpmn:incoming><bpmn:outgoing>f3</bpmn:outgoing></bpmn:serviceTask>
    <bpmn:endEvent id="en"><bpmn:incoming>f3</bpmn:incoming></bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>"""
        bpmn = parse_bpmn_xml(xml)
        errs = validate_bpmn_intermediate_catch_events(bpmn)
        self.assertTrue(any("timer" in e.lower() and "message" in e.lower() for e in errs))

    def test_intermediate_catch_validation_multi_outgoing_timer(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D" targetNamespace="t">
  <bpmn:process id="P" isExecutable="true">
    <bpmn:startEvent id="st"><bpmn:outgoing>f0</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="f0" sourceRef="st" targetRef="ic"/>
    <bpmn:intermediateCatchEvent id="ic"><bpmn:incoming>f0</bpmn:incoming>
      <bpmn:outgoing>f1</bpmn:outgoing><bpmn:outgoing>f2</bpmn:outgoing>
      <bpmn:timerEventDefinition><bpmn:timeDuration>PT1S</bpmn:timeDuration></bpmn:timerEventDefinition>
    </bpmn:intermediateCatchEvent>
    <bpmn:sequenceFlow id="f1" sourceRef="ic" targetRef="t2"/>
    <bpmn:sequenceFlow id="f2" sourceRef="ic" targetRef="t3"/>
    <bpmn:serviceTask id="t2"><bpmn:incoming>f1</bpmn:incoming></bpmn:serviceTask>
    <bpmn:serviceTask id="t3"><bpmn:incoming>f2</bpmn:incoming></bpmn:serviceTask>
  </bpmn:process>
</bpmn:definitions>"""
        bpmn = parse_bpmn_xml(xml)
        errs = validate_bpmn_intermediate_catch_events(bpmn)
        self.assertTrue(any("exactly one outgoing" in e.lower() for e in errs))


class EmbeddedSubprocessParseValidateTests(TestCase):
    """PAR-016: parse embedded subProcess, validate shape."""

    def _valid_subprocess_xml(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D" targetNamespace="t">
  <bpmn:process id="P" isExecutable="true">
    <bpmn:startEvent id="st"><bpmn:outgoing>f0</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="f0" sourceRef="st" targetRef="t_pre"/>
    <bpmn:serviceTask id="t_pre"><bpmn:incoming>f0</bpmn:incoming><bpmn:outgoing>f1</bpmn:outgoing></bpmn:serviceTask>
    <bpmn:sequenceFlow id="f1" sourceRef="t_pre" targetRef="sp"/>
    <bpmn:subProcess id="sp" name="Inner">
      <bpmn:incoming>f1</bpmn:incoming><bpmn:outgoing>f_sp_out</bpmn:outgoing>
      <bpmn:startEvent id="si"><bpmn:outgoing>fs0</bpmn:outgoing></bpmn:startEvent>
      <bpmn:sequenceFlow id="fs0" sourceRef="si" targetRef="tin"/>
      <bpmn:serviceTask id="tin"><bpmn:incoming>fs0</bpmn:incoming><bpmn:outgoing>fs1</bpmn:outgoing></bpmn:serviceTask>
      <bpmn:sequenceFlow id="fs1" sourceRef="tin" targetRef="endi"/>
      <bpmn:endEvent id="endi"><bpmn:incoming>fs1</bpmn:incoming></bpmn:endEvent>
    </bpmn:subProcess>
    <bpmn:sequenceFlow id="f_sp_out" sourceRef="sp" targetRef="t_post"/>
    <bpmn:serviceTask id="t_post"><bpmn:incoming>f_sp_out</bpmn:incoming><bpmn:outgoing>fe</bpmn:outgoing></bpmn:serviceTask>
    <bpmn:sequenceFlow id="fe" sourceRef="t_post" targetRef="en"/>
    <bpmn:endEvent id="en"><bpmn:incoming>fe</bpmn:incoming></bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>"""

    def test_parse_subprocess_sets_container_and_root_ids(self):
        bpmn = parse_bpmn_xml(self._valid_subprocess_xml())
        self.assertNotIn("parse_error", bpmn)
        self.assertIn("sp", bpmn.get("subprocess_root_ids") or [])
        self.assertEqual(bpmn["elements"]["tin"].get("subprocess_container"), "sp")
        self.assertEqual(bpmn["elements"]["sp"].get("type"), "subProcess")
        self.assertNotIn("subprocess_container", bpmn["elements"]["sp"])

    def test_validate_embedded_subprocess_ok(self):
        bpmn = parse_bpmn_xml(self._valid_subprocess_xml())
        self.assertEqual(validate_bpmn_embedded_subprocesses(bpmn), [])
        self.assertEqual(validate_bpmn_for_save(bpmn), [])

    def test_two_internal_starts_rejected(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D" targetNamespace="t">
  <bpmn:process id="P" isExecutable="true">
    <bpmn:startEvent id="st"><bpmn:outgoing>f0</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="f0" sourceRef="st" targetRef="sp"/>
    <bpmn:subProcess id="sp"><bpmn:incoming>f0</bpmn:incoming><bpmn:outgoing>f1</bpmn:outgoing>
      <bpmn:startEvent id="s1"><bpmn:outgoing>a</bpmn:outgoing></bpmn:startEvent>
      <bpmn:startEvent id="s2"><bpmn:outgoing>b</bpmn:outgoing></bpmn:startEvent>
      <bpmn:sequenceFlow id="a" sourceRef="s1" targetRef="e1"/>
      <bpmn:sequenceFlow id="b" sourceRef="s2" targetRef="e1"/>
      <bpmn:endEvent id="e1"><bpmn:incoming>a</bpmn:incoming><bpmn:incoming>b</bpmn:incoming></bpmn:endEvent>
    </bpmn:subProcess>
    <bpmn:sequenceFlow id="f1" sourceRef="sp" targetRef="en"/>
    <bpmn:endEvent id="en"><bpmn:incoming>f1</bpmn:incoming></bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>"""
        bpmn = parse_bpmn_xml(xml)
        errs = validate_bpmn_embedded_subprocesses(bpmn)
        self.assertTrue(any("exactly one internal startEvent" in e for e in errs))

    def test_nested_subprocess_rejected(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D" targetNamespace="t">
  <bpmn:process id="P" isExecutable="true">
    <bpmn:startEvent id="st"><bpmn:outgoing>f0</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="f0" sourceRef="st" targetRef="outer"/>
    <bpmn:subProcess id="outer"><bpmn:incoming>f0</bpmn:incoming><bpmn:outgoing>fo</bpmn:outgoing>
      <bpmn:startEvent id="so"><bpmn:outgoing>fi</bpmn:outgoing></bpmn:startEvent>
      <bpmn:sequenceFlow id="fi" sourceRef="so" targetRef="inner"/>
      <bpmn:subProcess id="inner"><bpmn:incoming>fi</bpmn:incoming><bpmn:outgoing>fj</bpmn:outgoing>
        <bpmn:startEvent id="si"><bpmn:outgoing>fk</bpmn:outgoing></bpmn:startEvent>
        <bpmn:sequenceFlow id="fk" sourceRef="si" targetRef="ei"/>
        <bpmn:endEvent id="ei"><bpmn:incoming>fk</bpmn:incoming></bpmn:endEvent>
      </bpmn:subProcess>
      <bpmn:sequenceFlow id="fj" sourceRef="inner" targetRef="eo"/>
      <bpmn:endEvent id="eo"><bpmn:incoming>fj</bpmn:incoming></bpmn:endEvent>
    </bpmn:subProcess>
    <bpmn:sequenceFlow id="fo" sourceRef="outer" targetRef="en"/>
    <bpmn:endEvent id="en"><bpmn:incoming>fo</bpmn:incoming></bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>"""
        bpmn = parse_bpmn_xml(xml)
        errs = validate_bpmn_embedded_subprocesses(bpmn)
        self.assertTrue(any("Nested embedded subprocess" in e for e in errs))
