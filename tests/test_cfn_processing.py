"""Tests for the cfn_processing module."""

import json
from pathlib import Path

import pytest
import yaml

from aws_sam_tools.cfn_processing import (
    load_yaml,
    load_yaml_file,
    process_yaml_template,
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
        main_content = """MyStack:
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
        main_content = """MyStack:
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
        main_content = """MyStack:
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
        main_content = """MyStack:
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
        main_content = """Resources:
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


class TestCFNToolsUUID:
    """Test cases for !CFNToolsUUID tag."""

    def test_generate_uuid(self) -> None:
        """Test generating a UUID."""
        yaml_content = """MyStack:
  Id: !CFNToolsUUID"""

        result = load_yaml(yaml_content)
        uuid_str = result["MyStack"]["Id"]

        # Check it's a valid UUID format (36 chars with hyphens in right places)
        assert len(uuid_str) == 36
        assert uuid_str[8] == "-"
        assert uuid_str[13] == "-"
        assert uuid_str[18] == "-"
        assert uuid_str[23] == "-"

        # Verify it's a valid UUID by trying to parse it
        import uuid

        uuid.UUID(uuid_str)  # Will raise if invalid

    def test_multiple_uuids_are_different(self) -> None:
        """Test that multiple UUID tags generate different values."""
        yaml_content = """MyStack:
  Id1: !CFNToolsUUID
  Id2: !CFNToolsUUID"""

        result = load_yaml(yaml_content)
        assert result["MyStack"]["Id1"] != result["MyStack"]["Id2"]

    def test_invalid_with_arguments(self) -> None:
        """Test error when UUID tag has arguments."""
        yaml_content = """MyStack:
  Id: !CFNToolsUUID some-arg"""

        with pytest.raises(yaml.constructor.ConstructorError, match="takes no arguments"):
            load_yaml(yaml_content)


class TestCFNToolsVersion:
    """Test cases for !CFNToolsVersion tag."""

    def test_default_version(self, monkeypatch) -> None:
        """Test generating version with defaults."""
        # Mock dunamai to return a known version
        from unittest.mock import Mock

        mock_version = Mock()
        mock_version.serialize.return_value = "1.0.0-dev.1+123e4567"

        def mock_get_version(source):
            return mock_version

        monkeypatch.setattr("aws_sam_tools.cfn_processing.get_version", mock_get_version)

        yaml_content = """MyStack:
  Version: !CFNToolsVersion"""

        result = load_yaml(yaml_content)
        assert result["MyStack"]["Version"] == "1.0.0-dev.1+123e4567"
        mock_version.serialize.assert_called_once()

    def test_version_with_pep440_style(self, monkeypatch) -> None:
        """Test generating version with pep440 style."""
        from unittest.mock import Mock

        from dunamai import Style

        mock_version = Mock()
        mock_version.serialize.return_value = "1.0.0.dev1+123e4567"

        def mock_get_version(source):
            return mock_version

        monkeypatch.setattr("aws_sam_tools.cfn_processing.get_version", mock_get_version)

        yaml_content = """MyStack:
  Version: !CFNToolsVersion { Style: pep440 }"""

        result = load_yaml(yaml_content)
        assert result["MyStack"]["Version"] == "1.0.0.dev1+123e4567"
        mock_version.serialize.assert_called_once_with(style=Style.Pep440)

    def test_version_with_any_source(self, monkeypatch) -> None:
        """Test generating version with Any source."""
        from unittest.mock import Mock

        mock_version = Mock()
        mock_version.serialize.return_value = "2.0.0"

        mock_get_version = Mock(return_value=mock_version)
        monkeypatch.setattr("aws_sam_tools.cfn_processing.get_version", mock_get_version)

        yaml_content = """MyStack:
  Version: !CFNToolsVersion { Source: Any }"""

        result = load_yaml(yaml_content)
        assert result["MyStack"]["Version"] == "2.0.0"
        mock_get_version.assert_called_once_with("any")

    def test_version_fallback_no_dunamai(self, monkeypatch) -> None:
        """Test fallback when dunamai is not available."""
        monkeypatch.setattr("aws_sam_tools.cfn_processing.get_version", None)

        yaml_content = """MyStack:
  Version: !CFNToolsVersion"""

        result = load_yaml(yaml_content)
        assert result["MyStack"]["Version"] == "0.0.0-dev"

    def test_version_fallback_on_error(self, monkeypatch) -> None:
        """Test fallback when version detection fails."""

        def mock_get_version(source):
            raise Exception("Git not found")

        monkeypatch.setattr("aws_sam_tools.cfn_processing.get_version", mock_get_version)

        yaml_content = """MyStack:
  Version: !CFNToolsVersion"""

        result = load_yaml(yaml_content)
        assert result["MyStack"]["Version"] == "0.0.0-dev"

    def test_invalid_source(self) -> None:
        """Test error with invalid source."""
        yaml_content = """MyStack:
  Version: !CFNToolsVersion { Source: SVN }"""

        with pytest.raises(yaml.constructor.ConstructorError, match='Source must be "Git" or "Any"'):
            load_yaml(yaml_content)

    def test_invalid_style(self) -> None:
        """Test error with invalid style."""
        yaml_content = """MyStack:
  Version: !CFNToolsVersion { Style: custom }"""

        with pytest.raises(yaml.constructor.ConstructorError, match='Style must be "semver" or "pep440"'):
            load_yaml(yaml_content)


class TestCFNToolsTimestamp:
    """Test cases for !CFNToolsTimestamp tag."""

    def test_default_timestamp(self) -> None:
        """Test generating timestamp with defaults (ISO-8601)."""
        yaml_content = """MyStack:
  Timestamp: !CFNToolsTimestamp"""

        result = load_yaml(yaml_content)
        timestamp = result["MyStack"]["Timestamp"]

        # Check ISO-8601 format with Z suffix
        assert timestamp.endswith("Z")
        assert len(timestamp) == 20  # YYYY-MM-DDTHH:MM:SSZ
        assert timestamp[10] == "T"

        # Verify it can be parsed
        from datetime import datetime

        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_custom_format(self) -> None:
        """Test timestamp with custom format."""
        yaml_content = """MyStack:
  Timestamp: !CFNToolsTimestamp { Format: "%Y-%m-%d %H:%M:%S" }"""

        result = load_yaml(yaml_content)
        timestamp = result["MyStack"]["Timestamp"]

        # Check format YYYY-MM-DD HH:MM:SS
        assert len(timestamp) == 19
        assert timestamp[4] == "-"
        assert timestamp[7] == "-"
        assert timestamp[10] == " "
        assert timestamp[13] == ":"
        assert timestamp[16] == ":"

    def test_timestamp_with_offset(self, monkeypatch) -> None:
        """Test timestamp with offset."""
        # Mock datetime to have a fixed time
        from datetime import datetime, timezone

        fixed_time = datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        class MockDatetime:
            @staticmethod
            def now(tz):
                return fixed_time

        monkeypatch.setattr("aws_sam_tools.cfn_processing.datetime", MockDatetime)

        yaml_content = """MyStack:
  Timestamp: !CFNToolsTimestamp { Offset: 1, OffsetUnit: minutes }"""

        result = load_yaml(yaml_content)
        assert result["MyStack"]["Timestamp"] == "2021-01-01T00:01:00Z"

    def test_timestamp_with_various_offsets(self, monkeypatch) -> None:
        """Test timestamp with different offset units."""
        from datetime import datetime, timezone

        fixed_time = datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        class MockDatetime:
            @staticmethod
            def now(tz):
                return fixed_time

        monkeypatch.setattr("aws_sam_tools.cfn_processing.datetime", MockDatetime)

        # Test hours offset
        yaml_content = """MyStack:
  Hour: !CFNToolsTimestamp { Offset: 2, OffsetUnit: hours }
  Day: !CFNToolsTimestamp { Offset: 1, OffsetUnit: days }
  Week: !CFNToolsTimestamp { Offset: 1, OffsetUnit: weeks }"""

        result = load_yaml(yaml_content)
        assert result["MyStack"]["Hour"] == "2021-01-01T02:00:00Z"
        assert result["MyStack"]["Day"] == "2021-01-02T00:00:00Z"
        assert result["MyStack"]["Week"] == "2021-01-08T00:00:00Z"

    def test_invalid_format_type(self) -> None:
        """Test error when Format is not a string."""
        yaml_content = """MyStack:
  Timestamp: !CFNToolsTimestamp { Format: 123 }"""

        with pytest.raises(yaml.constructor.ConstructorError, match="Format must be a string"):
            load_yaml(yaml_content)

    def test_invalid_offset_type(self) -> None:
        """Test error when Offset is not an integer."""
        yaml_content = """MyStack:
  Timestamp: !CFNToolsTimestamp { Offset: "1" }"""

        with pytest.raises(yaml.constructor.ConstructorError, match="Offset must be an integer"):
            load_yaml(yaml_content)

    def test_invalid_offset_unit(self) -> None:
        """Test error with invalid offset unit."""
        yaml_content = """MyStack:
  Timestamp: !CFNToolsTimestamp { OffsetUnit: microseconds }"""

        with pytest.raises(yaml.constructor.ConstructorError, match="OffsetUnit must be one of"):
            load_yaml(yaml_content)


class TestCFNToolsCRC:
    """Test cases for !CFNToolsCRC tag."""

    def test_string_checksum_default(self) -> None:
        """Test checksum of a string with default settings (SHA256, hex)."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC [ "Hello, World!" ]"""

        result = load_yaml(yaml_content)
        # SHA256 of "Hello, World!" in hex
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert result["MyStack"]["CRC"] == expected

    def test_dict_checksum(self) -> None:
        """Test checksum of a dictionary."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC [ { "name": "John", "age": 30 } ]"""

        result = load_yaml(yaml_content)
        # Should create consistent JSON string and hash it
        assert len(result["MyStack"]["CRC"]) == 64  # SHA256 hex length

    def test_file_checksum(self, tmp_path: Path) -> None:
        """Test checksum of a file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        # Create YAML file
        main_file = tmp_path / "template.yaml"
        main_content = """MyStack:
  CRC: !CFNToolsCRC [ "file://test.txt" ]"""
        main_file.write_text(main_content)

        result = load_yaml_file(str(main_file))
        # SHA256 of "Test content"
        expected = "9d9595c5d94fb65b824f56e9999527dba9542481580d69feb89056aabaa0aa87"
        assert result["MyStack"]["CRC"] == expected

    def test_md5_algorithm(self) -> None:
        """Test checksum with MD5 algorithm."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC [ "Hello, World!", { Algorithm: md5 } ]"""

        result = load_yaml(yaml_content)
        # MD5 of "Hello, World!" in hex
        expected = "65a8e27d8879283831b664bd8b7f0ad4"
        assert result["MyStack"]["CRC"] == expected

    def test_base64_encoding(self) -> None:
        """Test checksum with base64 encoding."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC [ "Hello, World!", { Encoding: base64 } ]"""

        result = load_yaml(yaml_content)
        # SHA256 of "Hello, World!" in base64
        expected = "3/1gIbsr1bCvZ2KQgJ7DpTGR3YHH9wpLKGiKNiGCmG8="
        assert result["MyStack"]["CRC"] == expected

    def test_sha1_algorithm(self) -> None:
        """Test checksum with SHA1 algorithm."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC [ "Test", { Algorithm: sha1 } ]"""

        result = load_yaml(yaml_content)
        # SHA1 of "Test" in hex
        expected = "640ab2bae07bedc4c163f679a746f7ab7fb5d1fa"
        assert result["MyStack"]["CRC"] == expected

    def test_sha512_algorithm(self) -> None:
        """Test checksum with SHA512 algorithm."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC [ "Test", { Algorithm: sha512 } ]"""

        result = load_yaml(yaml_content)
        # SHA512 produces 128 character hex string
        assert len(result["MyStack"]["CRC"]) == 128

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Test error when file not found."""
        main_file = tmp_path / "template.yaml"
        main_content = """MyStack:
  CRC: !CFNToolsCRC [ "file://nonexistent.txt" ]"""
        main_file.write_text(main_content)

        with pytest.raises(yaml.constructor.ConstructorError, match="file not found"):
            load_yaml_file(str(main_file))

    def test_invalid_algorithm(self) -> None:
        """Test error with invalid algorithm."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC [ "test", { Algorithm: sha384 } ]"""

        with pytest.raises(yaml.constructor.ConstructorError, match="Algorithm must be one of"):
            load_yaml(yaml_content)

    def test_invalid_encoding(self) -> None:
        """Test error with invalid encoding."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC [ "test", { Encoding: base32 } ]"""

        with pytest.raises(yaml.constructor.ConstructorError, match='Encoding must be "hex" or "base64"'):
            load_yaml(yaml_content)

    def test_invalid_node_type(self) -> None:
        """Test error when tag is used with non-sequence node."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC "not a sequence" """

        with pytest.raises(yaml.constructor.ConstructorError, match="expected a sequence node"):
            load_yaml(yaml_content)

    def test_empty_sequence(self) -> None:
        """Test error when sequence is empty."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC []"""

        with pytest.raises(yaml.constructor.ConstructorError, match="requires at least one parameter"):
            load_yaml(yaml_content)

    def test_number_checksum(self) -> None:
        """Test checksum of a number."""
        yaml_content = """MyStack:
  CRC: !CFNToolsCRC [ 42 ]"""

        result = load_yaml(yaml_content)
        # SHA256 of "42"
        expected = "73475cb40a568e8da8a045ced110137e159f890ac4da883b6b17dc651b3a8049"
        assert result["MyStack"]["CRC"] == expected


class TestCloudFormationTagReplacement:
    """Test cases for CloudFormation tag replacement functionality."""

    def test_replace_ref_tag(self) -> None:
        """Test replacing !Ref tags with Ref intrinsic function."""
        yaml_content = """Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketParam"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Resources": {
                "MyBucket": {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {"BucketName": {"Ref": "BucketParam"}},
                }
            }
        }
        assert result == expected

    def test_replace_getatt_tag(self) -> None:
        """Test replacing !GetAtt tags with Fn::GetAtt intrinsic function."""
        yaml_content = """Outputs:
  BucketArn:
    Value: !GetAtt
      - MyBucket
      - Arn"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Outputs": {"BucketArn": {"Value": {"Fn::GetAtt": ["MyBucket", "Arn"]}}}}
        assert result == expected

    def test_replace_getatt_tag_dot_notation(self) -> None:
        """Test replacing !GetAtt tags with dot notation."""
        yaml_content = """Outputs:
  BucketArn:
    Value: !GetAtt MyBucket.Arn
  QueueArn:
    Value: !GetAtt MyQueue.Arn"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Outputs": {
                "BucketArn": {"Value": {"Fn::GetAtt": ["MyBucket", "Arn"]}},
                "QueueArn": {"Value": {"Fn::GetAtt": ["MyQueue", "Arn"]}},
            }
        }
        assert result == expected

    def test_replace_sub_tag(self) -> None:
        """Test replacing !Sub tags with Fn::Sub intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      Name: !Sub 'Hello ${AWS::Region}'"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"Name": {"Fn::Sub": "Hello ${AWS::Region}"}}}}}
        assert result == expected

    def test_replace_join_tag(self) -> None:
        """Test replacing !Join tags with Fn::Join intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      Value: !Join
        - '-'
        - - 'prefix'
          - !Ref Param
          - 'suffix'"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"Value": {"Fn::Join": ["-", ["prefix", {"Ref": "Param"}, "suffix"]]}}}}}
        assert result == expected

    def test_replace_select_tag(self) -> None:
        """Test replacing !Select tags with Fn::Select intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      Az: !Select
        - 0
        - !GetAZs ''"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"Az": {"Fn::Select": [0, {"Fn::GetAZs": ""}]}}}}}
        assert result == expected

    def test_replace_split_tag(self) -> None:
        """Test replacing !Split tags with Fn::Split intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      Items: !Split
        - ','
        - 'a,b,c'"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"Items": {"Fn::Split": [",", "a,b,c"]}}}}}
        assert result == expected

    def test_replace_getazs_tag(self) -> None:
        """Test replacing !GetAZs tags with Fn::GetAZs intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      AvailabilityZones: !GetAZs ''"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"AvailabilityZones": {"Fn::GetAZs": ""}}}}}
        assert result == expected

    def test_replace_importvalue_tag(self) -> None:
        """Test replacing !ImportValue tags with Fn::ImportValue intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      VpcId: !ImportValue SharedVpcId"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"VpcId": {"Fn::ImportValue": "SharedVpcId"}}}}}
        assert result == expected

    def test_nested_tag_replacement(self) -> None:
        """Test replacing nested CloudFormation tags."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      Name: !Sub
        - '${Prefix}-${!Ref Suffix}'
        - Prefix: !Ref PrefixParam"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Resources": {
                "MyResource": {
                    "Properties": {
                        "Name": {
                            "Fn::Sub": [
                                "${Prefix}-${!Ref Suffix}",
                                {"Prefix": {"Ref": "PrefixParam"}},
                            ]
                        }
                    }
                }
            }
        }
        assert result == expected

    def test_complex_nested_tags(self) -> None:
        """Test complex nested tag structures."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      ComplexValue: !Join
        - '-'
        - - !Select
            - 0
            - !Split
              - ','
              - !Ref CSVParam
          - !GetAtt
            - MyBucket
            - Arn
          - !Sub '${AWS::Region}'"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Resources": {
                "MyResource": {
                    "Properties": {
                        "ComplexValue": {
                            "Fn::Join": [
                                "-",
                                [
                                    {
                                        "Fn::Select": [
                                            0,
                                            {"Fn::Split": [",", {"Ref": "CSVParam"}]},
                                        ]
                                    },
                                    {"Fn::GetAtt": ["MyBucket", "Arn"]},
                                    {"Fn::Sub": "${AWS::Region}"},
                                ],
                            ]
                        }
                    }
                }
            }
        }
        assert result == expected

    def test_without_replace_tags_flag(self) -> None:
        """Test that tags are preserved when replace_tags is False."""
        yaml_content = """Resources:
  MyBucket:
    Properties:
      BucketName: !Ref BucketParam"""

        result = load_yaml(yaml_content, replace_tags=False)
        # Check that the RefTag object is preserved
        assert hasattr(result["Resources"]["MyBucket"]["Properties"]["BucketName"], "value")
        assert result["Resources"]["MyBucket"]["Properties"]["BucketName"].value == "BucketParam"

    def test_replace_tags_in_file(self, tmp_path) -> None:
        """Test replacing tags when loading from file."""
        yaml_content = """Resources:
  MyFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-function'
      Role: !GetAtt
        - LambdaRole
        - Arn
      Environment:
        Variables:
          BUCKET_NAME: !Ref S3Bucket
          REGION: !Ref AWS::Region"""

        template_file = tmp_path / "template.yaml"
        template_file.write_text(yaml_content)

        result = load_yaml_file(str(template_file), replace_tags=True)
        expected = {
            "Resources": {
                "MyFunction": {
                    "Type": "AWS::Lambda::Function",
                    "Properties": {
                        "FunctionName": {"Fn::Sub": "${AWS::StackName}-function"},
                        "Role": {"Fn::GetAtt": ["LambdaRole", "Arn"]},
                        "Environment": {
                            "Variables": {
                                "BUCKET_NAME": {"Ref": "S3Bucket"},
                                "REGION": {"Ref": "AWS::Region"},
                            }
                        },
                    },
                }
            }
        }
        assert result == expected

    def test_replace_tags_preserves_other_content(self) -> None:
        """Test that non-tag content is preserved during replacement."""
        yaml_content = """Description: Test Template
Parameters:
  BucketName:
    Type: String
    Default: my-bucket
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketName
      Tags:
        - Key: Name
          Value: !Sub '${AWS::StackName}-bucket'
        - Key: Environment
          Value: production"""

        result = load_yaml(yaml_content, replace_tags=True)

        # Check that non-tag content is preserved
        assert result["Description"] == "Test Template"
        assert result["Parameters"]["BucketName"]["Type"] == "String"
        assert result["Parameters"]["BucketName"]["Default"] == "my-bucket"
        assert result["Resources"]["MyBucket"]["Type"] == "AWS::S3::Bucket"

        # Check that tags are replaced
        assert result["Resources"]["MyBucket"]["Properties"]["BucketName"] == {"Ref": "BucketName"}
        assert result["Resources"]["MyBucket"]["Properties"]["Tags"][0]["Value"] == {"Fn::Sub": "${AWS::StackName}-bucket"}
        assert result["Resources"]["MyBucket"]["Properties"]["Tags"][1]["Value"] == "production"

    def test_replace_findinmap_tag(self) -> None:
        """Test replacing !FindInMap tags with Fn::FindInMap intrinsic function."""
        yaml_content = """Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: !FindInMap
        - RegionMap
        - !Ref AWS::Region
        - AMI"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Resources": {
                "MyInstance": {
                    "Type": "AWS::EC2::Instance",
                    "Properties": {"ImageId": {"Fn::FindInMap": ["RegionMap", {"Ref": "AWS::Region"}, "AMI"]}},
                }
            }
        }
        assert result == expected

    def test_replace_transform_tag(self) -> None:
        """Test replacing !Transform tags with Fn::Transform intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Type: AWS::CloudFormation::CustomResource
    Properties:
      Data: !Transform
        Name: MyTransform
        Parameters:
          Param1: Value1"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Resources": {
                "MyResource": {
                    "Type": "AWS::CloudFormation::CustomResource",
                    "Properties": {"Data": {"Fn::Transform": {"Name": "MyTransform", "Parameters": {"Param1": "Value1"}}}},
                }
            }
        }
        assert result == expected

    def test_replace_conditional_tags(self) -> None:
        """Test replacing conditional function tags."""
        yaml_content = """Conditions:
  IsProduction: !Equals
    - !Ref Environment
    - production
  HasMultiAZ: !And
    - !Equals [!Ref Environment, production]
    - !Not [!Equals [!Ref Region, us-east-1]]
  UseCustomVpc: !Or
    - !Equals [!Ref VpcId, ""]
    - !Condition IsProduction
Resources:
  MyResource:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !If
        - IsProduction
        - t3.large
        - t3.micro"""

        result = load_yaml(yaml_content, replace_tags=True)

        # Check conditions
        assert result["Conditions"]["IsProduction"] == {"Fn::Equals": [{"Ref": "Environment"}, "production"]}
        assert result["Conditions"]["HasMultiAZ"] == {
            "Fn::And": [
                {"Fn::Equals": [{"Ref": "Environment"}, "production"]},
                {"Fn::Not": [{"Fn::Equals": [{"Ref": "Region"}, "us-east-1"]}]},
            ]
        }
        assert result["Conditions"]["UseCustomVpc"] == {"Fn::Or": [{"Fn::Equals": [{"Ref": "VpcId"}, ""]}, {"Condition": "IsProduction"}]}

        # Check If function
        assert result["Resources"]["MyResource"]["Properties"]["InstanceType"] == {"Fn::If": ["IsProduction", "t3.large", "t3.micro"]}

    def test_complex_nested_with_new_tags(self) -> None:
        """Test complex nested structures with new tags."""
        yaml_content = """Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Condition: !And
      - !Not [!Equals [!Ref Environment, dev]]
      - !Or
        - !Equals [!Ref CreateBucket, "true"]
        - !Condition IsProduction
    Properties:
      BucketName: !If
        - IsProduction
        - !Sub '${AWS::StackName}-prod-${!GetAtt MyResource.Id}'
        - !Join
          - '-'
          - - !Ref AWS::StackName
            - dev
            - !Select [0, !Split ['-', !Ref Identifier]]"""

        result = load_yaml(yaml_content, replace_tags=True)

        # Check condition
        assert result["Resources"]["MyBucket"]["Condition"] == {
            "Fn::And": [
                {"Fn::Not": [{"Fn::Equals": [{"Ref": "Environment"}, "dev"]}]},
                {
                    "Fn::Or": [
                        {"Fn::Equals": [{"Ref": "CreateBucket"}, "true"]},
                        {"Condition": "IsProduction"},
                    ]
                },
            ]
        }

        # Check nested If with Sub and Join
        bucket_name = result["Resources"]["MyBucket"]["Properties"]["BucketName"]
        assert bucket_name["Fn::If"][0] == "IsProduction"
        assert bucket_name["Fn::If"][1] == {"Fn::Sub": "${AWS::StackName}-prod-${!GetAtt MyResource.Id}"}
        assert bucket_name["Fn::If"][2]["Fn::Join"][0] == "-"


class TestProcessYamlTemplateComprehensive:
    """Comprehensive test cases for the process_yaml_template function."""

    def test_comprehensive_cfntools_and_cloudformation_processing(self, tmp_path: Path) -> None:
        """
        Comprehensive test that validates both CFNTools processing and CloudFormation tag preservation.

        This test ensures that:
        1. CFNTools tags are processed correctly during loading
        2. CloudFormation tags are preserved as objects and can be dumped back to YAML syntax
        3. The template structure remains intact
        4. Both simple and complex nested scenarios work
        """
        # Create external files for inclusion
        config_file = tmp_path / "config.json"
        config_content = {"database": {"host": "localhost", "port": 5432, "name": "myapp"}, "redis": {"host": "redis.example.com", "port": 6379}}
        config_file.write_text(json.dumps(config_content, indent=2))

        policy_file = tmp_path / "policy.yaml"
        policy_content = """Version: '2012-10-17'
Statement:
  - Effect: Allow
    Principal: '*'
    Action: 's3:GetObject'
    Resource: !Sub '${BucketArn}/*'"""
        policy_file.write_text(policy_content)

        # Create comprehensive template with mixed CFNTools and CloudFormation tags
        template_file = tmp_path / "template.yaml"
        template_content = """AWSTemplateFormatVersion: '2010-09-09'
Description: Comprehensive test template with CFNTools and CloudFormation tags
Transform: AWS::Serverless-2016-10-31

Parameters:
  Environment:
    Type: String
    Default: dev
  BucketPrefix:
    Type: String
    Default: my-app

Conditions:
  IsProduction: !Equals
    - !Ref Environment
    - production
  HasCustomConfig: !Not
    - !Equals [!Ref BucketPrefix, ""]

Resources:
  # Resource with multiple CloudFormation tags
  S3Bucket:
    Type: AWS::S3::Bucket
    Condition: !And
      - !Condition IsProduction
      - !Not [!Equals [!Ref BucketPrefix, ""]]
    Properties:
      BucketName: !Sub
        - '${{Prefix}}-${{Environment}}-${{UUID}}'
        - Prefix: !Ref BucketPrefix
          Environment: !Ref Environment
          UUID: !CFNToolsUUID
      VersioningConfiguration:
        Status: !If
          - IsProduction
          - Enabled
          - Suspended
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: CreatedAt
          Value: !CFNToolsTimestamp
        - Key: Version
          Value: !CFNToolsVersion
        - Key: ConfigHash
          Value: !CFNToolsCRC
            - !CFNToolsIncludeFile config.json
            - Algorithm: sha256

  # Lambda function with included policy and various tags
  LambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Join
        - '-'
        - - !Ref AWS::StackName
          - processor
          - !Select [0, !Split ['-', !Ref AWS::AccountId]]
      Runtime: python3.9
      Handler: index.handler
      Role: !GetAtt LambdaRole.Arn
      Code:
        ZipFile: |
          import json
          def handler(event, context):
              return {{'statusCode': 200, 'body': 'Hello'}}
      Environment:
        Variables:
          BUCKET_NAME: !Ref S3Bucket
          CONFIG_DATA: !CFNToolsToString
            - !CFNToolsIncludeFile config.json
            - ConvertTo: JSONString
              OneLine: true
          POLICY_TEMPLATE: !CFNToolsToString
            - !CFNToolsIncludeFile policy.yaml
            - ConvertTo: YAMLString

  # IAM Role with included policy
  LambdaRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${{AWS::StackName}}-lambda-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: S3Access
          PolicyDocument: !CFNToolsIncludeFile policy.yaml

Outputs:
  BucketName:
    Description: Name of the created bucket
    Value: !Ref S3Bucket
    Export:
      Name: !Sub '${{AWS::StackName}}-BucketName'
  
  FunctionArn:
    Description: ARN of the Lambda function
    Value: !GetAtt LambdaFunction.Arn
    Condition: IsProduction
  
  ConfigChecksum:
    Description: Checksum of configuration
    Value: !CFNToolsCRC
      - !CFNToolsIncludeFile config.json
      - Algorithm: md5
      - Encoding: base64"""

        template_file.write_text(template_content)

        # Test 1: Process template with replace_tags=False and load back to verify structure
        result_yaml = process_yaml_template(str(template_file), replace_tags=False)

        # Load the processed YAML back to verify it's valid and check the structure
        from aws_sam_tools.cfn_yaml import load_yaml

        processed_data = load_yaml(result_yaml)

        # Validate basic template structure is preserved
        assert processed_data["AWSTemplateFormatVersion"] == "2010-09-09"
        assert processed_data["Description"] == "Comprehensive test template with CFNTools and CloudFormation tags"
        assert processed_data["Transform"] == "AWS::Serverless-2016-10-31"
        assert "Parameters" in processed_data
        assert "Conditions" in processed_data
        assert "Resources" in processed_data
        assert "Outputs" in processed_data

        # Validate CloudFormation tags are preserved as tag objects
        s3_bucket = processed_data["Resources"]["S3Bucket"]
        assert hasattr(s3_bucket["Condition"], "value"), "Condition should be a CloudFormation tag object"
        assert hasattr(s3_bucket["Properties"]["BucketName"], "value"), "BucketName should be a CloudFormation tag object"
        assert hasattr(s3_bucket["Properties"]["VersioningConfiguration"]["Status"], "value"), "Status should be a CloudFormation tag object"

        # Validate CloudFormation tags in different sections
        lambda_func = processed_data["Resources"]["LambdaFunction"]
        assert hasattr(lambda_func["Properties"]["FunctionName"], "value"), "FunctionName should be a CloudFormation tag object"
        assert hasattr(lambda_func["Properties"]["Role"], "value"), "Role should be a CloudFormation tag object"
        assert hasattr(lambda_func["Properties"]["Environment"]["Variables"]["BUCKET_NAME"], "value"), "BUCKET_NAME should be a CloudFormation tag object"

        # Validate CFNTools tags were processed correctly
        # UUID should be a string now (processed)
        uuid_value = s3_bucket["Properties"]["BucketName"].value[1]["UUID"]
        assert isinstance(uuid_value, str), "UUID should be processed to a string"
        import re

        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        assert re.match(uuid_pattern, uuid_value), "UUID should be valid format"

        # Timestamp should be a string (processed)
        timestamp_value = s3_bucket["Properties"]["Tags"][1]["Value"]
        assert isinstance(timestamp_value, str), "Timestamp should be processed to a string"
        timestamp_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        assert re.match(timestamp_pattern, timestamp_value), "Timestamp should be valid ISO format"

        # Version should be a string (processed)
        version_value = s3_bucket["Properties"]["Tags"][2]["Value"]
        assert isinstance(version_value, str), "Version should be processed to a string"

        # ConfigHash should be a string (processed)
        config_hash_value = s3_bucket["Properties"]["Tags"][3]["Value"]
        assert isinstance(config_hash_value, str), "ConfigHash should be processed to a string"
        sha256_pattern = r"^[0-9a-f]{64}$"
        assert re.match(sha256_pattern, config_hash_value), "ConfigHash should be SHA256 hex string"

        # CONFIG_DATA should be a JSON string with included file content
        config_data_value = lambda_func["Properties"]["Environment"]["Variables"]["CONFIG_DATA"]
        assert isinstance(config_data_value, str), "CONFIG_DATA should be processed to a string"
        config_parsed = json.loads(config_data_value)
        assert config_parsed["database"]["host"] == "localhost"
        assert config_parsed["database"]["port"] == 5432
        assert config_parsed["redis"]["host"] == "redis.example.com"

        # POLICY_TEMPLATE should be a YAML string with included file content
        policy_template_value = lambda_func["Properties"]["Environment"]["Variables"]["POLICY_TEMPLATE"]
        assert isinstance(policy_template_value, str), "POLICY_TEMPLATE should be processed to a string"
        assert "Version: '2012-10-17'" in policy_template_value
        assert "s3:GetObject" in policy_template_value

        # Included policy should be expanded in IAM role
        role_policy = processed_data["Resources"]["LambdaRole"]["Properties"]["Policies"][0]["PolicyDocument"]
        assert role_policy["Version"] == "2012-10-17"
        assert role_policy["Statement"][0]["Effect"] == "Allow"
        assert role_policy["Statement"][0]["Action"] == "s3:GetObject"
        # The !Sub tag in the included file should be preserved
        assert hasattr(role_policy["Statement"][0]["Resource"], "value"), "Resource should be a CloudFormation tag object"

        # MD5 checksum in outputs should be processed
        config_checksum_value = processed_data["Outputs"]["ConfigChecksum"]["Value"]
        assert isinstance(config_checksum_value, str), "ConfigChecksum should be processed to a string"
        # MD5 is 32 hex characters
        md5_pattern = r"^[0-9a-f]{32}$"
        assert re.match(md5_pattern, config_checksum_value), "ConfigChecksum should be MD5 hex string"

        # Test 2: Process template with replace_tags=True and verify intrinsic functions
        result_yaml_replaced = process_yaml_template(str(template_file), replace_tags=True)
        processed_data_replaced = yaml.safe_load(result_yaml_replaced)

        # Validate CloudFormation tags are converted to intrinsic functions
        s3_bucket_replaced = processed_data_replaced["Resources"]["S3Bucket"]
        assert isinstance(s3_bucket_replaced["Condition"], dict), "Condition should be converted to dict"
        assert "Fn::And" in s3_bucket_replaced["Condition"], "Condition should use Fn::And"

        bucket_name_replaced = s3_bucket_replaced["Properties"]["BucketName"]
        assert isinstance(bucket_name_replaced, dict), "BucketName should be converted to dict"
        assert "Fn::Sub" in bucket_name_replaced, "BucketName should use Fn::Sub"

        # Validate CFNTools processing still worked in replace_tags=True mode
        lambda_func_replaced = processed_data_replaced["Resources"]["LambdaFunction"]
        config_data_replaced = lambda_func_replaced["Properties"]["Environment"]["Variables"]["CONFIG_DATA"]
        assert isinstance(config_data_replaced, str), "CONFIG_DATA should still be processed string"
        config_parsed_replaced = json.loads(config_data_replaced)
        assert config_parsed_replaced["database"]["host"] == "localhost"

        # Validate the processed result is valid YAML that can be parsed
        assert processed_data_replaced["AWSTemplateFormatVersion"] == "2010-09-09"
        assert "S3Bucket" in processed_data_replaced["Resources"]
        assert "LambdaFunction" in processed_data_replaced["Resources"]

    def test_cloudformation_tags_survive_roundtrip(self, tmp_path: Path) -> None:
        """
        Test that CloudFormation tags survive the process → dump → load cycle.

        This verifies that after processing with CFNTools and dumping back to YAML,
        the CloudFormation tags can still be parsed correctly when loaded again.
        """
        # Create a template with both CFNTools and CloudFormation tags
        template_file = tmp_path / "template.yaml"
        template_content = """AWSTemplateFormatVersion: '2010-09-09'
Resources:
  S3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${AWS::StackName}-bucket'
      BucketId: !CFNToolsUUID
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: CreatedAt
          Value: !CFNToolsTimestamp
      VersioningConfiguration:
        Status: !If
          - IsProduction
          - Enabled
          - Suspended
      NotificationConfiguration:
        TopicConfigurations:
          - Topic: !GetAtt MyTopic.Arn
            Event: s3:ObjectCreated:*

  MyTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Join
        - '-'
        - - !Ref AWS::StackName
          - notifications
          - !Select [0, !Split ['-', !Ref AWS::AccountId]]

Parameters:
  Environment:
    Type: String
    Default: dev

Conditions:
  IsProduction: !Equals
    - !Ref Environment
    - production"""

        template_file.write_text(template_content)

        # Step 1: Process template (CFNTools tags processed, CloudFormation tags preserved)
        processed_yaml = process_yaml_template(str(template_file), replace_tags=False)

        # Step 2: Load the processed YAML again with CloudFormation loader to verify tags survived
        from aws_sam_tools.cfn_yaml import EqualsTag, GetAttTag, IfTag, JoinTag, RefTag, SelectTag, SplitTag, SubTag, load_yaml

        reloaded_data = load_yaml(processed_yaml)

        # Verify template structure is intact
        assert reloaded_data["AWSTemplateFormatVersion"] == "2010-09-09"
        assert "Resources" in reloaded_data
        assert "Parameters" in reloaded_data
        assert "Conditions" in reloaded_data

        # Verify CFNTools tags were processed (UUID and timestamp should be actual values)
        s3_bucket = reloaded_data["Resources"]["S3Bucket"]

        # BucketName should be a SubTag (CloudFormation tag preserved)
        bucket_name_tag = s3_bucket["Properties"]["BucketName"]
        assert isinstance(bucket_name_tag, SubTag), "BucketName should be SubTag object"
        assert bucket_name_tag.value == ["${AWS::StackName}-bucket"], "BucketName SubTag should have correct template"

        # BucketId should be processed UUID (CFNTools tag processed)
        bucket_id_value = s3_bucket["Properties"]["BucketId"]
        assert isinstance(bucket_id_value, str), "BucketId should be processed to string"
        import re

        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        assert re.match(uuid_pattern, bucket_id_value), "BucketId should be valid UUID"

        # CreatedAt timestamp should be processed to actual timestamp
        created_at_value = s3_bucket["Properties"]["Tags"][1]["Value"]
        assert isinstance(created_at_value, str), "CreatedAt should be processed to string"
        timestamp_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
        assert re.match(timestamp_pattern, created_at_value), "CreatedAt should be valid timestamp"

        # Verify CloudFormation tags are properly preserved as tag objects
        # Environment should be RefTag
        environment_tag = s3_bucket["Properties"]["Tags"][0]["Value"]
        assert isinstance(environment_tag, RefTag), "Environment should be RefTag object"
        assert environment_tag.value == "Environment", "RefTag should reference 'Environment'"

        # Status should be IfTag
        status_tag = s3_bucket["Properties"]["VersioningConfiguration"]["Status"]
        assert isinstance(status_tag, IfTag), "Status should be IfTag object"
        assert status_tag.value == ["IsProduction", "Enabled", "Suspended"], "IfTag should have correct condition and values"

        # Topic should be GetAttTag
        topic_tag = s3_bucket["Properties"]["NotificationConfiguration"]["TopicConfigurations"][0]["Topic"]
        assert isinstance(topic_tag, GetAttTag), "Topic should be GetAttTag object"
        assert topic_tag.value == ["MyTopic", "Arn"], "GetAttTag should reference MyTopic.Arn"

        # TopicName should be JoinTag with nested tags
        my_topic = reloaded_data["Resources"]["MyTopic"]
        topic_name_tag = my_topic["Properties"]["TopicName"]
        assert isinstance(topic_name_tag, JoinTag), "TopicName should be JoinTag object"

        # Verify the JoinTag structure: [delimiter, [values...]]
        join_value = topic_name_tag.value
        assert isinstance(join_value, list) and len(join_value) == 2, "JoinTag should have delimiter and values"
        assert join_value[0] == "-", "Join delimiter should be '-'"

        # Values should contain RefTag and SelectTag
        join_values = join_value[1]
        assert isinstance(join_values[0], RefTag), "First join value should be RefTag"
        assert join_values[0].value == "AWS::StackName", "RefTag should reference AWS::StackName"
        assert join_values[1] == "notifications", "Second join value should be literal string"
        assert isinstance(join_values[2], SelectTag), "Third join value should be SelectTag"

        # Verify SelectTag contains SplitTag
        select_tag = join_values[2]
        select_value = select_tag.value
        assert select_value[0] == 0, "SelectTag should select index 0"
        assert isinstance(select_value[1], SplitTag), "SelectTag should contain SplitTag"

        # Verify SplitTag contains RefTag
        split_tag = select_value[1]
        split_value = split_tag.value
        assert split_value[0] == "-", "SplitTag delimiter should be '-'"
        assert isinstance(split_value[1], RefTag), "SplitTag should contain RefTag"
        assert split_value[1].value == "AWS::AccountId", "RefTag should reference AWS::AccountId"

        # Verify Condition is EqualsTag
        condition_tag = reloaded_data["Conditions"]["IsProduction"]
        assert isinstance(condition_tag, EqualsTag), "Condition should be EqualsTag object"
        condition_value = condition_tag.value
        assert isinstance(condition_value[0], RefTag), "First equals value should be RefTag"
        assert condition_value[0].value == "Environment", "RefTag should reference Environment"
        assert condition_value[1] == "production", "Second equals value should be 'production'"

        # Step 3: Verify the reloaded data can be dumped again and still contains CloudFormation tags
        from aws_sam_tools.cfn_yaml import dump_yaml

        redumped_yaml = dump_yaml(reloaded_data)

        # Step 4: Load the redumped YAML to verify tags are still valid
        final_reloaded_data = load_yaml(redumped_yaml)

        # Verify CloudFormation tags are still preserved after round-trip
        final_s3_bucket = final_reloaded_data["Resources"]["S3Bucket"]

        # Check that tag types are preserved
        final_environment_tag = final_s3_bucket["Properties"]["Tags"][0]["Value"]
        assert isinstance(final_environment_tag, RefTag), "Environment should still be RefTag after round-trip"
        assert final_environment_tag.value == "Environment", "RefTag value should be preserved"

        final_status_tag = final_s3_bucket["Properties"]["VersioningConfiguration"]["Status"]
        assert isinstance(final_status_tag, IfTag), "Status should still be IfTag after round-trip"

        final_topic_tag = final_s3_bucket["Properties"]["NotificationConfiguration"]["TopicConfigurations"][0]["Topic"]
        assert isinstance(final_topic_tag, GetAttTag), "Topic should still be GetAttTag after round-trip"
        assert final_topic_tag.value == ["MyTopic", "Arn"], "GetAttTag value should be preserved"

        final_condition_tag = final_reloaded_data["Conditions"]["IsProduction"]
        assert isinstance(final_condition_tag, EqualsTag), "Condition should still be EqualsTag after round-trip"

        # Verify CFNTools processing results are preserved (UUID and timestamp should still be there)
        final_bucket_name_tag = final_s3_bucket["Properties"]["BucketName"]
        assert isinstance(final_bucket_name_tag, SubTag), "BucketName should still be SubTag after round-trip"
        assert final_bucket_name_tag.value == ["${AWS::StackName}-bucket"], "BucketName SubTag should be preserved"

        final_bucket_id_value = final_s3_bucket["Properties"]["BucketId"]
        assert isinstance(final_bucket_id_value, str), "BucketId should still be string after round-trip"
        assert re.match(uuid_pattern, final_bucket_id_value), "UUID should still be valid after round-trip"

        final_created_at_value = final_s3_bucket["Properties"]["Tags"][1]["Value"]
        assert isinstance(final_created_at_value, str), "CreatedAt should still be string after round-trip"
        assert re.match(timestamp_pattern, final_created_at_value), "Timestamp should still be valid after round-trip"

    def test_process_yaml_template_error_handling(self, tmp_path: Path) -> None:
        """Test error handling in process_yaml_template."""
        # Test file not found
        with pytest.raises(FileNotFoundError, match="Template file not found"):
            process_yaml_template("/nonexistent/template.yaml")

        # Test invalid YAML with CFNTools tag error
        invalid_template = tmp_path / "invalid.yaml"
        invalid_content = """Resources:
  Bucket:
    Properties:
      Config: !CFNToolsIncludeFile nonexistent.yaml"""
        invalid_template.write_text(invalid_content)

        with pytest.raises(yaml.constructor.ConstructorError, match="file not found"):
            process_yaml_template(str(invalid_template))

    def test_process_yaml_template_edge_cases(self, tmp_path: Path) -> None:
        """Test edge cases in process_yaml_template."""
        # Test empty template
        empty_template = tmp_path / "empty.yaml"
        empty_template.write_text("")

        result = process_yaml_template(str(empty_template))
        assert "null" in result

        # Test template with only CloudFormation tags
        cf_only_template = tmp_path / "cf_only.yaml"
        cf_only_content = """Resources:
  Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketName"""
        cf_only_template.write_text(cf_only_content)

        result = process_yaml_template(str(cf_only_template))
        assert "!Ref BucketName" in result

        # Test template with only CFNTools tags
        cfntools_only_template = tmp_path / "cfntools_only.yaml"
        cfntools_only_content = """Config:
  UUID: !CFNToolsUUID
  Timestamp: !CFNToolsTimestamp"""
        cfntools_only_template.write_text(cfntools_only_content)

        result = process_yaml_template(str(cfntools_only_template))
        assert "!CFNToolsUUID" not in result
        assert "!CFNToolsTimestamp" not in result


class TestProcessYamlTemplate:
    """Test cases for the process_yaml_template function."""

    def test_process_yaml_template_cloudformation_tags_preserved(self, tmp_path: Path) -> None:
        """Test that CloudFormation tags are preserved when replace_tags=False."""
        template_file = tmp_path / "template.yaml"
        template_content = """AWSTemplateFormatVersion: '2010-09-09'
Description: Test template with CloudFormation tags
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketNameParameter
      Tags:
        - Key: Environment
          Value: !Sub '${Environment}-bucket'
  MyFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-function'
      Role: !GetAtt MyRole.Arn
      Code:
        ZipFile: !Base64 |
          def handler(event, context):
              return {'statusCode': 200}
Parameters:
  BucketNameParameter:
    Type: String
    Default: my-test-bucket
  Environment:
    Type: String
    Default: dev"""
        template_file.write_text(template_content)

        result = process_yaml_template(str(template_file), replace_tags=False)

        # Verify CloudFormation tags are preserved in output
        assert "!Ref BucketNameParameter" in result
        assert "!Sub ${Environment}-bucket" in result
        assert "!Sub ${AWS::StackName}-function" in result
        assert "!GetAtt MyRole.Arn" in result
        assert "!Base64" in result

        # Verify the structure is maintained
        assert "AWSTemplateFormatVersion: '2010-09-09'" in result
        assert "Description: Test template with CloudFormation tags" in result
        assert "Resources:" in result
        assert "Parameters:" in result

    def test_process_yaml_template_replace_tags_enabled(self, tmp_path: Path) -> None:
        """Test that CloudFormation tags are converted to intrinsic functions when replace_tags=True."""
        template_file = tmp_path / "template.yaml"
        template_content = """Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketNameParameter
      Description: !Sub 'Bucket for ${Environment}'
      Arn: !GetAtt SomeResource.Arn
      Values: !Join
        - ','
        - - value1
          - value2"""
        template_file.write_text(template_content)

        result = process_yaml_template(str(template_file), replace_tags=True)

        # CloudFormation tags should be converted to intrinsic functions
        assert "Ref: BucketNameParameter" in result
        assert "Fn::Sub: Bucket for ${Environment}" in result
        assert "Fn::GetAtt:" in result
        assert "- SomeResource" in result
        assert "- Arn" in result
        assert "Fn::Join:" in result

        # Original tag syntax should not be present
        assert "!Ref" not in result
        assert "!Sub" not in result
        assert "!GetAtt" not in result
        assert "!Join" not in result

    def test_process_yaml_template_with_cfntools_tags(self, tmp_path: Path) -> None:
        """Test processing of CFNTools tags along with CloudFormation tags."""
        # Create included file
        include_file = tmp_path / "config.yaml"
        include_content = """database:
  host: localhost
  port: 5432"""
        include_file.write_text(include_content)

        template_file = tmp_path / "template.yaml"
        template_content = """Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketNameParameter
      Config: !CFNToolsIncludeFile config.yaml
      UUID: !CFNToolsUUID"""
        template_file.write_text(template_content)

        result = process_yaml_template(str(template_file), replace_tags=False)

        # CloudFormation tags should be preserved
        assert "!Ref BucketNameParameter" in result

        # CFNTools tags should be processed (included file content should be present)
        assert "database:" in result
        assert "host: localhost" in result
        assert "port: 5432" in result

        # UUID should be generated (should be a string, not the tag)
        assert "!CFNToolsUUID" not in result

    def test_process_yaml_template_file_not_found(self) -> None:
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError, match="Template file not found"):
            process_yaml_template("/nonexistent/path/template.yaml")

    def test_process_yaml_template_invalid_yaml(self, tmp_path: Path) -> None:
        """Test that YAMLError is raised for invalid YAML content."""
        template_file = tmp_path / "invalid.yaml"
        template_content = """
        Resources:
          MyBucket:
            Type: AWS::S3::Bucket
            Properties:
              BucketName: !Ref
        """  # Invalid YAML - !Ref without value
        template_file.write_text(template_content)

        with pytest.raises(Exception):  # Should raise some kind of parsing error
            process_yaml_template(str(template_file))

    def test_process_yaml_template_dump_kwargs(self, tmp_path: Path) -> None:
        """Test that additional dump kwargs are passed through correctly."""
        template_file = tmp_path / "template.yaml"
        template_content = """Resources:
  ZBucket:
    Type: AWS::S3::Bucket
  ABucket:
    Type: AWS::S3::Bucket"""
        template_file.write_text(template_content)

        # Test with sort_keys=True
        result_sorted = process_yaml_template(str(template_file), sort_keys=True)
        lines = result_sorted.strip().split("\n")
        resource_lines = [line for line in lines if "Bucket:" in line]

        # Should be sorted alphabetically
        assert "ABucket:" in resource_lines[0]
        assert "ZBucket:" in resource_lines[1]

    def test_process_yaml_template_complex_nested_tags(self, tmp_path: Path) -> None:
        """Test processing of complex nested CloudFormation tags."""
        template_file = tmp_path / "template.yaml"
        template_content = """Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub
        - '${StackName}-${Suffix}'
        - StackName: !Ref 'AWS::StackName'
          Suffix: !Ref BucketSuffix
      Tags:
        - Key: Name
          Value: !Join
            - '-'
            - - !Ref Environment
              - bucket
              - !Select
                - 0
                - !Split
                  - '-'
                  - !Ref 'AWS::StackName'"""
        template_file.write_text(template_content)

        result = process_yaml_template(str(template_file), replace_tags=False)

        # Verify all nested tags are preserved
        assert "!Sub" in result
        assert "!Ref AWS::StackName" in result
        assert "!Ref BucketSuffix" in result
        assert "!Join" in result
        assert "!Select" in result
        assert "!Split" in result
        assert "!Ref Environment" in result

        # Test with replace_tags=True
        result_replaced = process_yaml_template(str(template_file), replace_tags=True)

        # Verify tags are converted
        assert "Fn::Sub:" in result_replaced
        assert "Ref: AWS::StackName" in result_replaced
        assert "Fn::Join:" in result_replaced
        assert "Fn::Select:" in result_replaced
        assert "Fn::Split:" in result_replaced


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
        main_content = """Parameters:
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
