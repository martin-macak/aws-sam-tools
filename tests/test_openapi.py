"""Tests for OpenAPI processing functionality."""

import json
import pytest
import yaml

from aws_sam_tools.openapi import (
    SafeNavigationDict,
    RuleContext,
    Rule,
    OutputFormat,
    detect_format,
    load_openapi_spec,
    apply_rules,
    process_openapi,
)


class TestSafeNavigationDict:
    """Test SafeNavigationDict functionality."""

    def test_dict_navigation(self):
        """Test navigation through nested dictionaries."""
        data = {"a": {"b": {"c": "value"}}}
        nav = SafeNavigationDict(data)

        assert nav.a.b.c == "value"
        assert nav["a"]["b"]["c"] == "value"
        assert nav.a.b.c.value == "value"

    def test_list_navigation(self):
        """Test navigation through lists."""
        data = {"items": [{"name": "first"}, {"name": "second"}]}
        nav = SafeNavigationDict(data)

        assert nav.items[0].name == "first"
        assert nav.items["1"].name == "second"
        assert nav.items[2].name == None

    def test_missing_keys(self):
        """Test navigation with missing keys."""
        data = {"a": {"b": "value"}}
        nav = SafeNavigationDict(data)

        assert nav.x == None
        assert nav.a.x == None
        assert nav.a.b.c == None
        assert nav.x.y.z == None

    def test_comparisons(self):
        """Test comparison operations."""
        data = {"auth": "oauth2", "empty": None}
        nav = SafeNavigationDict(data)

        assert nav.auth == "oauth2"
        assert nav.auth != "basic"
        assert nav.empty == None
        assert nav.missing == None
        assert bool(nav.auth) is True
        assert bool(nav.empty) is False
        assert bool(nav.missing) is False


class TestRuleContext:
    """Test RuleContext functionality."""

    def test_context_creation(self):
        """Test creating a rule context."""
        resource = {"security": [{"auth": []}]}
        context = RuleContext(resource, "/users", "get")

        assert context.path == "/users"
        assert context.method == "get"
        assert context.resource.security[0].auth.value == []

    def test_context_access(self):
        """Test accessing context via dictionary notation."""
        resource = {"summary": "Test"}
        context = RuleContext(resource)

        assert context["resource"].summary == "Test"
        assert context["path"] is None
        assert context["method"] is None


class TestRule:
    """Test Rule parsing and evaluation."""

    def test_rule_parsing(self):
        """Test parsing rule string."""
        rule = Rule("path/method : delete : resource.security is not None")

        assert rule.node_type.value == "path/method"
        assert rule.action.value == "delete"
        assert rule.filter_expression == "resource.security is not None"

    def test_invalid_rule_format(self):
        """Test invalid rule format."""
        with pytest.raises(ValueError, match="Invalid rule format"):
            Rule("invalid rule")

    def test_rule_evaluation(self):
        """Test evaluating rules."""
        rule = Rule("path/method : delete : resource.security is not None and resource.security != 'auth'")

        # Should match: has security but not 'auth'
        context1 = RuleContext({"security": [{"api_key": []}]})
        assert rule.evaluate(context1) is True

        # Should not match: has security with 'auth'
        context2 = RuleContext({"security": [{"auth": []}]})
        assert rule.evaluate(context2) is False

        # Should not match: no security
        context3 = RuleContext({"summary": "Test"})
        assert rule.evaluate(context3) is False

    def test_safe_evaluation(self):
        """Test that evaluation is safe."""
        # Try to use dangerous functions
        rule = Rule("path/method : delete : __import__('os').system('ls')")
        context = RuleContext({})

        # Should return False (evaluation fails safely)
        assert rule.evaluate(context) is False


class TestFormatDetection:
    """Test format detection functionality."""

    def test_detect_yaml_extension(self):
        """Test detecting YAML by extension."""
        assert detect_format("file.yaml") == OutputFormat.YAML
        assert detect_format("file.yml") == OutputFormat.YAML
        assert detect_format("FILE.YAML") == OutputFormat.YAML

    def test_detect_json_extension(self):
        """Test detecting JSON by extension."""
        assert detect_format("file.json") == OutputFormat.JSON
        assert detect_format("FILE.JSON") == OutputFormat.JSON

    def test_detect_with_hint(self):
        """Test detection with format hint."""
        assert detect_format("file.txt", OutputFormat.JSON) == OutputFormat.JSON
        assert detect_format("file.txt", OutputFormat.YAML) == OutputFormat.YAML

    def test_detect_stdin(self):
        """Test detection for stdin."""
        assert detect_format("-", OutputFormat.JSON) == OutputFormat.JSON
        assert detect_format(None, OutputFormat.YAML) == OutputFormat.YAML


class TestLoadOpenAPISpec:
    """Test loading OpenAPI specifications."""

    def test_load_json(self):
        """Test loading JSON spec."""
        content = '{"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}}'
        spec, format = load_openapi_spec(content)

        assert spec["openapi"] == "3.0.0"
        assert spec["info"]["title"] == "Test"
        assert format == OutputFormat.JSON

    def test_load_yaml(self):
        """Test loading YAML spec."""
        content = """openapi: 3.0.0
info:
  title: Test
  version: "1.0"
"""
        spec, format = load_openapi_spec(content)

        assert spec["openapi"] == "3.0.0"
        assert spec["info"]["title"] == "Test"
        assert format == OutputFormat.YAML

    def test_load_with_format_hint(self):
        """Test loading with format hint."""
        yaml_content = "openapi: 3.0.0"

        # Force JSON parsing (should fail)
        with pytest.raises(ValueError, match="Invalid JSON format"):
            load_openapi_spec(yaml_content, OutputFormat.JSON)

    def test_load_invalid_content(self):
        """Test loading invalid content."""
        # Use invalid YAML that will fail parsing
        with pytest.raises(ValueError, match="Unable to parse|Invalid"):
            load_openapi_spec(":\n  - invalid\nyaml")


class TestApplyRules:
    """Test applying rules to OpenAPI specs."""

    def test_delete_operations_with_security(self):
        """Test deleting operations based on security."""
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {"security": [{"api_key": []}]},
                    "post": {"security": [{"auth": []}]},
                },
                "/health": {"get": {"summary": "Health check"}},
            },
        }

        rule = Rule("path/method : delete : resource.security is not None and resource.security != 'auth'")
        result = apply_rules(spec, [rule])

        # /users/get should be deleted (has api_key security)
        assert "/users" in result["paths"]  # Path still exists
        assert "get" not in result["paths"]["/users"]
        # /users/post should remain (has auth security)
        assert "post" in result["paths"]["/users"]
        # /health/get should remain (no security)
        assert "get" in result["paths"]["/health"]

    def test_remove_empty_paths(self):
        """Test that empty paths are removed."""
        spec = {"openapi": "3.0.0", "paths": {"/users": {"get": {"security": [{"api_key": []}]}}}}

        rule = Rule("path/method : delete : resource.security is not None")
        result = apply_rules(spec, [rule])

        # Path should be removed entirely
        assert "/users" not in result["paths"]

    def test_original_spec_unchanged(self):
        """Test that original spec is not modified."""
        spec = {"paths": {"/users": {"get": {"security": [{"api_key": []}]}}}}

        rule = Rule("path/method : delete : resource.security is not None")
        result = apply_rules(spec, [rule])

        # Original should still have the operation
        assert "get" in spec["paths"]["/users"]
        # Result should not
        assert "/users" not in result["paths"]


class TestProcessOpenAPI:
    """Test the main process_openapi function."""

    def test_process_yaml_to_yaml(self):
        """Test processing YAML spec with YAML output."""
        input_yaml = """openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /do-not-delete:
    get:
      summary: Test operation
  /do-not-delete-as-well:
    get:
      summary: Test operation
      security:
        - auth: []
  /delete-me:
    get:
      summary: Test operation
      security:
        - api_key: []
"""

        result = process_openapi(
            input_yaml,
            ["path/method : delete : resource.security is not None and resource.security != 'auth'"],
        )

        # Parse result
        result_spec = yaml.safe_load(result)

        assert "/do-not-delete" in result_spec["paths"]
        assert "/do-not-delete-as-well" in result_spec["paths"]
        assert "/delete-me" not in result_spec["paths"]

    def test_process_json_to_json(self):
        """Test processing JSON spec with JSON output."""
        input_json = json.dumps({"openapi": "3.0.0", "paths": {"/users": {"get": {"security": [{"oauth2": []}]}}}})

        result = process_openapi(input_json, ["path/method : delete : resource.security is not None"], output_format=OutputFormat.JSON)

        # Parse result
        result_spec = json.loads(result)

        assert "/users" not in result_spec["paths"]

    def test_process_multiple_rules(self):
        """Test processing with multiple rules."""
        input_yaml = """openapi: 3.0.0
paths:
  /public:
    get:
      summary: Public endpoint
  /private:
    get:
      summary: Private endpoint
      security:
        - api_key: []
  /auth:
    get:
      summary: Auth endpoint
      security:
        - auth: []
"""

        # Apply two rules
        result = process_openapi(
            input_yaml,
            ["path/method : delete : resource.security is not None and resource.security != 'auth'", "path/method : delete : path == '/public'"],
        )

        result_spec = yaml.safe_load(result)

        # Only /auth should remain
        assert "/public" not in result_spec["paths"]
        assert "/private" not in result_spec["paths"]
        assert "/auth" in result_spec["paths"]
