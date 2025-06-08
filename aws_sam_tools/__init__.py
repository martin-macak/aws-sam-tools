"""
AWS SAM Tools - A Python package for processing AWS CloudFormation and SAM templates.

This package provides utilities for working with AWS CloudFormation and SAM templates,
including a custom YAML parser that properly handles CloudFormation-specific
intrinsic function tags (like !Ref, !GetAtt, !Sub) and additional processing
capabilities for template manipulation.

Key Features:
    - Custom YAML loader supporting all CloudFormation intrinsic functions
    - Extended processing tags for advanced template manipulation
    - Command-line interface for template processing
    - OpenAPI specification processing with rule-based transformations

Main Modules:
    cfn_yaml: Core YAML parsing with CloudFormation tag support
    cfn_processing: Extended processing capabilities with CFNTools tags
    cli: Command-line interface
    openapi: OpenAPI specification processing

Example:
    >>> from aws_sam_tools import cfn_yaml
    >>> template = cfn_yaml.load_yaml_file('template.yaml')
    >>> print(template)
"""

from . import cfn_processing, cfn_yaml

__all__ = ["cfn_yaml", "cfn_processing"]
