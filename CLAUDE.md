# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cfn-tools is a CloudFormation Tools package that provides utilities for working with AWS CloudFormation templates. The main functionality is a custom YAML parser that properly handles CloudFormation-specific tags (like `!Ref`, `!GetAtt`, `!Sub`) which standard YAML parsers struggle with.

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

1. **cfn_tools/cfn_yaml.py** - Heart of the package
   - `CloudFormationLoader`: Custom YAML loader extending `yaml.SafeLoader`
   - Tag classes for each CloudFormation intrinsic function (RefTag, GetAttTag, SubTag, etc.)
   - Main API: `load_yaml()` and `load_yaml_file()` functions
   - Each tag has a constructor function that validates the YAML node structure

2. **Tag System**
   - Each CloudFormation intrinsic function has its own tag class
   - Tags preserve the CloudFormation syntax when loaded
   - Constructor functions validate node types and content according to AWS specs
   - Tags: !Ref, !GetAtt, !Sub, !Join, !Split, !Select, !FindInMap, !Base64, !Cidr, !ImportValue, !GetAZs

### Testing Strategy

- Comprehensive test coverage in `tests/test_cfn.py`
- Test both valid and invalid YAML scenarios
- Test nested tags and edge cases
- When adding new features, add corresponding tests

### Build System

- Uses `uv` as package manager (modern Python packaging)
- Python 3.13+ required
- Dynamic versioning from git tags
- Configured for PyPI distribution

## Important Notes

- The CLI entry point (`cfn_tools.cli:cli`) is configured but the CLI module doesn't exist yet
- When modifying tag parsing, ensure error messages include YAML position info for debugging
- All CloudFormation tag constructors should validate input according to AWS documentation
- Use Ruff for formatting (200 char line length configured)