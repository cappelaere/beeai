"""
Shared condition syntax for BPMN exclusive gateway conditions.
Single parse path and single evaluation path; used by validation and runtime.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, List, Union


# Parsed expression types (deliberately small language)
@dataclass(frozen=True)
class LiteralCondition:
    value: bool


@dataclass(frozen=True)
class ComparisonCondition:
    state_attr: str
    op: str  # ==, !=, >, >=, <, <=
    right_value: Union[bool, int, float, str]


@dataclass(frozen=True)
class InListCondition:
    state_attr: str
    right_list: List[Any]


ParsedCondition = Union[LiteralCondition, ComparisonCondition, InListCondition]


def _parse_right_value(raw: str) -> Any:
    """Parse right-hand side to bool, int, float, or string."""
    raw = raw.strip("'\"").strip()
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if raw.lstrip("-").isdigit():
        return int(raw)
    if raw.lstrip("-").replace(".", "", 1).isdigit():
        return float(raw)
    if raw.startswith(("'", '"')) and raw.endswith(("'", '"')):
        return raw[1:-1]
    return raw


def parse_condition(condition_text: str) -> ParsedCondition:
    """
    Parse condition text into a typed expression. Raises ValueError with a clear message
    if the text is unsupported or invalid. Use for validation and runtime.
    """
    if not condition_text or not condition_text.strip():
        raise ValueError("Condition is empty")
    text = condition_text.strip()
    if text.lower() == "true":
        return LiteralCondition(True)
    if text.lower() == "false":
        return LiteralCondition(False)
    for op, sep in [("==", "=="), ("!=", "!="), (">=", ">="), ("<=", "<="), (">", ">"), ("<", "<")]:
        if sep in text:
            left, _, right = text.partition(sep)
            left, right = left.strip(), right.strip()
            if not left.startswith("state."):
                raise ValueError(
                    f"Unsupported condition: expected state.<attr> op value, got left side {left!r}. "
                    "Use a single identifier for attr (no dots)."
                )
            attr = left[6:].strip()
            if not attr.replace("_", "").isalnum():
                raise ValueError(
                    f"Invalid attribute {attr!r}: use letters, digits, underscores only (no dots)."
                )
            try:
                right_val = _parse_right_value(right)
            except Exception as e:
                raise ValueError(f"Could not parse value {right!r}: {e}") from e
            return ComparisonCondition(state_attr=attr, op=op, right_value=right_val)
    if " in " in text and text.strip().startswith("state."):
        left, _, right = text.partition(" in ")
        left, right = left.strip(), right.strip()
        if not left.startswith("state."):
            raise ValueError("Unsupported condition: expected state.<attr> in [...]")
        attr = left[6:].strip()
        if not attr.replace("_", "").isalnum():
            raise ValueError(f"Invalid attribute {attr!r}: use letters, digits, underscores only.")
        if not (right.startswith("[") and right.endswith("]")):
            raise ValueError(
                "Unsupported condition: right side of 'in' must be a list literal [...], e.g. [1, 2, 3]"
            )
        try:
            right_list = ast.literal_eval(right)
        except Exception as e:
            raise ValueError(f"Invalid list literal {right!r}: {e}") from e
        if not isinstance(right_list, list):
            raise ValueError("Right side of 'in' must evaluate to a list")
        return InListCondition(state_attr=attr, right_list=right_list)
    raise ValueError(
        f"Unsupported condition: {text!r}. "
        "Use true/false, state.<attr> op value (op: ==, !=, >, >=, <, <=), or state.<attr> in [...]."
    )


def is_supported_condition_syntax(condition_text: str) -> bool:
    """
    Return True only if the condition parses successfully. Same grammar as parse_condition.
    """
    if not condition_text or not condition_text.strip():
        return False
    try:
        parse_condition(condition_text.strip())
        return True
    except ValueError:
        return False


def evaluate_condition(parsed: ParsedCondition, state: Any) -> bool:
    """Evaluate a parsed condition against workflow state."""
    if isinstance(parsed, LiteralCondition):
        return parsed.value
    if isinstance(parsed, ComparisonCondition):
        val = getattr(state, parsed.state_attr, None)
        r = parsed.right_value
        if parsed.op == "==":
            return val == r
        if parsed.op == "!=":
            return val != r
        if (
            parsed.op in (">", ">=", "<", "<=")
            and isinstance(val, (int, float))
            and isinstance(r, (int, float))
        ):
            if parsed.op == ">":
                return val > r
            if parsed.op == ">=":
                return val >= r
            if parsed.op == "<":
                return val < r
            if parsed.op == "<=":
                return val <= r
        return False
    if isinstance(parsed, InListCondition):
        val = getattr(state, parsed.state_attr, None)
        return val in parsed.right_list
    return False
