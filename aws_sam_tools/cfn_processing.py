"""Extended CloudFormation template processing with CFNTools tags.

This module extends the core cfn_yaml functionality with additional processing
tags that enable advanced template manipulation capabilities. It includes tags
for file inclusion, string conversion, UUID generation, version stamping,
timestamp generation, and checksum calculation.

CFNTools Processing Tags:
- !CFNToolsIncludeFile: Include content from external files
- !CFNToolsToString: Convert values to JSON/YAML strings
- !CFNToolsUUID: Generate unique identifiers
- !CFNToolsVersion: Include version information from git
- !CFNToolsTimestamp: Generate timestamps with formatting options
- !CFNToolsCRC: Calculate checksums of values or files

The module also provides functionality to replace CloudFormation tags with
their intrinsic function equivalents for compatibility with standard AWS tools.

Example:
    >>> from aws_sam_tools.cfn_processing import load_yaml_file
    >>> template = load_yaml_file('template.yaml', replace_tags=True)
    >>> # CFNTools tags are processed, CloudFormation tags converted to intrinsic functions
"""

import base64
import hashlib
import json
import mimetypes
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dunamai import Style

try:
    from dunamai import Version, get_version
except ImportError:
    # Provide a fallback if dunamai is not available
    Version = None
    get_version = None

from aws_sam_tools.cfn_yaml import (
    AndTag,
    Base64Tag,
    CidrTag,
    CloudFormationLoader,
    CloudFormationTag,
    ConditionTag,
    EqualsTag,
    FindInMapTag,
    GetAttTag,
    GetAZsTag,
    IfTag,
    ImportValueTag,
    JoinTag,
    NotTag,
    OrTag,
    RefTag,
    SelectTag,
    SplitTag,
    SubTag,
    TransformTag,
    get_node_type_name,
)


class CFNToolsIncludeFileTag(CloudFormationTag):
    """Represents !CFNToolsIncludeFile tag."""

    pass


class CFNToolsToStringTag(CloudFormationTag):
    """Represents !CFNToolsToString tag."""

    pass


class CFNToolsUUIDTag(CloudFormationTag):
    """Represents !CFNToolsUUID tag."""

    pass


class CFNToolsVersionTag(CloudFormationTag):
    """Represents !CFNToolsVersion tag."""

    pass


class CFNToolsTimestampTag(CloudFormationTag):
    """Represents !CFNToolsTimestamp tag."""

    pass


class CFNToolsCRCTag(CloudFormationTag):
    """Represents !CFNToolsCRC tag."""

    pass


def construct_cfntools_include_file(loader: yaml.Loader, node: yaml.Node) -> Any:
    """Construct !CFNToolsIncludeFile tag."""
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.constructor.ConstructorError(
            None,
            None,
            f"expected a scalar node for file path, but found {get_node_type_name(node)}",
            node.start_mark,
        )

    file_path = loader.construct_scalar(node)
    if not file_path:
        raise yaml.constructor.ConstructorError(None, None, "!CFNToolsIncludeFile tag must specify a file path", node.start_mark)

    # If relative path, resolve from YAML file location
    if not os.path.isabs(file_path):
        if hasattr(loader, "name") and loader.name:
            base_dir = os.path.dirname(loader.name)
            file_path = os.path.join(base_dir, file_path)
        else:
            # Use current working directory if no loader name
            file_path = os.path.abspath(file_path)

    # Check if file exists
    if not os.path.exists(file_path):
        raise yaml.constructor.ConstructorError(None, None, f"!CFNToolsIncludeFile: file not found: {file_path}", node.start_mark)

    # Determine file type and load accordingly
    mime_type, _ = mimetypes.guess_type(file_path)
    file_extension = Path(file_path).suffix.lower()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Handle structured data formats
        if file_extension in [".yaml", ".yml"]:
            # Use the same loader to support nested CloudFormation tags
            return yaml.load(content, Loader=loader.__class__)
        elif file_extension == ".json" or (mime_type and "json" in mime_type):
            return json.loads(content)
        else:
            # Return as plain string for other file types
            return content
    except Exception as e:
        raise yaml.constructor.ConstructorError(None, None, f"!CFNToolsIncludeFile: error reading file {file_path}: {str(e)}", node.start_mark)


def cloudformation_tag_to_dict(tag: CloudFormationTag) -> Dict[str, Any]:
    """Convert CloudFormation tag to a dictionary representation."""
    tag_name = "!" + tag.__class__.__name__.replace("Tag", "")
    return {tag_name: tag.value}


def prepare_value_for_serialization(value: Any) -> Any:
    """Recursively prepare a value for JSON/YAML serialization by converting CloudFormation tags."""
    if isinstance(value, CloudFormationTag):
        return cloudformation_tag_to_dict(value)
    elif isinstance(value, dict):
        return {k: prepare_value_for_serialization(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [prepare_value_for_serialization(v) for v in value]
    else:
        return value


def construct_cfntools_to_string(loader: yaml.Loader, node: yaml.Node) -> str:
    """Construct !CFNToolsToString tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(
            None,
            None,
            f"expected a sequence node, but found {get_node_type_name(node)}",
            node.start_mark,
        )

    values = loader.construct_sequence(node, deep=True)
    if not values:
        raise yaml.constructor.ConstructorError(None, None, "!CFNToolsToString requires at least one parameter", node.start_mark)

    # First element is the value to convert
    value = values[0]

    # Parse optional parameters
    convert_to = "JSONString"
    one_line = False

    if len(values) > 1:
        if not isinstance(values[1], dict):
            raise yaml.constructor.ConstructorError(None, None, "!CFNToolsToString optional parameters must be a mapping", node.start_mark)

        options = values[1]
        if "ConvertTo" in options:
            convert_to = options["ConvertTo"]
            if convert_to not in ["YAMLString", "JSONString"]:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f'!CFNToolsToString ConvertTo must be "YAMLString" or "JSONString", got "{convert_to}"',
                    node.start_mark,
                )

        if "OneLine" in options:
            one_line = options["OneLine"]
            if not isinstance(one_line, bool):
                raise yaml.constructor.ConstructorError(None, None, f"!CFNToolsToString OneLine must be a boolean, got {type(one_line).__name__}", node.start_mark)

    # Convert value to string
    if isinstance(value, str):
        result = value
    elif isinstance(value, (dict, list)):
        # Prepare value by converting CloudFormation tags
        prepared_value = prepare_value_for_serialization(value)

        if convert_to == "YAMLString":
            result = yaml.dump(prepared_value, default_flow_style=False, sort_keys=False).rstrip("\n")
        else:  # JSONString
            if one_line:
                result = json.dumps(prepared_value, separators=(",", ":"), ensure_ascii=False)
            else:
                result = json.dumps(prepared_value, indent=2, ensure_ascii=False)
    else:
        # For other types, convert directly to string
        result = str(value)

    # Handle OneLine for string values with newlines
    if one_line and isinstance(value, str):
        result = result.replace("\n", " ")

    return result


def construct_cfntools_uuid(loader: yaml.Loader, node: yaml.Node) -> str:
    """Construct !CFNToolsUUID tag."""
    if not isinstance(node, yaml.ScalarNode) or node.value:
        raise yaml.constructor.ConstructorError(
            None,
            None,
            "!CFNToolsUUID takes no arguments",
            node.start_mark,
        )

    return str(uuid.uuid4())


def construct_cfntools_version(loader: yaml.Loader, node: yaml.Node) -> str:
    """Construct !CFNToolsVersion tag."""
    # Default values
    source = "Git"
    style = "semver"

    if isinstance(node, yaml.MappingNode):
        # Parse optional parameters
        options = loader.construct_mapping(node)

        if "Source" in options:
            source = options["Source"]
            if source not in ["Git", "Any"]:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f'!CFNToolsVersion Source must be "Git" or "Any", got "{source}"',
                    node.start_mark,
                )

        if "Style" in options:
            style = options["Style"]
            if style not in ["semver", "pep440"]:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f'!CFNToolsVersion Style must be "semver" or "pep440", got "{style}"',
                    node.start_mark,
                )
    elif not isinstance(node, yaml.ScalarNode) or node.value:
        raise yaml.constructor.ConstructorError(
            None,
            None,
            "!CFNToolsVersion takes no arguments or a mapping of options",
            node.start_mark,
        )

    # Get version using dunamai
    if get_version is None:
        # Fallback if dunamai is not available
        return "0.0.0-dev"

    try:
        if source == "Git":
            version = get_version("git")
        else:
            version = get_version("any")

        if style == "semver":
            return version.serialize()
        else:  # pep440
            return version.serialize(style=Style.Pep440)
    except Exception:
        # Fallback if version detection fails
        return "0.0.0-dev"


def construct_cfntools_timestamp(loader: yaml.Loader, node: yaml.Node) -> str:
    """Construct !CFNToolsTimestamp tag."""
    # Default values
    format_str = None  # Will use ISO-8601 by default
    offset = 0
    offset_unit = "seconds"

    if isinstance(node, yaml.MappingNode):
        # Parse optional parameters
        options = loader.construct_mapping(node)

        if "Format" in options:
            format_str = options["Format"]
            if not isinstance(format_str, str):
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f"!CFNToolsTimestamp Format must be a string, got {type(format_str).__name__}",
                    node.start_mark,
                )

        if "Offset" in options:
            offset = options["Offset"]
            if not isinstance(offset, int):
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f"!CFNToolsTimestamp Offset must be an integer, got {type(offset).__name__}",
                    node.start_mark,
                )

        if "OffsetUnit" in options:
            offset_unit = options["OffsetUnit"]
            valid_units = ["seconds", "minutes", "hours", "days", "weeks", "months", "years"]
            if offset_unit not in valid_units:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f'!CFNToolsTimestamp OffsetUnit must be one of {valid_units}, got "{offset_unit}"',
                    node.start_mark,
                )
    elif not isinstance(node, yaml.ScalarNode) or node.value:
        raise yaml.constructor.ConstructorError(
            None,
            None,
            "!CFNToolsTimestamp takes no arguments or a mapping of options",
            node.start_mark,
        )

    # Get current time in UTC
    now = datetime.now(timezone.utc)

    # Apply offset
    if offset != 0:
        delta = timedelta()  # Default
        if offset_unit == "seconds":
            delta = timedelta(seconds=offset)
        elif offset_unit == "minutes":
            delta = timedelta(minutes=offset)
        elif offset_unit == "hours":
            delta = timedelta(hours=offset)
        elif offset_unit == "days":
            delta = timedelta(days=offset)
        elif offset_unit == "weeks":
            delta = timedelta(weeks=offset)
        elif offset_unit == "months":
            # Approximate month as 30 days
            delta = timedelta(days=offset * 30)
        elif offset_unit == "years":
            # Approximate year as 365 days
            delta = timedelta(days=offset * 365)

        now = now + delta

    # Format the timestamp
    if format_str:
        return now.strftime(format_str)
    else:
        # ISO-8601 format with Z suffix
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def construct_cfntools_crc(loader: yaml.Loader, node: yaml.Node) -> str:
    """Construct !CFNToolsCRC tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(
            None,
            None,
            f"expected a sequence node, but found {get_node_type_name(node)}",
            node.start_mark,
        )

    values = loader.construct_sequence(node, deep=True)
    if not values:
        raise yaml.constructor.ConstructorError(None, None, "!CFNToolsCRC requires at least one parameter", node.start_mark)

    # First element is the value to checksum
    value = values[0]

    # Default values
    algorithm = "sha256"
    encoding = "hex"

    if len(values) > 1:
        if not isinstance(values[1], dict):
            raise yaml.constructor.ConstructorError(None, None, "!CFNToolsCRC optional parameters must be a mapping", node.start_mark)

        options = values[1]
        if "Algorithm" in options:
            algorithm = options["Algorithm"]
            valid_algorithms = ["md5", "sha1", "sha256", "sha512"]
            if algorithm not in valid_algorithms:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f'!CFNToolsCRC Algorithm must be one of {valid_algorithms}, got "{algorithm}"',
                    node.start_mark,
                )

        if "Encoding" in options:
            encoding = options["Encoding"]
            if encoding not in ["hex", "base64"]:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f'!CFNToolsCRC Encoding must be "hex" or "base64", got "{encoding}"',
                    node.start_mark,
                )

    # Prepare data for hashing
    if isinstance(value, str):
        if value.startswith("file://"):
            # Read file content
            file_path = value[7:]  # Remove "file://" prefix

            # If relative path, resolve from YAML file location
            if not os.path.isabs(file_path):
                if hasattr(loader, "name") and loader.name:
                    base_dir = os.path.dirname(loader.name)
                    file_path = os.path.join(base_dir, file_path)
                else:
                    file_path = os.path.abspath(file_path)

            if not os.path.exists(file_path):
                raise yaml.constructor.ConstructorError(None, None, f"!CFNToolsCRC: file not found: {file_path}", node.start_mark)

            try:
                with open(file_path, "rb") as f:
                    data = f.read()
            except Exception as e:
                raise yaml.constructor.ConstructorError(None, None, f"!CFNToolsCRC: error reading file {file_path}: {str(e)}", node.start_mark)
        else:
            # Use string as-is
            data = value.encode("utf-8")
    elif isinstance(value, (dict, list)):
        # Convert to JSON string for consistent hashing
        data = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    else:
        # Convert other types to string
        data = str(value).encode("utf-8")

    # Calculate hash
    hasher = hashlib.sha256()  # Default
    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha1":
        hasher = hashlib.sha1()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "sha512":
        hasher = hashlib.sha512()

    hasher.update(data)

    # Encode result
    if encoding == "hex":
        return hasher.hexdigest()
    else:  # base64
        return base64.b64encode(hasher.digest()).decode("ascii")


class CloudFormationProcessingLoader(CloudFormationLoader):
    """Extended YAML loader that supports CloudFormation tags and CFNTools processing tags."""

    pass


# Register the new processing tags
CloudFormationProcessingLoader.add_constructor("!CFNToolsIncludeFile", construct_cfntools_include_file)
CloudFormationProcessingLoader.add_constructor("!CFNToolsToString", construct_cfntools_to_string)
CloudFormationProcessingLoader.add_constructor("!CFNToolsUUID", construct_cfntools_uuid)
CloudFormationProcessingLoader.add_constructor("!CFNToolsVersion", construct_cfntools_version)
CloudFormationProcessingLoader.add_constructor("!CFNToolsTimestamp", construct_cfntools_timestamp)
CloudFormationProcessingLoader.add_constructor("!CFNToolsCRC", construct_cfntools_crc)


def replace_cloudformation_tags(data: Any) -> Any:
    """
    Recursively replace CloudFormation tags with their intrinsic function equivalents.

    Tag mappings:
    - !Ref -> {"Ref": value}
    - !GetAtt -> {"Fn::GetAtt": value}
    - !GetAZs -> {"Fn::GetAZs": value}
    - !ImportValue -> {"Fn::ImportValue": value}
    - !Join -> {"Fn::Join": value}
    - !Select -> {"Fn::Select": value}
    - !Split -> {"Fn::Split": value}
    - !Sub -> {"Fn::Sub": value}
    - !FindInMap -> {"Fn::FindInMap": value}
    - !Base64 -> {"Fn::Base64": value}
    - !Cidr -> {"Fn::Cidr": value}
    - !Transform -> {"Fn::Transform": value}
    - !And -> {"Fn::And": value}
    - !Equals -> {"Fn::Equals": value}
    - !If -> {"Fn::If": value}
    - !Not -> {"Fn::Not": value}
    - !Or -> {"Fn::Or": value}
    - !Condition -> {"Condition": value}
    """
    if isinstance(data, RefTag):
        return {"Ref": replace_cloudformation_tags(data.value)}
    elif isinstance(data, GetAttTag):
        return {"Fn::GetAtt": replace_cloudformation_tags(data.value)}
    elif isinstance(data, GetAZsTag):
        return {"Fn::GetAZs": replace_cloudformation_tags(data.value)}
    elif isinstance(data, ImportValueTag):
        return {"Fn::ImportValue": replace_cloudformation_tags(data.value)}
    elif isinstance(data, JoinTag):
        return {"Fn::Join": replace_cloudformation_tags(data.value)}
    elif isinstance(data, SelectTag):
        return {"Fn::Select": replace_cloudformation_tags(data.value)}
    elif isinstance(data, SplitTag):
        return {"Fn::Split": replace_cloudformation_tags(data.value)}
    elif isinstance(data, SubTag):
        # Sub tag stores value as a list, but for simple strings we want just the string
        replaced_value = replace_cloudformation_tags(data.value)
        if isinstance(replaced_value, list) and len(replaced_value) == 1:
            return {"Fn::Sub": replaced_value[0]}
        else:
            return {"Fn::Sub": replaced_value}
    elif isinstance(data, FindInMapTag):
        return {"Fn::FindInMap": replace_cloudformation_tags(data.value)}
    elif isinstance(data, Base64Tag):
        return {"Fn::Base64": replace_cloudformation_tags(data.value)}
    elif isinstance(data, CidrTag):
        return {"Fn::Cidr": replace_cloudformation_tags(data.value)}
    elif isinstance(data, TransformTag):
        return {"Fn::Transform": replace_cloudformation_tags(data.value)}
    elif isinstance(data, AndTag):
        return {"Fn::And": replace_cloudformation_tags(data.value)}
    elif isinstance(data, EqualsTag):
        return {"Fn::Equals": replace_cloudformation_tags(data.value)}
    elif isinstance(data, IfTag):
        return {"Fn::If": replace_cloudformation_tags(data.value)}
    elif isinstance(data, NotTag):
        return {"Fn::Not": replace_cloudformation_tags(data.value)}
    elif isinstance(data, OrTag):
        return {"Fn::Or": replace_cloudformation_tags(data.value)}
    elif isinstance(data, ConditionTag):
        # Condition is not an intrinsic function but a reference
        return {"Condition": data.value}
    elif isinstance(data, dict):
        return {k: replace_cloudformation_tags(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_cloudformation_tags(v) for v in data]
    else:
        return data


def load_yaml(stream: str, file_name: Optional[str] = None, replace_tags: bool = False) -> Dict[str, Any]:
    """
    Load YAML content with CloudFormation and CFNTools processing tag support.

    Args:
        stream: YAML content as string
        file_name: Optional file name to resolve relative paths
        replace_tags: If True, replace CloudFormation tags with intrinsic functions

    Returns:
        Dict containing the parsed YAML with all tags processed
    """
    loader = CloudFormationProcessingLoader(stream)
    if file_name:
        loader.name = file_name
    try:
        data = loader.get_single_data()
        if replace_tags:
            data = replace_cloudformation_tags(data)
        return data
    finally:
        loader.dispose()


def load_yaml_file(file_path: str, replace_tags: bool = False) -> Dict[str, Any]:
    """
    Load YAML file with CloudFormation and CFNTools processing tag support.

    Args:
        file_path: Path to the YAML file
        replace_tags: If True, replace CloudFormation tags with intrinsic functions

    Returns:
        Dict containing the parsed YAML with all tags processed
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return load_yaml(content, file_path, replace_tags)


def process_yaml_template(template_path: str, replace_tags: bool = False, **dump_kwargs) -> str:
    """
    Process a CloudFormation YAML template file and return the processed YAML string.

    This function loads a YAML template, processes any CFNTools tags, and returns
    the result as a YAML string with CloudFormation tags properly preserved or
    converted to intrinsic functions based on the replace_tags parameter.

    Args:
        template_path: Path to the CloudFormation template file
        replace_tags: If True, replace CloudFormation tags with intrinsic functions
        **dump_kwargs: Additional keyword arguments to pass to dump_yaml

    Returns:
        Processed YAML template as a string

    Raises:
        FileNotFoundError: If the template file doesn't exist
        yaml.YAMLError: If the YAML file cannot be parsed

    Example:
        >>> yaml_output = process_yaml_template('template.yaml')
        >>> print(yaml_output)  # CloudFormation tags preserved as !Ref, !Sub, etc.

        >>> yaml_output = process_yaml_template('template.yaml', replace_tags=True)
        >>> print(yaml_output)  # Tags converted to {"Ref": "..."}, {"Fn::Sub": "..."}, etc.
    """
    from aws_sam_tools.cfn_yaml import dump_yaml

    # Check if file exists
    template_file = Path(template_path)
    if not template_file.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    # Load and process the template with CFNTools support
    processed_data = load_yaml_file(str(template_file), replace_tags=replace_tags)

    # Set default dump options for CLI-friendly output
    default_dump_kwargs = {
        "sort_keys": False,
        "allow_unicode": True,
    }
    default_dump_kwargs.update(dump_kwargs)

    # Convert to YAML string using CloudFormation dumper
    result = dump_yaml(processed_data, **default_dump_kwargs)
    # When stream=None, dump_yaml always returns a string, never None
    assert result is not None
    return result
