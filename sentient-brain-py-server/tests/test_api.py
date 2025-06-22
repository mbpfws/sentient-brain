"""Basic API integration tests for health and context endpoints."""

import os
import pytest
from fastapi.testclient import TestClient

# Ensure project root is on PYTHONPATH
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from main import app  # noqa: E402

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "neo4j" in data and "weaviate" in data


def test_context_endpoint():
    # Use a known file inserted by earlier test (fallback to dummy.py)
    target = "src/helpers/dummy.py"
    resp = client.get("/context", params={"file": target})
    assert resp.status_code == 200
    data = resp.json()
    assert data["file"] == target
    # nodes or chunks may be empty if not yet indexed, but response keys exist
    assert "nodes" in data and "chunks" in data
