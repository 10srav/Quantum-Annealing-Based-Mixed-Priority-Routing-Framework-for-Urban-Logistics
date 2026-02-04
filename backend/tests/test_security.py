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

# Set test API key before importing app (must be done early)
# The hash of 'test-api-key-12345' is computed and set as env var
TEST_API_KEY = "test-api-key-12345"
TEST_API_KEY_HASH = "a7f5397443359ea76c2bda898e7c49ece2e2d7a7c6cc2b7968f3f9c5d2d7a1e2"

# Override settings before app import
os.environ["API_KEY_HASH"] = TEST_API_KEY_HASH

from src.auth import hash_api_key

# Verify the hash is correct (this is the actual hash we need)
ACTUAL_HASH = hash_api_key(TEST_API_KEY)
os.environ["API_KEY_HASH"] = ACTUAL_HASH

# Now import app after setting up auth
from app.main import app
from src.security import validate_graph_path, DATA_DIR, GRAPH_NAME_PATTERN


# Create test client with authentication header by default
client = TestClient(app, raise_server_exceptions=False)

# Default headers for authenticated requests
AUTH_HEADERS = {"X-API-Key": TEST_API_KEY}


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

    def test_traversal_raises_valueerror(self):
        """Path traversal should raise ValueError."""
        with pytest.raises(ValueError) as exc:
            validate_graph_path("../secret")
        assert "Invalid graph name" in str(exc.value)

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
