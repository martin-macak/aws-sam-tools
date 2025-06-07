import json
from pathlib import Path

import pytest
import yaml

from cfn_tools.cfn_processing import (
    load_yaml,
    load_yaml_file,
)


class TestCFNToolsIncludeFile:
    """Test cases for !CFNToolsIncludeFile tag."""

    def test_include_yaml_file(self, tmp_path: Path) -> None:
        """Test including a YAML file."""
        # Create test YAML file to include
        include_file = tmp_path / "openapi.yaml"
        include_content = """openapi: 3.0.0
info:
  title: My API
  version: 1.0.0"""
        include_file.write_text(include_content)

        # Create main YAML file
        main_file = tmp_path / "template.yaml"
        main_content = f"""MyStack:
  Def: !CFNToolsIncludeFile openapi.yaml"""
        main_file.write_text(main_content)

        # Load and verify
        result = load_yaml_file(str(main_file))
        expected = {
            "MyStack": {
                "Def": {
                    "openapi": "3.0.0",
                    "info": {"title": "My API", "version": "1.0.0"},
                }
            }
        }
        assert result == expected

    def test_include_json_file(self, tmp_path: Path) -> None:
        """Test including a JSON file."""
        # Create test JSON file to include
        include_file = tmp_path / "openapi.json"
        include_content = {
            "openapi": "3.0.0",
            "info": {"title": "My API", "version": "1.0.0"},
        }
        include_file.write_text(json.dumps(include_content))

        # Create main YAML file
        main_file = tmp_path / "template.yaml"
        main_content = f"""MyStack:
  Def: !CFNToolsIncludeFile openapi.json"""
        main_file.write_text(main_content)

        # Load and verify
        result = load_yaml_file(str(main_file))
        expected = {
            "MyStack": {
                "Def": {
                    "openapi": "3.0.0",
                    "info": {"title": "My API", "version": "1.0.0"},
                }
            }
        }
        assert result == expected

    def test_include_text_file(self, tmp_path: Path) -> None:
        """Test including a text file."""
        # Create test text file to include
        include_file = tmp_path / "README.txt"
        include_content = "Hello, World!"
        include_file.write_text(include_content)

        # Create main YAML file
        main_file = tmp_path / "template.yaml"
        main_content = f"""MyStack:
  Def: !CFNToolsIncludeFile README.txt"""
        main_file.write_text(main_content)

        # Load and verify
        result = load_yaml_file(str(main_file))
        expected = {"MyStack": {"Def": "Hello, World!"}}
        assert result == expected

    def test_relative_path(self, tmp_path: Path) -> None:
        """Test including file with relative path."""
        # Create subdirectory
        subdir = tmp_path / "src" / "api"
        subdir.mkdir(parents=True)

        # Create test YAML file to include
        include_file = subdir / "openapi.yaml"
        include_content = """openapi: 3.0.0
info:
  title: My API
  version: 1.0.0"""
        include_file.write_text(include_content)

        # Create main YAML file
        main_file = tmp_path / "template.yaml"
        main_content = f"""MyStack:
  Def: !CFNToolsIncludeFile src/api/openapi.yaml"""
        main_file.write_text(main_content)

        # Load and verify
        result = load_yaml_file(str(main_file))
        expected = {
            "MyStack": {
                "Def": {
                    "openapi": "3.0.0",
                    "info": {"title": "My API", "version": "1.0.0"},
                }
            }
        }
        assert result == expected

    def test_absolute_path(self, tmp_path: Path) -> None:
        """Test including file with absolute path."""
        # Create test YAML file to include
        include_file = tmp_path / "openapi.yaml"
        include_content = """openapi: 3.0.0
info:
  title: My API
  version: 1.0.0"""
        include_file.write_text(include_content)

        # Create main YAML file with absolute path
        main_file = tmp_path / "template.yaml"
        main_content = f"""MyStack:
  Def: !CFNToolsIncludeFile {str(include_file)}"""
        main_file.write_text(main_content)

        # Load and verify
        result = load_yaml_file(str(main_file))
        expected = {
            "MyStack": {
                "Def": {
                    "openapi": "3.0.0",
                    "info": {"title": "My API", "version": "1.0.0"},
                }
            }
        }
        assert result == expected

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Test error when included file not found."""
        # Create main YAML file
        main_file = tmp_path / "template.yaml"
        main_content = """MyStack:
  Def: !CFNToolsIncludeFile nonexistent.yaml"""
        main_file.write_text(main_content)

        # Load and expect error
        with pytest.raises(yaml.constructor.ConstructorError, match="file not found"):
            load_yaml_file(str(main_file))

    def test_invalid_node_type(self) -> None:
        """Test error when tag is used with non-scalar node."""
        yaml_content = """MyStack:
  Def: !CFNToolsIncludeFile [not, a, scalar]"""

        with pytest.raises(yaml.constructor.ConstructorError, match="expected a scalar node"):
            load_yaml(yaml_content)

    def test_empty_file_path(self) -> None:
        """Test error when file path is empty."""
        yaml_content = """MyStack:
  Def: !CFNToolsIncludeFile"""

        with pytest.raises(yaml.constructor.ConstructorError, match="must specify a file path"):
            load_yaml(yaml_content)

    def test_nested_cloudformation_tags(self, tmp_path: Path) -> None:
        """Test including YAML file with CloudFormation tags."""
        # Create test YAML file with CloudFormation tags
        include_file = tmp_path / "resources.yaml"
        include_content = """Type: AWS::S3::Bucket
Properties:
  BucketName: !Ref BucketNameParam
  Tags:
    - Key: Environment
      Value: !Sub ${Environment}-bucket"""
        include_file.write_text(include_content)

        # Create main YAML file
        main_file = tmp_path / "template.yaml"
        main_content = f"""Resources:
  S3Bucket: !CFNToolsIncludeFile resources.yaml"""
        main_file.write_text(main_content)

        # Load and verify CloudFormation tags are preserved
        result = load_yaml_file(str(main_file))
        assert result["Resources"]["S3Bucket"]["Type"] == "AWS::S3::Bucket"
        assert hasattr(result["Resources"]["S3Bucket"]["Properties"]["BucketName"], "value")
        assert hasattr(result["Resources"]["S3Bucket"]["Properties"]["Tags"][0]["Value"], "value")


class TestCFNToolsToString:
    """Test cases for !CFNToolsToString tag."""

    def test_simple_string(self) -> None:
        """Test converting simple string."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ "Hello, World!" ]"""

        result = load_yaml(yaml_content)
        assert result == {"MyStack": {"Def": "Hello, World!"}}

    def test_dict_to_yaml_string(self) -> None:
        """Test converting dict to YAML string."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ { "name": "John", "age": 30 }, { ConvertTo: "YAMLString" } ]"""

        result = load_yaml(yaml_content)
        expected_yaml = "name: John\nage: 30"
        assert result == {"MyStack": {"Def": expected_yaml}}

    def test_dict_to_json_string(self) -> None:
        """Test converting dict to JSON string."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ { "name": "John", "age": 30 }, { ConvertTo: "JSONString" } ]"""

        result = load_yaml(yaml_content)
        expected_json = '{\n  "name": "John",\n  "age": 30\n}'
        assert result == {"MyStack": {"Def": expected_json}}

    def test_dict_to_json_string_one_line(self) -> None:
        """Test converting dict to single-line JSON string."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ { "name": "John", "age": 30 }, { ConvertTo: "JSONString", OneLine: true } ]"""

        result = load_yaml(yaml_content)
        expected_json = '{"name":"John","age":30}'
        assert result == {"MyStack": {"Def": expected_json}}

    def test_string_with_newlines_one_line(self) -> None:
        """Test converting string with newlines to single line."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ "Hello\nWorld!", { OneLine: true } ]"""

        result = load_yaml(yaml_content)
        assert result == {"MyStack": {"Def": "Hello World!"}}

    def test_list_to_json_string(self) -> None:
        """Test converting list to JSON string."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ [ "a", "b", "c" ], { ConvertTo: "JSONString" } ]"""

        result = load_yaml(yaml_content)
        expected_json = '[\n  "a",\n  "b",\n  "c"\n]'
        assert result == {"MyStack": {"Def": expected_json}}

    def test_number_to_string(self) -> None:
        """Test converting number to string."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ 42 ]"""

        result = load_yaml(yaml_content)
        assert result == {"MyStack": {"Def": "42"}}

    def test_boolean_to_string(self) -> None:
        """Test converting boolean to string."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ true ]"""

        result = load_yaml(yaml_content)
        assert result == {"MyStack": {"Def": "True"}}

    def test_default_convert_to_json(self) -> None:
        """Test default ConvertTo is JSONString."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ { "key": "value" } ]"""

        result = load_yaml(yaml_content)
        expected_json = '{\n  "key": "value"\n}'
        assert result == {"MyStack": {"Def": expected_json}}

    def test_invalid_node_type(self) -> None:
        """Test error when tag is used with non-sequence node."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString "not a sequence" """

        with pytest.raises(yaml.constructor.ConstructorError, match="expected a sequence node"):
            load_yaml(yaml_content)

    def test_empty_sequence(self) -> None:
        """Test error when sequence is empty."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString []"""

        with pytest.raises(yaml.constructor.ConstructorError, match="requires at least one parameter"):
            load_yaml(yaml_content)

    def test_invalid_convert_to(self) -> None:
        """Test error when ConvertTo has invalid value."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ "test", { ConvertTo: "XMLString" } ]"""

        with pytest.raises(yaml.constructor.ConstructorError, match='must be "YAMLString" or "JSONString"'):
            load_yaml(yaml_content)

    def test_invalid_options_type(self) -> None:
        """Test error when options is not a mapping."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ "test", "not a mapping" ]"""

        with pytest.raises(yaml.constructor.ConstructorError, match="optional parameters must be a mapping"):
            load_yaml(yaml_content)

    def test_invalid_one_line_type(self) -> None:
        """Test error when OneLine is not boolean."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ "test", { OneLine: "yes" } ]"""

        with pytest.raises(yaml.constructor.ConstructorError, match="OneLine must be a boolean"):
            load_yaml(yaml_content)

    def test_complex_nested_structure(self) -> None:
        """Test converting complex nested structure."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString
    - users:
        - name: John
          roles: [admin, user]
        - name: Jane
          roles: [user]
    - ConvertTo: YAMLString"""

        result = load_yaml(yaml_content)
        # The exact formatting might vary slightly, so check the key parts
        assert "users:" in result["MyStack"]["Def"]
        assert "name: John" in result["MyStack"]["Def"]
        assert "roles:" in result["MyStack"]["Def"]

    def test_unicode_handling(self) -> None:
        """Test handling of Unicode characters."""
        yaml_content = """MyStack:
  Def: !CFNToolsToString [ { "message": "Hello 世界! 🌍" }, { ConvertTo: "JSONString" } ]"""

        result = load_yaml(yaml_content)
        # Should preserve Unicode without escaping
        assert '"message": "Hello 世界! 🌍"' in result["MyStack"]["Def"]


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_include_and_to_string(self, tmp_path: Path) -> None:
        """Test using both tags together."""
        # Create test YAML file to include
        include_file = tmp_path / "config.yaml"
        include_content = """database:
  host: localhost
  port: 5432
  name: mydb"""
        include_file.write_text(include_content)

        # Create main YAML file that includes and converts to string
        main_file = tmp_path / "template.yaml"
        main_content = f"""Parameters:
  ConfigData:
    Type: String
    Default: !CFNToolsToString
      - !CFNToolsIncludeFile config.yaml
      - ConvertTo: JSONString
        OneLine: true"""
        main_file.write_text(main_content)

        # Load and verify
        result = load_yaml_file(str(main_file))
        config_str = result["Parameters"]["ConfigData"]["Default"]
        # Parse back to verify it's valid JSON
        config_data = json.loads(config_str)
        assert config_data == {"database": {"host": "localhost", "port": 5432, "name": "mydb"}}

    def test_cloudformation_tags_preserved(self) -> None:
        """Test that CloudFormation tags still work alongside new tags."""
        yaml_content = """Resources:
  Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketNameParam
      Policy: !CFNToolsToString
        - Statement:
            - Effect: Allow
              Principal: !Sub "arn:aws:iam::${AWS::AccountId}:root"
              Action: s3:*
        - ConvertTo: JSONString"""

        result = load_yaml(yaml_content)
        # Check CloudFormation tags are preserved
        assert hasattr(result["Resources"]["Bucket"]["Properties"]["BucketName"], "value")
        # Check new tag worked
        assert isinstance(result["Resources"]["Bucket"]["Properties"]["Policy"], str)
        assert "Statement" in result["Resources"]["Bucket"]["Properties"]["Policy"]
