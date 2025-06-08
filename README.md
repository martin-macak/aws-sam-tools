# AWS SAM Tools

[![CI](https://github.com/martin-macak/aws-sam-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/martin-macak/aws-sam-tools/actions/workflows/ci.yml)
[![Test Build](https://github.com/martin-macak/aws-sam-tools/actions/workflows/test-build.yml/badge.svg)](https://github.com/martin-macak/aws-sam-tools/actions/workflows/test-build.yml)
[![PyPI version](https://badge.fury.io/py/aws-sam-tools.svg)](https://badge.fury.io/py/aws-sam-tools)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

A comprehensive Python package for processing AWS CloudFormation templates with advanced YAML parsing capabilities and extended processing features.

## Overview

aws-sam-tools provides utilities for working with AWS CloudFormation templates, including a custom YAML parser that properly handles CloudFormation-specific intrinsic function tags (like `!Ref`, `!GetAtt`, `!Sub`) which standard YAML parsers cannot handle correctly. The package also includes extended processing capabilities for advanced template manipulation and an OpenAPI specification processor.

## Key Features

### 🔧 CloudFormation YAML Processing
- **Custom YAML Loader**: Properly parses all CloudFormation intrinsic function tags
- **Tag Preservation**: Maintains CloudFormation syntax while enabling programmatic access
- **Validation**: Built-in validation for CloudFormation tag syntax according to AWS specifications
- **Error Handling**: Detailed error messages with YAML position information

### ⚡ Extended Processing Capabilities
- **File Inclusion**: Include content from external files (`!CFNToolsIncludeFile`)
- **String Conversion**: Convert data structures to JSON/YAML strings (`!CFNToolsToString`)
- **UUID Generation**: Generate unique identifiers (`!CFNToolsUUID`)
- **Version Stamping**: Include git version information (`!CFNToolsVersion`)
- **Timestamp Generation**: Add timestamps with formatting options (`!CFNToolsTimestamp`)
- **Checksum Calculation**: Calculate hashes of data or files (`!CFNToolsCRC`)

### 🌐 OpenAPI Processing
- **Rule-Based Transformations**: Filter and modify OpenAPI specifications
- **Flexible Expressions**: Use Python expressions for complex filtering logic
- **Multiple Formats**: Support for both JSON and YAML OpenAPI specifications

### 🖥️ Command Line Interface
- **Template Processing**: Process CloudFormation templates from command line
- **OpenAPI Processing**: Apply transformations to OpenAPI specifications
- **Format Conversion**: Convert between different output formats
- **Integration Ready**: Easy integration into build pipelines and CI/CD workflows

## Supported CloudFormation Tags

The package supports all standard CloudFormation intrinsic functions:

| Tag            | Description                       | Example                                                    |
| -------------- | --------------------------------- | ---------------------------------------------------------- |
| `!Ref`         | Reference parameters or resources | `!Ref MyBucket`                                            |
| `!GetAtt`      | Get resource attributes           | `!GetAtt MyBucket.DomainName`                              |
| `!Sub`         | String substitution               | `!Sub 'Hello ${Name}'`                                     |
| `!Join`        | Join values with delimiter        | `!Join [',', [a, b, c]]`                                   |
| `!Split`       | Split string into array           | `!Split [',', 'a,b,c']`                                    |
| `!Select`      | Select from array                 | `!Select [0, !GetAZs '']`                                  |
| `!FindInMap`   | Find value in mapping             | `!FindInMap [RegionMap, !Ref 'AWS::Region', AMI]`          |
| `!Base64`      | Base64 encode                     | `!Base64 'Hello World'`                                    |
| `!Cidr`        | Generate CIDR blocks              | `!Cidr ['10.0.0.0/16', 6, 8]`                              |
| `!ImportValue` | Import from another stack         | `!ImportValue SharedVPC`                                   |
| `!GetAZs`      | Get availability zones            | `!GetAZs 'us-east-1'`                                      |
| `!Transform`   | Apply transforms                  | `!Transform {'Name': 'AWS::Include', 'Parameters': {...}}` |

Plus all condition functions: `!And`, `!Equals`, `!If`, `!Not`, `!Or`, `!Condition`

## Installation

```bash
pip install aws-sam-tools
```

For development:
```bash
git clone https://github.com/yourusername/aws-sam-tools.git
cd aws-sam-tools
make init
```

## Quick Start

### Basic CloudFormation Template Processing

```python
from aws_sam_tools.cfn_yaml import load_yaml_file

# Load a CloudFormation template
template = load_yaml_file('template.yaml')

# Access CloudFormation tags as objects
bucket_name = template['Resources']['MyBucket']['Properties']['BucketName']
print(type(bucket_name))  # <class 'aws_sam_tools.cfn_yaml.RefTag'>
print(bucket_name.value)  # 'MyBucketParameter'
```

### Extended Processing with CFNTools Tags

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: !CFNToolsToString
  - Template built on: !CFNToolsTimestamp
    Version: !CFNToolsVersion
    ID: !CFNToolsUUID
  - ConvertTo: JSONString
    OneLine: true

Resources:
  UserDataScript: !CFNToolsIncludeFile scripts/setup.sh
  
  ConfigurationHash: !CFNToolsCRC
    - !CFNToolsIncludeFile config/app-config.json
    - Algorithm: sha256
      Encoding: hex
```

```python
from aws_sam_tools.cfn_processing import load_yaml_file

# Process template with CFNTools tags
template = load_yaml_file('template.yaml')

# CFNTools tags are resolved:
# - !CFNToolsTimestamp becomes actual timestamp
# - !CFNToolsUUID becomes generated UUID
# - !CFNToolsIncludeFile includes file content
# - !CFNToolsCRC calculates checksum
```

### Convert to AWS-Compatible Format

```python
from aws_sam_tools.cfn_processing import load_yaml_file
import yaml

# Load and convert CloudFormation tags to intrinsic functions
template = load_yaml_file('template.yaml', replace_tags=True)

# Output AWS-compatible YAML
aws_yaml = yaml.dump(template, default_flow_style=False)
print(aws_yaml)
# BucketName: 
#   Ref: MyBucketParameter
```

### Command Line Usage

Process CloudFormation templates:
```bash
# Process CFNTools tags and convert CloudFormation tags to intrinsic functions
aws-sam-tools template process --template template.yaml --output processed.yaml --replace-tags

# Process without converting CloudFormation tags
aws-sam-tools template process --template template.yaml --output processed.yaml
```

Process OpenAPI specifications:
```bash
# Remove operations without security requirements
aws-sam-tools openapi process \
  --rule "path/method : delete : resource.security == 'none'" \
  --input api.yaml \
  --output filtered-api.yaml

# Multiple rules
aws-sam-tools openapi process \
  --rule "path/method : delete : resource.security == 'none'" \
  --rule "path/method : delete : method == 'options'" \
  --input api.yaml
```

## CFNTools Processing Tags

### File Inclusion (`!CFNToolsIncludeFile`)

Include content from external files:

```yaml
# Include shell script
UserData: !CFNToolsIncludeFile scripts/userdata.sh

# Include JSON configuration  
Config: !CFNToolsIncludeFile config/app.json

# Include nested YAML with CFNTools support
NestedTemplate: !CFNToolsIncludeFile templates/nested.yaml
```

### String Conversion (`!CFNToolsToString`)

Convert data structures to strings:

```yaml
# Convert to JSON string
PolicyDocument: !CFNToolsToString
  - Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action: 's3:GetObject'
  - ConvertTo: JSONString
    OneLine: true

# Convert to YAML string
ConfigData: !CFNToolsToString
  - database:
      host: localhost
      port: 5432
  - ConvertTo: YAMLString
```

### Unique Identifiers (`!CFNToolsUUID`)

Generate UUIDs:

```yaml
Resources:
  MyResource:
    Properties:
      UniqueId: !CFNToolsUUID
```

### Version Information (`!CFNToolsVersion`)

Include git version:

```yaml
Parameters:
  Version:
    Type: String
    Default: !CFNToolsVersion

  PEP440Version:
    Type: String  
    Default: !CFNToolsVersion
      Style: pep440
```

### Timestamps (`!CFNToolsTimestamp`)

Generate timestamps:

```yaml
Parameters:
  BuildTime:
    Default: !CFNToolsTimestamp
    
  ExpiryTime:
    Default: !CFNToolsTimestamp
      Offset: 30
      OffsetUnit: days
      Format: '%Y-%m-%d'
```

### Checksums (`!CFNToolsCRC`)

Calculate hashes:

```yaml
Parameters:
  ConfigHash:
    Default: !CFNToolsCRC
      - !CFNToolsIncludeFile config.json
      - Algorithm: sha256
        Encoding: hex
        
  FileHash:
    Default: !CFNToolsCRC ["file://./setup.sh"]
```

## OpenAPI Processing

Process OpenAPI specifications with rule-based transformations:

```python
from aws_sam_tools.openapi import process_openapi

# Remove all operations without security
rules = ["path/method : delete : resource.security == 'none'"]
result = process_openapi(openapi_content, rules)

# Complex filtering
rules = [
    "path/method : delete : resource.security == 'none'",
    "path/method : delete : method == 'options'",
    "path/method : delete : path.startswith('/internal')"
]
result = process_openapi(openapi_content, rules)
```

## Development

### Requirements

- Python 3.13+
- uv (package manager)

### Setup

```bash
# Clone repository
git clone <repository-url>
cd aws-sam-tools

# Initialize development environment
make init

# Run tests
make test

# Type checking
make pyright

# Format code
make format

# Build package
make build
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test
uv run pytest tests/test_cfn.py::test_ref_tag -v

# Run with coverage
uv run pytest --cov=cfn_tools
```

## Architecture

### Core Components

1. **cfn_tools/cfn_yaml.py** - Core YAML parser with CloudFormation tag support
2. **cfn_tools/cfn_processing.py** - Extended processing with CFNTools tags  
3. **cfn_tools/cli.py** - Command line interface
4. **cfn_tools/openapi.py** - OpenAPI specification processing

### Design Principles

- **Tag Preservation**: CloudFormation tags are preserved as objects for programmatic access
- **Validation**: All tag constructors validate syntax according to AWS specifications
- **Error Handling**: Detailed error messages with YAML position information
- **Extensibility**: Easy to add new processing tags and capabilities

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`make test`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/martin-macak/aws-sam-tools/issues)
- 💬 [Discussions](https://github.com/martin-macak/aws-sam-tools/discussions)