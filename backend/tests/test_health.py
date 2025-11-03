"""
Health Check Testleri
"""
import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client):
    """Health endpoint testi"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]  # Veritabanı olmadan unhealthy olabilir


def test_root_endpoint(client):
    """Root endpoint testi"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "E-Mutabakat" in data["message"]

