"""
Tests for Swagger UI, ReDoc, and OpenAPI documentation security.
Verifies that interactive documentation and schema endpoints are disabled in production environments
to prevent API schema leakage.
"""
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.config import Settings


def test_docs_enabled_in_development():
    """Verify that in development environment, docs and schema endpoints are available."""
    dev_settings = Settings(ENVIRONMENT="development")
    assert not dev_settings.is_production
    assert dev_settings.docs_url == "/docs"
    assert dev_settings.redoc_url == "/redoc"
    assert dev_settings.openapi_url == "/openapi.json"

    app = FastAPI(
        title=dev_settings.APP_NAME,
        version=dev_settings.APP_VERSION,
        docs_url=dev_settings.docs_url,
        redoc_url=dev_settings.redoc_url,
        openapi_url=dev_settings.openapi_url,
    )
    client = TestClient(app)

    # Swagger UI
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200

    # OpenAPI JSON Schema
    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    assert "openapi" in res_openapi.json()

    # ReDoc UI
    res_redoc = client.get("/redoc")
    assert res_redoc.status_code == 200


def test_docs_disabled_in_production():
    """Verify that in production environment, docs and schema endpoints are disabled (404)."""
    prod_settings = Settings(ENVIRONMENT="production")
    assert prod_settings.is_production
    assert prod_settings.docs_url is None
    assert prod_settings.redoc_url is None
    assert prod_settings.openapi_url is None

    app = FastAPI(
        title=prod_settings.APP_NAME,
        version=prod_settings.APP_VERSION,
        docs_url=prod_settings.docs_url,
        redoc_url=prod_settings.redoc_url,
        openapi_url=prod_settings.openapi_url,
    )
    client = TestClient(app)

    # Swagger UI must be 404
    res_docs = client.get("/docs")
    assert res_docs.status_code == 404

    # OpenAPI JSON Schema must be 404
    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 404

    # ReDoc UI must be 404
    res_redoc = client.get("/redoc")
    assert res_redoc.status_code == 404


def test_docs_disabled_in_prod_shorthand():
    """Verify that 'prod' alias is also recognized as production."""
    prod_settings = Settings(ENVIRONMENT="prod")
    assert prod_settings.is_production
    assert prod_settings.docs_url is None
    assert prod_settings.redoc_url is None
    assert prod_settings.openapi_url is None


def test_explicit_docs_url_override():
    """Verify explicit override of documentation URLs takes precedence."""
    custom_settings = Settings(
        ENVIRONMENT="production",
        DOCS_URL="/custom-docs",
        REDOC_URL="/custom-redoc",
        OPENAPI_URL="/custom-openapi.json",
    )
    assert custom_settings.docs_url == "/custom-docs"
    assert custom_settings.redoc_url == "/custom-redoc"
    assert custom_settings.openapi_url == "/custom-openapi.json"

