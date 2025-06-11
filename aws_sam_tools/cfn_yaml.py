"""Core YAML parsing module with CloudFormation intrinsic function support.

This module provides a custom YAML loader and dumper that can parse and serialize
CloudFormation templates with their intrinsic function tags (like !Ref, !GetAtt, !Sub)
which standard YAML parsers cannot handle properly.

The module includes:
- CloudFormationTag base class and specific tag implementations
- Constructor functions for each CloudFormation intrinsic function
- CloudFormationLoader - custom YAML loader
- CloudFormationDumper - custom YAML dumper
- Main API functions for loading and dumping YAML files and strings

Supported CloudFormation Tags:
- !Ref: Reference to parameters, resources, or pseudo parameters
- !GetAtt: Get attribute from a resource
- !Sub: String substitution with variables
- !Join: Join values with a delimiter
- !Split: Split a string into an array
- !Select: Select an element from an array
- !FindInMap: Find value in a mapping
- !Base64: Base64 encode a value
- !Cidr: Generate CIDR blocks
- !ImportValue: Import value from another stack
- !GetAZs: Get availability zones
- !Transform: Apply transforms
- Condition functions: !And, !Equals, !If, !Not, !Or, !Condition

Example:
    >>> from aws_sam_tools.cfn_yaml import load_yaml_file, dump_yaml
    >>> template = load_yaml_file('template.yaml')
    >>> print(template['Resources']['MyBucket']['Properties']['BucketName'])
    RefTag('MyBucketName')
    >>> yaml_string = dump_yaml(template)
    >>> print(yaml_string)
"""

from typing import Any, Dict, Optional

import yaml


def get_node_type_name(node: yaml.Node) -> str:
    """Get a human-readable type name for a YAML node."""
    if isinstance(node, yaml.ScalarNode):
        return "scalar"
    elif isinstance(node, yaml.SequenceNode):
        return "sequence"
    elif isinstance(node, yaml.MappingNode):
        return "mapping"
    else:
        return "unknown"


class CloudFormationTag:
    """Base class for all CloudFormation intrinsic function tags.

    This class provides the common interface for all CloudFormation tag types.
    Each tag preserves the original CloudFormation syntax when loaded from YAML.

    Attributes:
        value: The value contained within the tag

    Example:
        >>> tag = RefTag('MyParameter')
        >>> print(tag.value)
        'MyParameter'
    """

    def __init__(self, value: Any):
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.value == other.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.value)})"

    @classmethod
    def yaml_representer(cls, dumper: "CloudFormationDumper", data: "CloudFormationTag") -> yaml.Node:
        """Base YAML representer for CloudFormation tags."""
        # Get the tag name without 'Tag' suffix from the data object's class
        tag_name = data.__class__.__name__[:-3] if data.__class__.__name__.endswith("Tag") else data.__class__.__name__
        yaml_tag = f"!{tag_name}"

        # Handle different value types
        if isinstance(data.value, str):
            return dumper.represent_scalar(yaml_tag, data.value, style="")
        elif isinstance(data.value, list):
            return dumper.represent_sequence(yaml_tag, data.value)
        elif isinstance(data.value, dict):
            return dumper.represent_mapping(yaml_tag, data.value)
        else:
            return dumper.represent_scalar(yaml_tag, str(data.value), style="")


class RefTag(CloudFormationTag):
    """Represents the !Ref CloudFormation intrinsic function.

    The !Ref intrinsic function returns the value of the specified parameter
    or resource. When you specify a parameter's logical name, it returns the
    value of the parameter. When you specify a resource's logical name, it
    typically returns a value that you can typically use to refer to that resource.

    Example YAML:
        BucketName: !Ref MyBucket

    Example:
        >>> ref = RefTag('MyBucket')
        >>> print(ref.value)
        'MyBucket'
    """

    pass


class GetAttTag(CloudFormationTag):
    """Represents the !GetAtt CloudFormation intrinsic function.

    The !GetAtt intrinsic function returns the value of an attribute from a
    resource in the template. The value can be either a list [LogicalName, AttributeName]
    or a string "LogicalName.AttributeName".

    Example YAML:
        DomainName: !GetAtt MyBucket.DomainName
        # or
        DomainName: !GetAtt [MyBucket, DomainName]

    Example:
        >>> getatt = GetAttTag(['MyBucket', 'DomainName'])
        >>> print(getatt.value)
        ['MyBucket', 'DomainName']
    """

    @classmethod
    def yaml_representer(cls, dumper: "CloudFormationDumper", data: "CloudFormationTag") -> yaml.Node:
        """Custom YAML representer for !GetAtt tag."""
        # Convert list format back to dot notation when dumping
        if isinstance(data.value, list) and len(data.value) == 2:
            scalar_value = f"{data.value[0]}.{data.value[1]}"
            return dumper.represent_scalar("!GetAtt", scalar_value, style="")
        else:
            return super().yaml_representer(dumper, data)


class SubTag(CloudFormationTag):
    """Represents the !Sub CloudFormation intrinsic function.

    The !Sub intrinsic function substitutes variables in an input string with
    values that you specify. The value can be either a string or a list containing
    the string and a mapping of variables.

    Example YAML:
        Description: !Sub 'Stack ${AWS::StackName} in ${AWS::Region}'
        # or
        Description: !Sub
          - 'Instance ${Instance} in ${Region}'
          - Instance: !Ref MyInstance
            Region: !Ref 'AWS::Region'

    Example:
        >>> sub = SubTag(['Hello ${Name}', {'Name': 'World'}])
        >>> print(sub.value)
        ['Hello ${Name}', {'Name': 'World'}]
    """

    @classmethod
    def yaml_representer(cls, dumper: "CloudFormationDumper", data: "CloudFormationTag") -> yaml.Node:
        """Custom YAML representer for !Sub tag."""
        # Handle single string case - unwrap from list
        if isinstance(data.value, list) and len(data.value) == 1:
            return dumper.represent_scalar("!Sub", data.value[0], style="")
        else:
            return super().yaml_representer(dumper, data)


class JoinTag(CloudFormationTag):
    """Represents !Join tag."""

    pass


class SplitTag(CloudFormationTag):
    """Represents !Split tag."""

    pass


class SelectTag(CloudFormationTag):
    """Represents !Select tag."""

    pass


class FindInMapTag(CloudFormationTag):
    """Represents !FindInMap tag."""

    pass


class Base64Tag(CloudFormationTag):
    """Represents !Base64 tag."""

    pass


class CidrTag(CloudFormationTag):
    """Represents !Cidr tag."""

    pass


class ImportValueTag(CloudFormationTag):
    """Represents !ImportValue tag."""

    pass


class GetAZsTag(CloudFormationTag):
    """Represents !GetAZs tag."""

    pass


class TransformTag(CloudFormationTag):
    """Represents !Transform tag."""

    pass


class AndTag(CloudFormationTag):
    """Represents !And tag."""

    pass


class EqualsTag(CloudFormationTag):
    """Represents !Equals tag."""

    pass


class IfTag(CloudFormationTag):
    """Represents !If tag."""

    pass


class NotTag(CloudFormationTag):
    """Represents !Not tag."""

    pass


class OrTag(CloudFormationTag):
    """Represents !Or tag."""

    pass


class ConditionTag(CloudFormationTag):
    """Represents !Condition tag."""

    pass


def construct_ref(loader: yaml.Loader, node: yaml.Node) -> RefTag:
    """Construct !Ref tag."""
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a scalar node, but found %s" % get_node_type_name(node), node.start_mark)
    value = loader.construct_scalar(node)
    if value is None or value == "":
        raise yaml.constructor.ConstructorError(None, None, "!Ref tag must not be empty", node.start_mark)
    return RefTag(value)


def construct_get_att(loader: yaml.Loader, node: yaml.Node) -> GetAttTag:
    """Construct !GetAtt tag."""
    if isinstance(node, yaml.ScalarNode):
        # Support dot notation: !GetAtt MyResource.MyAttribute
        value = loader.construct_scalar(node)
        if "." not in value:
            raise yaml.constructor.ConstructorError(None, None, "!GetAtt scalar must contain a dot (e.g., Resource.Attribute)", node.start_mark)
        # Split only on the first dot to handle attributes with dots
        parts = value.split(".", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise yaml.constructor.ConstructorError(None, None, "!GetAtt scalar must be in format Resource.Attribute", node.start_mark)
        return GetAttTag(parts)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
        if len(value) != 2:
            raise yaml.constructor.ConstructorError(None, None, "expected 2 items in sequence, but found %d" % len(value), node.start_mark)
        return GetAttTag(value)
    else:
        raise yaml.constructor.ConstructorError(None, None, "expected a scalar or sequence node, but found %s" % get_node_type_name(node), node.start_mark)


def construct_sub(loader: yaml.Loader, node: yaml.Node) -> SubTag:
    """Construct !Sub tag."""
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
        if value is None or value == "":
            raise yaml.constructor.ConstructorError(None, None, "!Sub tag must not be empty", node.start_mark)
        return SubTag([value])
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
        if len(value) != 2:
            raise yaml.constructor.ConstructorError(None, None, "expected 2 items in sequence, but found %d" % len(value), node.start_mark)
        return SubTag(value)
    else:
        raise yaml.constructor.ConstructorError(None, None, "expected a scalar or sequence node, but found %s" % get_node_type_name(node), node.start_mark)


def construct_join(loader: yaml.Loader, node: yaml.Node) -> JoinTag:
    """Construct !Join tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a sequence node, but found %s" % get_node_type_name(node), node.start_mark)
    value = loader.construct_sequence(node)
    if len(value) != 2:
        raise yaml.constructor.ConstructorError(None, None, "expected 2 items in sequence, but found %d" % len(value), node.start_mark)
    return JoinTag(value)


def construct_split(loader: yaml.Loader, node: yaml.Node) -> SplitTag:
    """Construct !Split tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a sequence node, but found %s" % get_node_type_name(node), node.start_mark)
    value = loader.construct_sequence(node)
    if len(value) != 2:
        raise yaml.constructor.ConstructorError(None, None, "expected 2 items in sequence, but found %d" % len(value), node.start_mark)
    return SplitTag(value)


def construct_select(loader: yaml.Loader, node: yaml.Node) -> SelectTag:
    """Construct !Select tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a sequence node, but found %s" % get_node_type_name(node), node.start_mark)
    value = loader.construct_sequence(node)
    if len(value) != 2:
        raise yaml.constructor.ConstructorError(None, None, "expected 2 items in sequence, but found %d" % len(value), node.start_mark)
    if not isinstance(value[0], int):
        raise yaml.constructor.ConstructorError(None, None, "expected an integer index, but found %s" % type(value[0]).__name__, node.start_mark)
    return SelectTag(value)


def construct_find_in_map(loader: yaml.Loader, node: yaml.Node) -> FindInMapTag:
    """Construct !FindInMap tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a sequence node, but found %s" % get_node_type_name(node), node.start_mark)
    value = loader.construct_sequence(node)
    if len(value) != 3:
        raise yaml.constructor.ConstructorError(None, None, "expected 3 items in sequence, but found %d" % len(value), node.start_mark)
    return FindInMapTag(value)


def construct_base64(loader: yaml.Loader, node: yaml.Node) -> Base64Tag:
    """Construct !Base64 tag."""
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a scalar node, but found %s" % get_node_type_name(node), node.start_mark)
    return Base64Tag(loader.construct_scalar(node))


def construct_cidr(loader: yaml.Loader, node: yaml.Node) -> CidrTag:
    """Construct !Cidr tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a sequence node, but found %s" % get_node_type_name(node), node.start_mark)
    value = loader.construct_sequence(node)
    if len(value) != 3:
        raise yaml.constructor.ConstructorError(None, None, "expected 3 items in sequence, but found %d" % len(value), node.start_mark)
    return CidrTag(value)


def construct_import_value(loader: yaml.Loader, node: yaml.Node) -> ImportValueTag:
    """Construct !ImportValue tag."""
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a scalar node, but found %s" % get_node_type_name(node), node.start_mark)
    return ImportValueTag(loader.construct_scalar(node))


def construct_get_azs(loader: yaml.Loader, node: yaml.Node) -> GetAZsTag:
    """Construct !GetAZs tag."""
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a scalar node, but found %s" % get_node_type_name(node), node.start_mark)
    return GetAZsTag(loader.construct_scalar(node))


def construct_transform(loader: yaml.Loader, node: yaml.Node) -> TransformTag:
    """Construct !Transform tag."""
    if not isinstance(node, yaml.MappingNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a mapping node, but found %s" % get_node_type_name(node), node.start_mark)
    return TransformTag(loader.construct_mapping(node))


def construct_and(loader: yaml.Loader, node: yaml.Node) -> AndTag:
    """Construct !And tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a sequence node, but found %s" % get_node_type_name(node), node.start_mark)
    values = loader.construct_sequence(node)
    if len(values) < 2 or len(values) > 10:
        raise yaml.constructor.ConstructorError(None, None, "!And must have between 2 and 10 conditions", node.start_mark)
    return AndTag(values)


def construct_equals(loader: yaml.Loader, node: yaml.Node) -> EqualsTag:
    """Construct !Equals tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a sequence node, but found %s" % get_node_type_name(node), node.start_mark)
    values = loader.construct_sequence(node)
    if len(values) != 2:
        raise yaml.constructor.ConstructorError(None, None, "expected 2 items in sequence, but found %d" % len(values), node.start_mark)
    return EqualsTag(values)


def construct_if(loader: yaml.Loader, node: yaml.Node) -> IfTag:
    """Construct !If tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a sequence node, but found %s" % get_node_type_name(node), node.start_mark)
    values = loader.construct_sequence(node)
    if len(values) != 3:
        raise yaml.constructor.ConstructorError(None, None, "expected 3 items in sequence (condition, true_value, false_value), but found %d" % len(values), node.start_mark)
    return IfTag(values)


def construct_not(loader: yaml.Loader, node: yaml.Node) -> NotTag:
    """Construct !Not tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a sequence node, but found %s" % get_node_type_name(node), node.start_mark)
    values = loader.construct_sequence(node)
    if len(values) != 1:
        raise yaml.constructor.ConstructorError(None, None, "expected 1 item in sequence, but found %d" % len(values), node.start_mark)
    return NotTag(values)


def construct_or(loader: yaml.Loader, node: yaml.Node) -> OrTag:
    """Construct !Or tag."""
    if not isinstance(node, yaml.SequenceNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a sequence node, but found %s" % get_node_type_name(node), node.start_mark)
    values = loader.construct_sequence(node)
    if len(values) < 2 or len(values) > 10:
        raise yaml.constructor.ConstructorError(None, None, "!Or must have between 2 and 10 conditions", node.start_mark)
    return OrTag(values)


def construct_condition(loader: yaml.Loader, node: yaml.Node) -> ConditionTag:
    """Construct !Condition tag."""
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a scalar node, but found %s" % get_node_type_name(node), node.start_mark)
    value = loader.construct_scalar(node)
    if not value:
        raise yaml.constructor.ConstructorError(None, None, "!Condition must specify a condition name", node.start_mark)
    return ConditionTag(value)


class CloudFormationLoader(yaml.SafeLoader):
    """Custom YAML loader that supports CloudFormation intrinsic function tags.

    This loader extends PyYAML's SafeLoader to handle CloudFormation-specific
    tags that are not supported by standard YAML parsers. It registers constructors
    for all CloudFormation intrinsic functions and validates their syntax according
    to AWS CloudFormation specifications.

    The loader preserves the original CloudFormation syntax by creating tag objects
    instead of immediately evaluating the intrinsic functions.

    Example:
        >>> import yaml
        >>> from aws_sam_tools.cfn_yaml import CloudFormationLoader
        >>> yaml_content = "BucketName: !Ref MyBucket"
        >>> result = yaml.load(yaml_content, Loader=CloudFormationLoader)
        >>> print(type(result['BucketName']))
        <class 'aws_sam_tools.cfn_yaml.RefTag'>
    """

    pass


# Register CloudFormation tags
CloudFormationLoader.add_constructor("!Ref", construct_ref)
CloudFormationLoader.add_constructor("!GetAtt", construct_get_att)
CloudFormationLoader.add_constructor("!Sub", construct_sub)
CloudFormationLoader.add_constructor("!Join", construct_join)
CloudFormationLoader.add_constructor("!Split", construct_split)
CloudFormationLoader.add_constructor("!Select", construct_select)
CloudFormationLoader.add_constructor("!FindInMap", construct_find_in_map)
CloudFormationLoader.add_constructor("!Base64", construct_base64)
CloudFormationLoader.add_constructor("!Cidr", construct_cidr)
CloudFormationLoader.add_constructor("!ImportValue", construct_import_value)
CloudFormationLoader.add_constructor("!GetAZs", construct_get_azs)
CloudFormationLoader.add_constructor("!Transform", construct_transform)
CloudFormationLoader.add_constructor("!And", construct_and)
CloudFormationLoader.add_constructor("!Equals", construct_equals)
CloudFormationLoader.add_constructor("!If", construct_if)
CloudFormationLoader.add_constructor("!Not", construct_not)
CloudFormationLoader.add_constructor("!Or", construct_or)
CloudFormationLoader.add_constructor("!Condition", construct_condition)


class CloudFormationDumper(yaml.SafeDumper):
    """Custom YAML dumper that supports CloudFormation intrinsic function tags.

    This dumper extends PyYAML's SafeDumper to handle CloudFormation-specific
    tags and properly serialize CloudFormationTag objects back to their original
    YAML format.

    Example:
        >>> import yaml
        >>> from aws_sam_tools.cfn_yaml import CloudFormationDumper, RefTag
        >>> data = {'BucketName': RefTag('MyBucket')}
        >>> yaml.dump(data, Dumper=CloudFormationDumper)
        'BucketName: !Ref MyBucket\\n'
    """

    def write_literal(self, text):
        return super().write_literal(text)

    def choose_scalar_style(self) -> str:
        """Override scalar style choice to avoid quoting CloudFormation tag values."""
        # Get the default style
        style = super().choose_scalar_style()

        # For tagged scalars that look like CloudFormation values, prefer plain style
        if self.event and hasattr(self.event, "tag") and hasattr(self.event, "value") and getattr(self.event, "tag", None) and getattr(self.event, "tag", "").startswith("!"):
            value = getattr(self.event, "value", None)
            # Check if the value can be safely represented without quotes
            if value and isinstance(value, str):
                # Allow alphanumeric, spaces, common CloudFormation characters
                # Special handling for CloudFormation pseudo parameters and resource types with ::
                # Avoid single colons but allow double colons (::)
                has_single_colon = ":" in value.replace("::", "")
                if (
                    not any(char in value for char in ["\n", "\t", '"', "'", "\\", "#"])
                    and not has_single_colon
                    and not value.startswith("-")
                    and not value.startswith(" ")
                    and not value.endswith(" ")
                    and not value.strip() == ""
                    and value != ""
                ):
                    return ""  # Plain style (empty string means plain style in PyYAML)

        return style


# Register CloudFormation tag representers
CloudFormationDumper.add_representer(RefTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(GetAttTag, GetAttTag.yaml_representer)
CloudFormationDumper.add_representer(SubTag, SubTag.yaml_representer)
CloudFormationDumper.add_representer(JoinTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(SplitTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(SelectTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(FindInMapTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(Base64Tag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(CidrTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(ImportValueTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(GetAZsTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(TransformTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(AndTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(EqualsTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(IfTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(NotTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(OrTag, CloudFormationTag.yaml_representer)
CloudFormationDumper.add_representer(ConditionTag, CloudFormationTag.yaml_representer)


def dump_yaml(data: Dict[str, Any], stream=None, **kwargs) -> Optional[str]:
    """
    Dump data to YAML with CloudFormation tag support.

    Args:
        data: Data to dump as YAML
        stream: Optional stream to write to. If None, returns string.
        **kwargs: Additional keyword arguments to pass to yaml.dump

    Returns:
        YAML string if stream is None, otherwise None
    """
    # Set default to maintain compatibility with existing behavior
    defaults = {
        "default_flow_style": False,
    }
    # Update with any user-provided kwargs
    defaults.update(kwargs)

    return yaml.dump(data, stream=stream, Dumper=CloudFormationDumper, **defaults)  # type: ignore


def load_yaml(stream: str) -> Dict[str, Any]:
    """
    Load YAML content with CloudFormation tag support.

    Args:
        stream: YAML content as string

    Returns:
        Dict containing the parsed YAML with CloudFormation tags
    """
    return yaml.load(stream, Loader=CloudFormationLoader)


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Load YAML file with CloudFormation tag support.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dict containing the parsed YAML with CloudFormation tags
    """
    with open(file_path, "r") as f:
        return yaml.load(f, Loader=CloudFormationLoader)
