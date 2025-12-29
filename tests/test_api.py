"""
Tests for AI Expense Analysis Assistant
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and info endpoints"""
    
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_info(self):
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "capabilities" in data
        assert "endpoints" in data
        assert "supported_languages" in data


class TestExtractEndpoints:
    """Test extraction endpoints (requires API key)"""
    
    def test_extract_single_validation(self):
        # Test missing required field
        response = client.post("/expenses/extract", json={})
        assert response.status_code == 422  # Validation error
    
    def test_extract_multi_validation(self):
        response = client.post("/expenses/extract/multi", json={})
        assert response.status_code == 422
    
    def test_extract_batch_validation(self):
        response = client.post("/expenses/extract/batch", json={})
        assert response.status_code == 422


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_analytics_empty(self):
        response = client.post("/expenses/analytics", json={
            "expenses": [],
            "group_by": "category"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_amount"] == 0
    
    def test_analytics_with_data(self):
        response = client.post("/expenses/analytics", json={
            "expenses": [
                {"amount": 50, "currency": "MAD", "category": "transport"},
                {"amount": 30, "currency": "MAD", "category": "food"},
                {"amount": 100, "currency": "MAD", "category": "transport"}
            ],
            "group_by": "category"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_amount"] == 180
        assert data["count"] == 3
        assert "transport" in data["breakdown"]
        assert "food" in data["breakdown"]
    
    def test_summary(self):
        response = client.post("/expenses/analytics/summary", json=[
            {"amount": 50, "currency": "MAD", "category": "transport"}
        ])
        assert response.status_code == 200
        assert "summary" in response.json()
    
    def test_anomalies(self):
        response = client.post("/expenses/analytics/anomalies", json=[
            {"amount": 10},
            {"amount": 12},
            {"amount": 11},
            {"amount": 1000}  # Anomaly
        ])
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1


class TestExportEndpoints:
    """Test export endpoints"""
    
    def test_export_csv(self):
        response = client.post("/expenses/export/csv", json=[
            {"amount": 50, "currency": "MAD", "category": "transport"},
            {"amount": 30, "currency": "MAD", "category": "food"}
        ])
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_export_excel(self):
        response = client.post("/expenses/export/excel", json=[
            {"amount": 50, "currency": "MAD", "category": "transport"},
            {"amount": 30, "currency": "MAD", "category": "food"}
        ])
        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]


class TestOCREndpoints:
    """Test OCR endpoints validation"""
    
    def test_ocr_url_validation(self):
        # Test with invalid URL (will fail at processing, not validation)
        response = client.post("/expenses/ocr/url", params={
            "image_url": "https://example.com/receipt.jpg"
        })
        # Will return 500 because URL is fake, but endpoint is reachable
        assert response.status_code in [200, 500]
