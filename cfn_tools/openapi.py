"""OpenAPI specification processing module."""

import json
import yaml
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from enum import Enum
import copy


class OutputFormat(Enum):
    """Supported output formats."""

    JSON = "json"
    YAML = "yaml"
    DEFAULT = "default"


class NodeType(Enum):
    """Supported node types for rules."""

    PATH_METHOD = "path/method"


class Action(Enum):
    """Supported actions for rules."""

    DELETE = "delete"


class SafeNavigationDict:
    """Dictionary wrapper that supports safe dot notation navigation."""

    def __init__(self, data: Any):
        self._data = data

    def __getattr__(self, key: str) -> "SafeNavigationDict":
        """Safe attribute access that returns None for missing keys."""
        if isinstance(self._data, dict) and key in self._data:
            return SafeNavigationDict(self._data[key])
        elif isinstance(self._data, list):
            try:
                idx = int(key)
                if 0 <= idx < len(self._data):
                    return SafeNavigationDict(self._data[idx])
            except (ValueError, TypeError):
                pass
        return SafeNavigationDict(None)

    def __getitem__(self, key: Union[str, int]) -> "SafeNavigationDict":
        """Safe index access."""
        if isinstance(self._data, dict) and key in self._data:
            return SafeNavigationDict(self._data[key])
        elif isinstance(self._data, list):
            try:
                idx = int(key) if isinstance(key, str) else key
                if 0 <= idx < len(self._data):
                    return SafeNavigationDict(self._data[idx])
            except (ValueError, TypeError):
                pass
        return SafeNavigationDict(None)

    def __eq__(self, other: Any) -> bool:
        """Equality comparison for OpenAPI security."""
        if isinstance(other, SafeNavigationDict):
            return self._data == other._data

        # Special handling for security comparisons
        if isinstance(other, str) and isinstance(self._data, list):
            # Check if any security requirement matches the string
            for item in self._data:
                if isinstance(item, dict) and other in item:
                    return True
            return False

        return self._data == other

    def __ne__(self, other: Any) -> bool:
        """Inequality comparison."""
        # Handle None case specially for != comparison
        if self._data is None:
            return False
        return not self.__eq__(other)

    def __contains__(self, item: Any) -> bool:
        """Support 'in' operator."""
        if isinstance(self._data, (list, dict)):
            return item in self._data
        return False

    def __bool__(self) -> bool:
        """Boolean evaluation."""
        return self._data is not None and self._data != []

    def __repr__(self) -> str:
        """String representation."""
        return f"SafeNavigationDict({self._data!r})"

    @property
    def value(self) -> Any:
        """Get the underlying value."""
        return self._data


class RuleContext:
    """Context for safe rule evaluation."""

    def __init__(self, resource: Any, path: Optional[str] = None, method: Optional[str] = None):
        """Initialize rule context.

        Args:
            resource: The resource being evaluated (e.g., operation object)
            path: The path of the operation
            method: The HTTP method of the operation
        """
        self.resource = SafeNavigationDict(resource)
        self.path = path
        self.method = method

    def __getitem__(self, key: str) -> Any:
        """Allow context['key'] access."""
        return getattr(self, key, None)


class Rule:
    """Represents a processing rule."""

    def __init__(self, rule_string: str):
        """Parse rule from string format.

        Args:
            rule_string: Rule in format "node_type : action : filter_expression"
        """
        parts = [p.strip() for p in rule_string.split(":", 2)]
        if len(parts) != 3:
            raise ValueError(f"Invalid rule format: {rule_string}")

        self.node_type = NodeType(parts[0])
        self.action = Action(parts[1])
        self.filter_expression = parts[2]

    def evaluate(self, context: RuleContext) -> bool:
        """Evaluate the filter expression in the given context.

        Args:
            context: The context for evaluation

        Returns:
            True if the rule matches, False otherwise
        """
        # Create a safe evaluation environment
        safe_globals = {
            "__builtins__": {
                "None": None,
                "True": True,
                "False": False,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "any": any,
                "all": all,
            }
        }

        # Add context variables
        safe_locals = {
            "resource": context.resource,
            "path": context.path,
            "method": context.method,
        }

        # Override is/is not comparisons for SafeNavigationDict
        def custom_eval(expr, globals, locals):
            # Replace 'is not None' with boolean check
            if "is not None" in expr:
                expr = expr.replace("is not None", ".__bool__()")
            if "is None" in expr:
                expr = expr.replace("is None", ".__bool__() == False")
            return eval(expr, globals, locals)

        try:
            result = bool(custom_eval(self.filter_expression, safe_globals, safe_locals))
            return result
        except Exception:
            return False


def detect_format(file_path: Optional[str], format_hint: Optional[OutputFormat] = None) -> OutputFormat:
    """Detect the format of the input file.

    Args:
        file_path: Path to the file or None for stdin
        format_hint: Format hint from command line

    Returns:
        Detected format
    """
    # If file path is provided, check extension
    if file_path and file_path != "-":
        path = Path(file_path)
        if path.suffix.lower() in [".yaml", ".yml"]:
            return OutputFormat.YAML
        elif path.suffix.lower() == ".json":
            return OutputFormat.JSON

    # Use format hint if provided
    if format_hint and format_hint != OutputFormat.DEFAULT:
        return format_hint

    # Default to YAML for now, actual detection will happen during loading
    return OutputFormat.YAML


def load_openapi_spec(content: str, format_hint: Optional[OutputFormat] = None) -> tuple[Dict[str, Any], OutputFormat]:
    """Load OpenAPI specification from string content.

    Args:
        content: The specification content
        format_hint: Format hint

    Returns:
        Tuple of (specification dict, detected format)
    """
    # Try JSON first if hint is JSON or no hint
    if format_hint != OutputFormat.YAML:
        try:
            spec = json.loads(content)
            return spec, OutputFormat.JSON
        except json.JSONDecodeError:
            if format_hint == OutputFormat.JSON:
                raise ValueError("Invalid JSON format")

    # Try YAML
    try:
        spec = yaml.safe_load(content)
        if spec is None:
            raise ValueError("Empty or invalid YAML content")
        return spec, OutputFormat.YAML
    except yaml.YAMLError as e:
        if format_hint == OutputFormat.YAML:
            raise ValueError(f"Invalid YAML format: {e}")
        raise ValueError("Unable to parse input as JSON or YAML")


def apply_rules(spec: Dict[str, Any], rules: List[Rule]) -> Dict[str, Any]:
    """Apply processing rules to the OpenAPI specification.

    Args:
        spec: The OpenAPI specification
        rules: List of rules to apply

    Returns:
        Processed specification
    """
    # Make a deep copy to avoid modifying the original
    spec = copy.deepcopy(spec)

    for rule in rules:
        if rule.node_type == NodeType.PATH_METHOD:
            # Process path/method rules
            paths = spec.get("paths", {})
            for path, path_item in list(paths.items()):
                if not isinstance(path_item, dict):
                    continue

                # Check each HTTP method
                for method in list(path_item.keys()):
                    if method in ["get", "post", "put", "delete", "patch", "head", "options", "trace"]:
                        operation = path_item[method]
                        context = RuleContext(operation, path, method)

                        if rule.evaluate(context):
                            if rule.action == Action.DELETE:
                                del path_item[method]

                # Remove empty paths
                if not any(method in path_item for method in ["get", "post", "put", "delete", "patch", "head", "options", "trace"]):
                    del paths[path]

    return spec


def process_openapi(input_content: str, rules: List[str], input_format: Optional[OutputFormat] = None, output_format: Optional[OutputFormat] = None) -> str:
    """Process OpenAPI specification with given rules.

    Args:
        input_content: The input specification content
        rules: List of rule strings
        input_format: Input format hint
        output_format: Desired output format

    Returns:
        Processed specification as string
    """
    # Parse rules
    parsed_rules = [Rule(rule) for rule in rules]

    # Load specification
    spec, detected_format = load_openapi_spec(input_content, input_format)

    # Apply rules
    processed_spec = apply_rules(spec, parsed_rules)

    # Determine output format
    if output_format == OutputFormat.DEFAULT or output_format is None:
        output_format = detected_format

    # Serialize output
    if output_format == OutputFormat.JSON:
        return json.dumps(processed_spec, indent=2)
    else:  # YAML
        return yaml.dump(processed_spec, default_flow_style=False, sort_keys=False)
