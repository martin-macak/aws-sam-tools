# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

aws-sam-tools is an AWS SAM Tools package that provides utilities for working with AWS CloudFormation and SAM templates. The main functionality is a custom YAML parser that properly handles CloudFormation-specific tags (like `!Ref`, `!GetAtt`, `!Sub`) which standard YAML parsers struggle with.

## Development Commands

```bash
make init      # Initialize development environment
make build     # Build the package
make test      # Run pytest tests
make pyright   # Run type checking
make format    # Format code with Ruff
make clean     # Clean build artifacts
```

To run a single test:
```bash
uv run pytest tests/test_cfn.py::test_function_name -v
```

## Code Architecture

### Core Components

1. **aws_sam_tools/cfn_yaml.py** - Heart of the package
   - `CloudFormationLoader`: Custom YAML loader extending `yaml.SafeLoader`
   - Tag classes for each CloudFormation intrinsic function (RefTag, GetAttTag, SubTag, etc.)
   - Main API: `load_yaml()` and `load_yaml_file()` functions
   - Each tag has a constructor function that validates the YAML node structure

2. **aws_sam_tools/cfn_processing.py** - Extended processing capabilities
   - `CloudFormationProcessingLoader`: Extends CloudFormationLoader with CFNTools tags
   - CFNTools processing tags: !CFNToolsIncludeFile, !CFNToolsToString, !CFNToolsUUID, !CFNToolsVersion, !CFNToolsTimestamp, !CFNToolsCRC
   - `replace_cloudformation_tags()`: Converts tag objects to AWS intrinsic function format
   - Enhanced `load_yaml()` and `load_yaml_file()` with processing support

3. **aws_sam_tools/cli.py** - Command line interface
   - `template process`: Process CloudFormation templates with CFNTools tags
   - `openapi process`: Process OpenAPI specifications with rule-based transformations
   - Support for --replace-tags option to convert CloudFormation tags to intrinsic functions

4. **aws_sam_tools/openapi.py** - OpenAPI specification processing
   - Rule-based processing with format "node_type : action : filter_expression"
   - `SafeNavigationDict`: Safe property access for rule evaluation
   - Support for path/method filtering and delete operations

### Tag System Architecture

- **Base Class**: `CloudFormationTag` provides common interface for all tags
- **Tag Preservation**: Tags maintain original CloudFormation syntax as objects
- **Validation**: Constructor functions validate YAML node structure per AWS specs
- **Two-Layer System**: 
  - Core CloudFormation tags (cfn_yaml.py) - preserve AWS syntax
  - Extended CFNTools tags (cfn_processing.py) - processed immediately during loading

### Testing Strategy

- Modular test structure with dedicated files:
  - `test_cfn.py`: Core CloudFormation tag parsing
  - `test_cfn_processing.py`: Extended processing functionality  
  - `test_cfn_processing_tags.py`: CFNTools tag behavior
  - `test_cli.py`: CLI template processing
  - `test_cli_openapi.py`: CLI OpenAPI processing
  - `test_openapi.py`: OpenAPI rule engine
- Test both valid and invalid scenarios with comprehensive error checking
- CLI tests use filesystem fixtures and output validation

### Build System

- Uses `uv` as package manager (modern Python packaging)
- Python 3.13+ required
- Dynamic versioning from git tags using dunamai
- CLI entry point: `aws-sam-tools = "aws_sam_tools.cli:cli"`
- Configured for PyPI distribution

## Important Notes

- When modifying tag parsing, ensure error messages include YAML position info for debugging
- All CloudFormation tag constructors should validate input according to AWS documentation
- Use Ruff for formatting (200 char line length configured)
- CFNTools tags are processed during YAML loading, CloudFormation tags preserved as objects
- The `replace_tags=True` option converts CloudFormation tag objects to AWS-compatible intrinsic functions