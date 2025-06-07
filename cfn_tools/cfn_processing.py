import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from cfn_tools.cfn_yaml import CloudFormationLoader, CloudFormationTag, get_node_type_name, SubTag


class CFNToolsIncludeFileTag(CloudFormationTag):
    """Represents !CFNToolsIncludeFile tag."""

    pass


class CFNToolsToStringTag(CloudFormationTag):
    """Represents !CFNToolsToString tag."""

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


class CloudFormationProcessingLoader(CloudFormationLoader):
    """Extended YAML loader that supports CloudFormation tags and CFNTools processing tags."""

    pass


# Register the new processing tags
CloudFormationProcessingLoader.add_constructor("!CFNToolsIncludeFile", construct_cfntools_include_file)
CloudFormationProcessingLoader.add_constructor("!CFNToolsToString", construct_cfntools_to_string)


def load_yaml(stream: str, file_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load YAML content with CloudFormation and CFNTools processing tag support.

    Args:
        stream: YAML content as string
        file_name: Optional file name to resolve relative paths

    Returns:
        Dict containing the parsed YAML with all tags processed
    """
    loader = CloudFormationProcessingLoader(stream)
    if file_name:
        loader.name = file_name
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Load YAML file with CloudFormation and CFNTools processing tag support.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dict containing the parsed YAML with all tags processed
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return load_yaml(content, file_path)
