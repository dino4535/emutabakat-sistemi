"""
Smoke Tests - Temel sistem sağlığı testleri
Hızlı çalışan, kritik fonksiyonları test eden testler
"""
import pytest
from fastapi.testclient import TestClient


class TestSmoke:
    """Smoke test suite"""
    
    def test_app_starts(self, client):
        """Uygulama başlatılabiliyor mu?"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_health_check(self, client):
        """Health check çalışıyor mu?"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_api_docs_accessible(self, client):
        """API dokümantasyonu erişilebilir mi?"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_schema(self, client):
        """OpenAPI schema mevcut mu?"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

