"""
API Endpoint Testleri
"""
import pytest
from fastapi.testclient import TestClient


def test_public_mutabakat_endpoint(client):
    """Public mutabakat endpoint testi (token olmadan)"""
    # Geçersiz token ile test
    response = client.get("/api/public/mutabakat/invalid_token")
    assert response.status_code in [404, 400]  # Token geçersiz olmalı


def test_health_endpoint(client):
    """Health check endpoint testi"""
    response = client.get("/health")
    assert response.status_code == 200


def test_docs_endpoint(client):
    """API docs endpoint testi"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint(client):
    """OpenAPI schema endpoint testi"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert "paths" in data

