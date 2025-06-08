"""Tests for the CLI module."""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from aws_sam_tools.cli import cli


class TestCLI:
    """Test cases for the CLI."""

    def test_cli_no_command_shows_error(self) -> None:
        """Test that running cli without command shows error."""
        runner = CliRunner()
        result = runner.invoke(cli, [])

        assert result.exit_code == 2
        assert "Usage:" in result.output

    def test_template_no_subcommand_shows_error(self) -> None:
        """Test that running template without subcommand shows error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["template"])

        assert result.exit_code == 2
        assert "Usage:" in result.output

    def test_template_process_command_default_template(self, tmp_path: Path) -> None:
        """Test template process command with default template.yaml."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create default template.yaml
            template_content = """Description: Test template
Resources:
  Bucket:
    Type: AWS::S3::Bucket"""
            Path("template.yaml").write_text(template_content)

            result = runner.invoke(cli, ["template", "process"])

        assert result.exit_code == 0
        assert "Description: Test template" in result.output

    def test_template_process_command_with_cfntools_tags(self, tmp_path: Path) -> None:
        """Test template process command with CFNTools tags."""
        # Create a test template with CFNTools tags
        template_file = tmp_path / "template.yaml"
        template_content = """Parameters:
  Id:
    Type: String
    Default: !CFNToolsUUID
  Version:
    Type: String  
    Default: !CFNToolsVersion"""
        template_file.write_text(template_content)

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--template", str(template_file)])

        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)

        # Check UUID was generated (36 chars with dashes)
        uuid_value = output_data["Parameters"]["Id"]["Default"]
        assert len(uuid_value) == 36
        assert uuid_value.count("-") == 4

        # Check version was generated
        version_value = output_data["Parameters"]["Version"]["Default"]
        assert version_value  # Should have some version string

    def test_template_process_command_with_output_file(self, tmp_path: Path) -> None:
        """Test template process command with output file."""
        template_file = tmp_path / "template.yaml"
        output_file = tmp_path / "output.yaml"

        template_content = """Resources:
  Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !CFNToolsToString [ "my-bucket" ]"""
        template_file.write_text(template_content)

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--template", str(template_file), "--output", str(output_file)])

        assert result.exit_code == 0
        assert f"Processed template written to: {output_file}" in result.output

        # Check output file was created
        assert output_file.exists()
        output_data = yaml.safe_load(output_file.read_text())
        assert output_data["Resources"]["Bucket"]["Properties"]["BucketName"] == "my-bucket"

    def test_template_process_command_template_not_found(self) -> None:
        """Test template process command when template file doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--template", "nonexistent.yaml"])

        assert result.exit_code == 1
        assert "Error: Template file not found" in result.output

    def test_template_process_command_invalid_yaml(self, tmp_path: Path) -> None:
        """Test template process command with invalid YAML."""
        template_file = tmp_path / "invalid.yaml"
        template_content = """Resources:
  Bucket:
    Type: AWS::S3::Bucket
    Properties:
      - invalid yaml structure
      BucketName: test"""
        template_file.write_text(template_content)

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--template", str(template_file)])

        assert result.exit_code == 1
        assert "Error: Failed to parse YAML" in result.output

    def test_template_process_command_cfntools_error(self, tmp_path: Path) -> None:
        """Test template process command when CFNTools tag has error."""
        template_file = tmp_path / "template.yaml"
        template_content = """Resources:
  Test:
    Properties:
      File: !CFNToolsIncludeFile nonexistent-file.yaml"""
        template_file.write_text(template_content)

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--template", str(template_file)])

        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_cli_help(self) -> None:
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "AWS SAM Tools" in result.output
        assert "Process CloudFormation templates" in result.output

    def test_template_help(self) -> None:
        """Test template command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["template", "--help"])

        assert result.exit_code == 0
        assert "Commands for working with CloudFormation templates" in result.output
        assert "process" in result.output

    def test_template_process_help(self) -> None:
        """Test template process subcommand help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--help"])

        assert result.exit_code == 0
        assert "Process all CFNTools tags" in result.output
        assert "--template" in result.output
        assert "--output" in result.output

    def test_template_process_with_included_file(self, tmp_path: Path) -> None:
        """Test template process command with file inclusion."""
        # Create included file
        include_file = tmp_path / "config.yaml"
        include_content = """database:
  host: localhost
  port: 5432"""
        include_file.write_text(include_content)

        # Create template that includes the file
        template_file = tmp_path / "template.yaml"
        template_content = f"""Parameters:
  Config:
    Type: String
    Default: !CFNToolsToString
      - !CFNToolsIncludeFile config.yaml
      - ConvertTo: JSONString
        OneLine: true"""
        template_file.write_text(template_content)

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--template", str(template_file)])

        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        config_json = output_data["Parameters"]["Config"]["Default"]
        assert "localhost" in config_json
        assert "5432" in config_json

    @pytest.mark.parametrize("option", ["-t", "--template"])
    def test_template_option_aliases(self, tmp_path: Path, option: str) -> None:
        """Test both -t and --template options work."""
        template_file = tmp_path / "test.yaml"
        template_file.write_text("test: value")

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", option, str(template_file)])

        assert result.exit_code == 0
        assert "test: value" in result.output

    @pytest.mark.parametrize("option", ["-o", "--output"])
    def test_output_option_aliases(self, tmp_path: Path, option: str) -> None:
        """Test both -o and --output options work."""
        template_file = tmp_path / "test.yaml"
        output_file = tmp_path / "out.yaml"
        template_file.write_text("test: value")

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "-t", str(template_file), option, str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_invalid_command(self) -> None:
        """Test invalid command shows error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["invalid"])

        assert result.exit_code == 2  # Click's usage error
        assert "No such command" in result.output

    def test_invalid_template_subcommand(self) -> None:
        """Test invalid template subcommand shows error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["template", "invalid"])

        assert result.exit_code == 2  # Click's usage error
        assert "No such command" in result.output

    def test_template_process_with_replace_tags(self, tmp_path: Path) -> None:
        """Test template process command with --replace-tags option."""
        template_file = tmp_path / "template.yaml"
        template_content = """Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketParam
  MyFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-function'
      Role: !GetAtt LambdaRole.Arn"""
        template_file.write_text(template_content)

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--template", str(template_file), "--replace-tags"])

        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)

        # Check that tags were replaced with intrinsic functions
        assert output_data["Resources"]["MyBucket"]["Properties"]["BucketName"] == {"Ref": "BucketParam"}
        assert output_data["Resources"]["MyFunction"]["Properties"]["FunctionName"] == {"Fn::Sub": "${AWS::StackName}-function"}
        assert output_data["Resources"]["MyFunction"]["Properties"]["Role"] == {"Fn::GetAtt": ["LambdaRole", "Arn"]}

    def test_template_process_without_replace_tags(self, tmp_path: Path) -> None:
        """Test that tags are preserved when --replace-tags is not specified."""
        template_file = tmp_path / "template.yaml"
        template_content = """Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketParam"""
        template_file.write_text(template_content)

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--template", str(template_file)])

        assert result.exit_code == 0
        # When not using --replace-tags, the YAML dumper will convert tags to their string representation
        # The exact output depends on how PyYAML handles custom tags
        assert "BucketParam" in result.output

    def test_template_process_replace_tags_with_cfntools_tags(self, tmp_path: Path) -> None:
        """Test that --replace-tags works with both CloudFormation and CFNTools tags."""
        template_file = tmp_path / "template.yaml"
        template_content = """Parameters:
  BucketName:
    Type: String
    Default: !CFNToolsToString
      - !Ref AWS::StackName
      - ConvertTo: JSONString
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketName"""
        template_file.write_text(template_content)

        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--template", str(template_file), "--replace-tags"])

        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)

        # Check that CloudFormation tags were replaced
        assert output_data["Resources"]["MyBucket"]["Properties"]["BucketName"] == {"Ref": "BucketName"}
        # CFNTools tags should be processed to their values
        assert isinstance(output_data["Parameters"]["BucketName"]["Default"], str)

    def test_template_process_help_shows_replace_tags(self) -> None:
        """Test that --replace-tags option is shown in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["template", "process", "--help"])

        assert result.exit_code == 0
        assert "--replace-tags" in result.output
        assert "Replace CloudFormation tags with intrinsic functions" in result.output
