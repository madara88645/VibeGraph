import pytest
from pydantic import ValidationError

from app.models import GhostNarrateRequest, MAX_NODE_ID_LENGTH


def test_ghost_narrate_request_context_nodes_validation():
    # Valid request
    req = GhostNarrateRequest(node_id="test", context_nodes=["a", "b", "c"])
    assert req.context_nodes == ["a", "b", "c"]

    # Invalid request (element too long)
    with pytest.raises(ValidationError) as excinfo:
        GhostNarrateRequest(
            node_id="test", context_nodes=["a", "b", "c" * (MAX_NODE_ID_LENGTH + 1)]
        )

    assert "context node length cannot exceed" in str(excinfo.value)
