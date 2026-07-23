"""Direct unit tests for the private scoring helpers in app/services/learning_path.py.

_is_public_api, _is_entry_point, and _complexity_penalty feed directly into
build_learning_path's ranking score but have no direct boundary-condition
tests of their own today.
"""

from app.services.learning_path import (
    _complexity_penalty,
    _is_entry_point,
    _is_public_api,
)


# ---------------------------------------------------------------------------
# _is_public_api
# ---------------------------------------------------------------------------


def test_is_public_api_respects_explicit_bool_true():
    assert _is_public_api("node1", {"public_api": True, "label": "_private"}) is True


def test_is_public_api_respects_explicit_bool_false():
    assert _is_public_api("node1", {"public_api": False, "label": "public_name"}) is False


def test_is_public_api_infers_true_for_non_underscore_name():
    assert _is_public_api("node1", {"label": "module.public_func"}) is True


def test_is_public_api_infers_false_for_underscore_prefixed_name():
    assert _is_public_api("node1", {"label": "module._private_func"}) is False


def test_is_public_api_falls_back_to_node_id_when_no_label():
    assert _is_public_api("_hidden_node", {}) is False
    assert _is_public_api("visible_node", {}) is True


# ---------------------------------------------------------------------------
# _is_entry_point
# ---------------------------------------------------------------------------


def test_is_entry_point_respects_explicit_true():
    assert _is_entry_point("node1", {"entry_point": True, "label": "helper"}) is True


def test_is_entry_point_ignores_non_true_entry_point_value():
    # Only an exact `True` should count — a truthy string must not match.
    assert _is_entry_point("node1", {"entry_point": "yes", "label": "helper"}) is False


def test_is_entry_point_detects_known_function_names():
    for name in ("main", "run", "app"):
        assert _is_entry_point("node1", {"label": f"module.{name}"}) is True


def test_is_entry_point_detects_known_file_names():
    for file_name in ("__main__.py", "cli.py", "main.py", "serve.py"):
        assert _is_entry_point("node1", {"label": "helper", "file": file_name}) is True


def test_is_entry_point_detects_known_file_names_with_nested_path():
    assert _is_entry_point("node1", {"label": "helper", "file": "app/cli.py"}) is True


def test_is_entry_point_false_for_unrelated_function():
    assert _is_entry_point("node1", {"label": "module.helper", "file": "app/utils.py"}) is False


# ---------------------------------------------------------------------------
# _complexity_penalty
# ---------------------------------------------------------------------------


def test_complexity_penalty_zero_for_empty_data():
    assert _complexity_penalty({}) == 0.0


def test_complexity_penalty_combines_loc_nesting_and_deps():
    data = {"loc": 100, "nesting_depth": 2, "dependency_count": 3}
    # 100 * 0.1 + 2 * 4.0 + 3 * 2.0 = 10 + 8 + 6 = 24
    assert _complexity_penalty(data) == 24.0


def test_complexity_penalty_is_capped_at_40():
    data = {"loc": 10000, "nesting_depth": 50, "dependency_count": 50}
    assert _complexity_penalty(data) == 40.0


def test_complexity_penalty_ignores_negative_values():
    data = {"loc": -100, "nesting_depth": -5, "dependency_count": -2}
    assert _complexity_penalty(data) == 0.0


def test_complexity_penalty_treats_missing_fields_as_zero():
    assert _complexity_penalty({"loc": None, "nesting_depth": None}) == 0.0
