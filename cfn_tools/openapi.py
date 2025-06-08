from copy import deepcopy
from dataclasses import dataclass
from enum import Enum


class OpenAPINodeType(Enum):
    HttpMethod = "path/method"


class ProcessorAction(Enum):
    Delete = "delete"


@dataclass
class ProcessorRule:
    """
    Processor rule.

    Attributes:
        type: The type of OpenAPI node this rule applies to
        action: The action to take when the rule matches
        filter_expression: The filter expression used to determine if the rule matches. The filter is a python expression.
    """

    type: OpenAPINodeType
    action: str
    filter_expression: str


class RuleContext:
    """
    Rule context.
    This captures the parent node and the current node.
    TODO: Implement this class by following the requirements:
    This class must also work as a dict-wrapper, so it can be used to navigate through values using dot notation.
    For example: context.node.subnode[0] must navigate to self.node['subnode'][0].
    Also it must return null if the value is not found and it also must not failt for non-existing keys, even in deep navigation.
    Foe example: context.node.subnode.value must return null if subnode is not found.

    Attributes:
        parent_node: The parent node of the current node
        node: The current node
        parent_locator: The locator of the parent node. It's str if the parent is a dict (name of the key), int if the parent is a list (index of the item)
    """

    def __init__(
        self,
        parent_node: dict | list,
        node: dict | list,
        parent_locator: str | int,
    ):
        self.parent_node = parent_node
        self.node = node
        self.parent_locator = parent_locator


class OpenAPIProcessor:
    """
    OpenAPI processor.

    TODO: Implement the processing logic.
    """

    def __init__(
        self,
        openapi_spec: dict,
        rules: list[ProcessorRule] | None = None,
    ):
        self.openapi_spec = openapi_spec
        self.rules = rules or []

    def add_rule(self, rule: ProcessorRule) -> "OpenAPIProcessor":
        self.rules.append(rule)
        return self

    def process(self) -> dict:
        modified_spec = deepcopy(self.openapi_spec)
        # TODO: Implement the processing logic
        return modified_spec
