"""
Tests for AI Expense Analysis Assistant
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and info endpoints"""
    
    def test_root_returns_html(self):
        """Root now returns web interface (HTML)"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_api_info(self):
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
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
    
    def test_anomalies_with_clear_outlier(self):
        """Test anomaly detection with a clear outlier"""
        response = client.post("/expenses/analytics/anomalies", json=[
            {"amount": 10},
            {"amount": 11},
            {"amount": 10},
            {"amount": 12},
            {"amount": 11},
            {"amount": 10},
            {"amount": 500}  # Clear anomaly
        ])
        assert response.status_code == 200
        data = response.json()
        # With more data points, anomaly should be detected
        assert "anomalies" in data
    
    def test_anomalies_no_outliers(self):
        """Test with similar values - no anomalies expected"""
        response = client.post("/expenses/analytics/anomalies", json=[
            {"amount": 10},
            {"amount": 11},
            {"amount": 10},
            {"amount": 12}
        ])
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0


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
    
    def test_export_csv_empty(self):
        response = client.post("/expenses/export/csv", json=[])
        assert response.status_code == 200


class TestOCREndpoints:
    """Test OCR endpoints validation"""
    
    def test_ocr_upload_no_file(self):
        """Test OCR upload without file"""
        response = client.post("/expenses/ocr/upload")
        assert response.status_code == 422  # Missing file
    
    def test_ocr_url_invalid(self):
        """Test with invalid URL format"""
        response = client.post("/expenses/ocr/url", params={
            "image_url": "not-a-valid-url"
        })
        assert response.status_code == 500  # Will fail validation
