"""Tests for OpenAPI CLI commands."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from aws_sam_tools.cli import cli


class TestOpenAPICLI:
    """Test OpenAPI CLI functionality."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    @pytest.fixture
    def sample_openapi_yaml(self):
        """Sample OpenAPI YAML content."""
        return """openapi: 3.0.0
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

    @pytest.fixture
    def sample_openapi_json(self):
        """Sample OpenAPI JSON content."""
        return json.dumps(
            {
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {"/users": {"get": {"summary": "Get users", "security": [{"oauth2": []}]}, "post": {"summary": "Create user"}}},
            },
            indent=2,
        )

    def test_openapi_process_help(self, runner):
        """Test openapi process help."""
        result = runner.invoke(cli, ["openapi", "process", "--help"])
        assert result.exit_code == 0
        assert "Process OpenAPI specification with rules" in result.output
        assert "--rule" in result.output
        assert "--input" in result.output
        assert "--output" in result.output
        assert "--format" in result.output

    def test_process_with_stdin_stdout(self, runner, sample_openapi_yaml):
        """Test processing from stdin to stdout."""
        rule = "path/method : delete : resource.security is not None and resource.security != 'auth'"

        result = runner.invoke(cli, ["openapi", "process", "--rule", rule], input=sample_openapi_yaml)

        assert result.exit_code == 0

        # Parse output
        output_spec = yaml.safe_load(result.output)
        assert "/do-not-delete" in output_spec["paths"]
        assert "/do-not-delete-as-well" in output_spec["paths"]
        assert "/delete-me" not in output_spec["paths"]

    def test_process_with_file_input(self, runner, sample_openapi_yaml):
        """Test processing from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(sample_openapi_yaml)
            input_file = f.name

        try:
            rule = "path/method : delete : resource.security is not None"

            result = runner.invoke(cli, ["openapi", "process", "--rule", rule, "--input", input_file])

            assert result.exit_code == 0
            output_spec = yaml.safe_load(result.output)

            # All operations with security should be deleted
            # /do-not-delete has no security, so it should remain
            assert "/do-not-delete" in output_spec["paths"]
            # Both other paths have operations with security, so they should be deleted
            assert len(output_spec["paths"]) == 1
        finally:
            Path(input_file).unlink()

    def test_process_with_file_output(self, runner, sample_openapi_yaml):
        """Test processing to file."""
        with tempfile.NamedTemporaryFile(delete=False) as output_file:
            output_path = output_file.name

        try:
            rule = "path/method : delete : resource.security is not None"

            result = runner.invoke(cli, ["openapi", "process", "--rule", rule, "--output", output_path], input=sample_openapi_yaml)

            assert result.exit_code == 0
            assert f"Processed specification written to: {output_path}" in result.output

            # Check output file
            with open(output_path) as f:
                output_spec = yaml.safe_load(f)
                # /do-not-delete has no security, so it should remain
                assert "/do-not-delete" in output_spec["paths"]
                assert len(output_spec["paths"]) == 1
        finally:
            Path(output_path).unlink()

    def test_process_json_format(self, runner, sample_openapi_json):
        """Test processing JSON with explicit format."""
        rule = "path/method : delete : resource.security is not None"

        result = runner.invoke(cli, ["openapi", "process", "--rule", rule, "--format", "json"], input=sample_openapi_json)

        assert result.exit_code == 0

        # Output should be valid JSON
        output_spec = json.loads(result.output)
        # Only the get operation has security, so it should be deleted
        assert "/users" in output_spec["paths"]
        assert "post" in output_spec["paths"]["/users"]
        assert "get" not in output_spec["paths"]["/users"]

    def test_process_yaml_to_json(self, runner, sample_openapi_yaml):
        """Test converting YAML to JSON."""
        result = runner.invoke(cli, ["openapi", "process", "--format", "json"], input=sample_openapi_yaml)

        assert result.exit_code == 0

        # Output should be valid JSON
        output_spec = json.loads(result.output)
        assert output_spec["openapi"] == "3.0.0"
        assert output_spec["info"]["title"] == "Test API"

    def test_process_multiple_rules(self, runner, sample_openapi_yaml):
        """Test applying multiple rules."""
        result = runner.invoke(
            cli, ["openapi", "process", "--rule", "path/method : delete : resource.security is not None", "--rule", "path/method : delete : path == '/do-not-delete'"], input=sample_openapi_yaml
        )

        assert result.exit_code == 0

        # Only empty paths should remain
        output_spec = yaml.safe_load(result.output)
        assert output_spec["paths"] == {}

    def test_process_invalid_rule(self, runner, sample_openapi_yaml):
        """Test with invalid rule format."""
        result = runner.invoke(cli, ["openapi", "process", "--rule", "invalid rule"], input=sample_openapi_yaml)

        assert result.exit_code == 1
        assert "Invalid rule format" in result.output

    def test_process_invalid_input_file(self, runner):
        """Test with non-existent input file."""
        result = runner.invoke(cli, ["openapi", "process", "--input", "nonexistent.yaml"])

        assert result.exit_code == 1
        assert "Input file not found" in result.output

    def test_process_invalid_yaml(self, runner):
        """Test with invalid YAML input."""
        invalid_yaml = "invalid: yaml: content: {"

        result = runner.invoke(cli, ["openapi", "process", "--format", "yaml"], input=invalid_yaml)

        assert result.exit_code == 1
        assert "Unable to parse" in result.output or "Invalid" in result.output

    def test_format_auto_detection(self, runner):
        """Test automatic format detection from file extension."""
        # Create YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\n")
            yaml_file = f.name

        # Create JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0.0"}}, f)
            json_file = f.name

        try:
            # Test YAML detection
            result = runner.invoke(cli, ["openapi", "process", "--input", yaml_file])
            assert result.exit_code == 0
            # Output should be YAML
            yaml.safe_load(result.output)  # Should not raise

            # Test JSON detection
            result = runner.invoke(cli, ["openapi", "process", "--input", json_file])
            assert result.exit_code == 0
            # Output should be JSON
            json.loads(result.output)  # Should not raise
        finally:
            Path(yaml_file).unlink()
            Path(json_file).unlink()
