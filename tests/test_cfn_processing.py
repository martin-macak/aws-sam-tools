import json
from pathlib import Path

import pytest
import yaml

from aws_sam_tools.cfn_processing import (
    load_yaml,
    load_yaml_file,
    replace_cloudformation_tags,
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
        from datetime import datetime, timezone, timedelta

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
        main_content = f"""MyStack:
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
