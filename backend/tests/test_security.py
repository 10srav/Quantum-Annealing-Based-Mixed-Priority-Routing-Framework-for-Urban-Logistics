"""
Security Tests for Quantum Priority Router API.

This module tests security controls including:
- Path traversal prevention
- Graph name validation
- Error message sanitization (no path or stack trace leaks)
"""

import os
import re
import pytest
from fastapi.testclient import TestClient
from app.main import app
from src.config import get_settings
from src.security import validate_graph_path, DATA_DIR, GRAPH_NAME_PATTERN


# Create test client with authentication header by default
client = TestClient(app, raise_server_exceptions=False)

# Use the "test" API key (hash is configured via conftest.py and .env)
AUTH_HEADERS = {"X-API-Key": "test"}


# Helper for detecting sensitive information in responses
SENSITIVE_PATTERNS = [
    r'/home/',
    r'/Users/',
    r'C:\\\\',  # Escaped backslash for regex
    r'/var/',
    r'/etc/',
    r'backend/',
    r'\.py',
    r'Traceback',
    r'File "',
    r'line \d+',
]


def assert_no_sensitive_info(response_text: str):
    """Assert response doesn't contain sensitive path or stack info."""
    for pattern in SENSITIVE_PATTERNS:
        assert not re.search(pattern, response_text, re.IGNORECASE), \
            f"Response contains sensitive pattern '{pattern}': {response_text[:200]}"


class TestPathTraversal:
    """Tests for path traversal attack prevention.

    These tests verify that path traversal attempts are rejected.
    Note: FastAPI/Starlette may normalize or reject paths at the routing layer
    before they reach our endpoint, which is also acceptable security behavior.
    """

    def test_simple_traversal(self):
        """Request with ../ path traversal should not return file contents."""
        # Note: ../../../etc/passwd in URL path may be routed as /etc/passwd by framework
        # The important thing is that no sensitive file contents are returned
        response = client.get("/graphs/../../../etc/passwd", headers=AUTH_HEADERS)
        # Either 400 (security rejection), 404 (not found), or framework redirect
        assert response.status_code in [400, 404, 307]
        # Critical: Ensure no sensitive data leaked (Unix passwd file marker)
        assert "root:" not in response.text.lower()
        assert_no_sensitive_info(response.text)

    def test_traversal_via_valid_looking_name(self):
        """Request with path traversal embedded in name should return 400."""
        # This name has .. which will fail the GRAPH_NAME_PATTERN
        response = client.get("/graphs/..secret", headers=AUTH_HEADERS)
        assert response.status_code == 400
        assert_no_sensitive_info(response.text)

    def test_windows_traversal(self):
        """Request with Windows-style path traversal should return 400."""
        # Backslash is not allowed in graph names
        response = client.get("/graphs/test\\..\\secret", headers=AUTH_HEADERS)
        assert response.status_code == 400
        assert_no_sensitive_info(response.text)

    def test_null_byte_injection(self):
        """Request with null byte injection should return 400."""
        response = client.get("/graphs/valid%00.json", headers=AUTH_HEADERS)
        assert response.status_code == 400
        assert_no_sensitive_info(response.text)

    def test_name_with_dots(self):
        """Name with dots (used in traversal) should return 400."""
        response = client.get("/graphs/file.json", headers=AUTH_HEADERS)
        assert response.status_code == 400
        assert_no_sensitive_info(response.text)

    def test_encoded_traversal_name(self):
        """URL-encoded traversal sequence as single path segment should return 400."""
        # %2e%2e = .. in URL encoding - when this is the graph_name it should be rejected
        response = client.get("/graphs/%2e%2esecret", headers=AUTH_HEADERS)
        # The framework decodes %2e%2e to .. which then fails our pattern
        assert response.status_code == 400
        assert_no_sensitive_info(response.text)


class TestGraphNameValidation:
    """Tests for graph name validation at API level."""

    def test_valid_alphanumeric(self):
        """Valid alphanumeric name should work (200 or 404 if not exists)."""
        response = client.get("/graphs/city01", headers=AUTH_HEADERS)
        # Valid name format, so either 200 (exists) or 404 (not found)
        # but NOT 400 (validation error)
        assert response.status_code in [200, 404]

    def test_valid_with_hyphen(self):
        """Valid name with hyphen should work."""
        response = client.get("/graphs/city-test", headers=AUTH_HEADERS)
        assert response.status_code in [200, 404]

    def test_valid_with_underscore(self):
        """Valid name with underscore should work."""
        response = client.get("/graphs/city_test", headers=AUTH_HEADERS)
        assert response.status_code in [200, 404]

    def test_invalid_with_dots(self):
        """Name with dots should return 400."""
        response = client.get("/graphs/city.test", headers=AUTH_HEADERS)
        assert response.status_code == 400

    def test_invalid_with_space(self):
        """Name with space should return 400."""
        response = client.get("/graphs/city%20test", headers=AUTH_HEADERS)
        assert response.status_code == 400

    def test_invalid_with_slash_nested(self):
        """Name with slash creates nested route, should return 400 or 404."""
        response = client.get("/graphs/city/test", headers=AUTH_HEADERS)
        # This may be routed differently (not matching /graphs/{graph_name})
        # but should not leak info
        assert response.status_code in [400, 404]
        assert_no_sensitive_info(response.text)

    def test_empty_name(self):
        """Empty name routes to list endpoint, returns 200."""
        response = client.get("/graphs/", headers=AUTH_HEADERS)
        # FastAPI will route this to list_graphs endpoint
        assert response.status_code in [200, 307]  # 307 for redirect to /graphs


class TestErrorMessageSanitization:
    """Tests for error message sanitization - no path or stack trace leaks."""

    def test_traversal_error_no_path_leak(self):
        """Path traversal error should not contain actual system paths."""
        response = client.get("/graphs/..secret", headers=AUTH_HEADERS)
        assert_no_sensitive_info(response.text)
        # Should not contain DATA_DIR path
        data_dir_str = str(DATA_DIR)
        assert data_dir_str not in response.text

    def test_not_found_error_no_path_leak(self):
        """404 error should not expose DATA_DIR path."""
        response = client.get("/graphs/nonexistent-graph-name", headers=AUTH_HEADERS)
        assert response.status_code == 404
        assert_no_sensitive_info(response.text)
        # Should not contain internal path
        assert "data/" not in response.text.lower()
        data_dir_str = str(DATA_DIR)
        assert data_dir_str not in response.text

    def test_internal_error_no_stack_trace(self):
        """Long names should be handled gracefully without stack traces."""
        response = client.get("/graphs/" + "A" * 1000, headers=AUTH_HEADERS)
        # Should be handled gracefully:
        # - 400 (validation error - pattern match failed or too long)
        # - 404 (valid pattern but file not found)
        # - 414 (URI Too Long)
        # The key point is: no stack trace in response
        assert response.status_code in [400, 404, 414]
        assert_no_sensitive_info(response.text)

    def test_validation_error_safe_message(self):
        """Validation errors should have safe, generic messages."""
        response = client.get("/graphs/..secret", headers=AUTH_HEADERS)
        assert response.status_code == 400
        data = response.json()
        # Error message should be informative but not leak paths
        assert "detail" in data
        detail_lower = data["detail"].lower()
        assert "/home" not in detail_lower
        assert "users" not in detail_lower
        assert "c:\\" not in detail_lower


class TestAuthenticationRequired:
    """Tests that verify authentication is required for graph endpoints."""

    def test_graphs_list_requires_auth(self):
        """Graph list endpoint should require authentication."""
        response = client.get("/graphs")
        # 400 because X-API-Key header is required
        assert response.status_code == 400
        data = response.json()
        assert "x-api-key" in str(data).lower()

    def test_graph_get_requires_auth(self):
        """Graph get endpoint should require authentication."""
        response = client.get("/graphs/test")
        assert response.status_code == 400
        data = response.json()
        assert "x-api-key" in str(data).lower()

    def test_invalid_api_key_rejected(self):
        """Invalid API key should be rejected with 401."""
        response = client.get("/graphs/test", headers={"X-API-Key": "invalid-key"})
        assert response.status_code == 401


class TestValidateGraphPathUnit:
    """Unit tests for validate_graph_path function."""

    def test_valid_name_returns_path(self):
        """Valid name should return a Path object."""
        result = validate_graph_path("test-graph")
        assert result.name == "test-graph.json"
        assert result.parent == DATA_DIR.resolve()

    def test_valid_name_with_numbers(self):
        """Valid name with numbers should return a Path object."""
        result = validate_graph_path("city123")
        assert result.name == "city123.json"

    def test_valid_name_with_hyphen(self):
        """Valid name with hyphen should return a Path object."""
        result = validate_graph_path("city-grid")
        assert result.name == "city-grid.json"

    def test_valid_name_with_underscore(self):
        """Valid name with underscore should return a Path object."""
        result = validate_graph_path("city_grid")
        assert result.name == "city_grid.json"

    def test_traversal_raises_valueerror(self):
        """Path traversal should raise ValueError."""
        with pytest.raises(ValueError) as exc:
            validate_graph_path("../secret")
        assert "Invalid graph name" in str(exc.value)

    def test_traversal_error_message_safe(self):
        """ValueError message should not contain system paths."""
        with pytest.raises(ValueError) as exc:
            validate_graph_path("../../../etc/passwd")
        error_msg = str(exc.value)
        # Should be a safe, generic message
        assert "Invalid graph name" in error_msg
        # Should NOT contain actual path info
        assert str(DATA_DIR) not in error_msg
        assert "/etc" not in error_msg

    def test_dots_rejected(self):
        """Names with dots should be rejected."""
        with pytest.raises(ValueError):
            validate_graph_path("file.json")

    def test_spaces_rejected(self):
        """Names with spaces should be rejected."""
        with pytest.raises(ValueError):
            validate_graph_path("my graph")

    def test_special_chars_rejected(self):
        """Names with special characters should be rejected."""
        for char in ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')']:
            with pytest.raises(ValueError):
                validate_graph_path(f"graph{char}name")

    def test_slash_rejected(self):
        """Names with slashes should be rejected."""
        with pytest.raises(ValueError):
            validate_graph_path("path/to/file")

    def test_backslash_rejected(self):
        """Names with backslashes should be rejected."""
        with pytest.raises(ValueError):
            validate_graph_path("path\\to\\file")

    def test_empty_string_rejected(self):
        """Empty string should be rejected."""
        with pytest.raises(ValueError):
            validate_graph_path("")

    def test_unicode_rejected(self):
        """Names with unicode characters should be rejected."""
        with pytest.raises(ValueError):
            validate_graph_path("city\u00e9")  # e with accent

    def test_newline_rejected(self):
        """Names with newlines should be rejected."""
        with pytest.raises(ValueError):
            validate_graph_path("city\ntest")


class TestGraphNamePattern:
    """Tests for the GRAPH_NAME_PATTERN regex."""

    @pytest.mark.parametrize("name", [
        "valid",
        "valid123",
        "valid-name",
        "valid_name",
        "UPPERCASE",
        "MixedCase123",
        "a",
        "a1",
        "test-graph-1",
        "MY_GRAPH_2",
    ])
    def test_valid_patterns(self, name):
        """Valid names should match the pattern."""
        assert GRAPH_NAME_PATTERN.match(name)

    @pytest.mark.parametrize("name", [
        "../traversal",
        "with space",
        "with.dot",
        "with/slash",
        "with\\backslash",
        "",
        "with:colon",
        "with?question",
        "with*asterisk",
        "with<angle",
        "with>angle",
        "with|pipe",
        "with\"quote",
    ])
    def test_invalid_patterns(self, name):
        """Invalid names should not match the pattern."""
        assert not GRAPH_NAME_PATTERN.match(name)


class TestCORSBehavior:
    """Tests for CORS middleware behavior.

    FastAPI's CORSMiddleware handles CORS by either including or omitting
    Access-Control-Allow-Origin headers. When an origin is not in the allowed
    list, the header is simply not included, causing the browser to block the
    response. This is standard CORS behavior per the W3C spec.
    """

    def test_allowed_origin_gets_cors_headers(self):
        """Request from allowed origin should receive CORS headers."""
        # Default allowed origins include http://localhost:5173
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"}
        )
        assert response.status_code == 200
        # Should have CORS header matching the request origin
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_disallowed_origin_no_cors_headers(self):
        """Request from disallowed origin should NOT receive CORS headers."""
        response = client.get(
            "/health",
            headers={"Origin": "http://evil-site.com"}
        )
        assert response.status_code == 200  # Request still succeeds
        # But CORS header should be absent (browser will block)
        assert "access-control-allow-origin" not in response.headers

    def test_preflight_allowed_origin(self):
        """CORS preflight from allowed origin should return CORS headers."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )
        # Preflight returns 200 with CORS headers
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_preflight_disallowed_origin(self):
        """CORS preflight from disallowed origin should NOT return CORS headers."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://evil-site.com",
                "Access-Control-Request-Method": "GET",
            }
        )
        # Preflight may return 200 or 400, but should NOT have CORS headers
        assert "access-control-allow-origin" not in response.headers

    def test_no_origin_header_no_cors_response(self):
        """Request without Origin header should not get CORS headers."""
        response = client.get("/health")
        assert response.status_code == 200
        # No Origin header = server-to-server call, no CORS needed
        assert "access-control-allow-origin" not in response.headers

    def test_alternate_allowed_origin(self):
        """Both default allowed origins should work."""
        # Test http://localhost:3000 (alternate dev port)
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


class TestCORSConfiguration:
    """Tests for CORS environment configuration."""

    def test_cors_origins_parsing_comma_separated(self):
        """CORS_ORIGINS env var should parse comma-separated values."""
        from src.config import parse_cors_origins_value

        result = parse_cors_origins_value("https://app.example.com,https://admin.example.com")
        assert result == ["https://app.example.com", "https://admin.example.com"]

    def test_cors_origins_parsing_json_array(self):
        """CORS_ORIGINS env var should parse JSON array values."""
        from src.config import parse_cors_origins_value

        result = parse_cors_origins_value('["https://a.com", "https://b.com"]')
        assert result == ["https://a.com", "https://b.com"]

    def test_cors_origins_parsing_single_value(self):
        """Single origin should be parsed correctly."""
        from src.config import parse_cors_origins_value

        result = parse_cors_origins_value("https://app.example.com")
        assert result == ["https://app.example.com"]

    def test_cors_origins_parsing_with_whitespace(self):
        """Whitespace around origins should be trimmed."""
        from src.config import parse_cors_origins_value

        result = parse_cors_origins_value("  https://a.com  ,  https://b.com  ")
        assert result == ["https://a.com", "https://b.com"]

    def test_cors_origins_parsing_empty_values_filtered(self):
        """Empty values from double commas should be filtered."""
        from src.config import parse_cors_origins_value

        result = parse_cors_origins_value("https://a.com,,https://b.com")
        assert result == ["https://a.com", "https://b.com"]

    def test_wildcard_rejected_in_production(self):
        """Wildcard '*' should be rejected in production environment."""
        from src.config import Settings

        # Save current env
        old_cors = os.environ.get("CORS_ORIGINS")
        old_env = os.environ.get("ENVIRONMENT")

        try:
            os.environ["CORS_ORIGINS"] = "*"
            os.environ["ENVIRONMENT"] = "production"
            get_settings.cache_clear()

            with pytest.raises(ValueError) as exc:
                Settings()
            assert "Wildcard" in str(exc.value)
            assert "production" in str(exc.value)
        finally:
            # Restore env
            if old_cors:
                os.environ["CORS_ORIGINS"] = old_cors
            else:
                os.environ.pop("CORS_ORIGINS", None)
            if old_env:
                os.environ["ENVIRONMENT"] = old_env
            else:
                os.environ.pop("ENVIRONMENT", None)
            get_settings.cache_clear()

    def test_wildcard_allowed_in_development(self):
        """Wildcard '*' should be allowed in development environment."""
        from src.config import Settings

        # Save current env
        old_cors = os.environ.get("CORS_ORIGINS")
        old_env = os.environ.get("ENVIRONMENT")

        try:
            os.environ["CORS_ORIGINS"] = "*"
            os.environ["ENVIRONMENT"] = "development"
            get_settings.cache_clear()

            settings = Settings()
            assert "*" in settings.cors_origins
        finally:
            # Restore env
            if old_cors:
                os.environ["CORS_ORIGINS"] = old_cors
            else:
                os.environ.pop("CORS_ORIGINS", None)
            if old_env:
                os.environ["ENVIRONMENT"] = old_env
            else:
                os.environ.pop("ENVIRONMENT", None)
            get_settings.cache_clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
