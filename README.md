# AWS SAM Tools

[![CI](https://github.com/martin-macak/aws-sam-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/martin-macak/aws-sam-tools/actions/workflows/ci.yml)
[![Test Build](https://github.com/martin-macak/aws-sam-tools/actions/workflows/test-build.yml/badge.svg)](https://github.com/martin-macak/aws-sam-tools/actions/workflows/test-build.yml)
[![PyPI version](https://badge.fury.io/py/aws-sam-tools.svg)](https://badge.fury.io/py/aws-sam-tools)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

A powerful command-line tool for processing AWS CloudFormation templates with advanced template enhancement capabilities. Transform your infrastructure-as-code workflows with dynamic content inclusion, automated versioning, and intelligent template processing.

## ✨ Key Features

### 🔧 Advanced Template Processing
- **Dynamic File Inclusion**: Include external files directly into your templates
- **Automatic Versioning**: Inject git version information into your infrastructure
- **UUID Generation**: Generate unique identifiers for resources
- **Timestamp Injection**: Add build and deployment timestamps
- **Checksum Calculation**: Ensure configuration integrity with automated hashing
- **String Conversion**: Convert complex data structures to JSON/YAML strings

### 🌐 OpenAPI Specification Processing
- **Rule-Based Filtering**: Remove or modify API operations based on custom rules
- **Security-Based Filtering**: Filter endpoints by security requirements
- **Format Conversion**: Convert between JSON and YAML formats
- **Pipeline Integration**: Perfect for CI/CD automation

### ⚡ CloudFormation Compatibility
- **Native Tag Support**: Full support for all CloudFormation intrinsic functions
- **Tag Conversion**: Convert shorthand tags to AWS-compatible intrinsic functions
- **Template Validation**: Ensure your templates remain CloudFormation-compliant

## 🚀 Quick Start

### Installation

```bash
pip install aws-sam-tools
```

### Basic Usage

Process a CloudFormation template with enhanced capabilities:

```bash
# Process template with CFNTools enhancements
aws-sam-tools template process --template template.yaml --output processed.yaml

# Convert CloudFormation tags to intrinsic functions for AWS compatibility
aws-sam-tools template process --template template.yaml --output aws-compatible.yaml --replace-tags
```

## 📋 Command Reference

### Template Processing

```bash
aws-sam-tools template process [OPTIONS]
```

**Options:**
- `--template, -t PATH`: Input CloudFormation template (default: `template.yaml`)
- `--output, -o PATH`: Output file (default: stdout with `-`)
- `--replace-tags`: Convert CloudFormation tags to intrinsic functions

**Examples:**

```bash
# Basic processing
aws-sam-tools template process

# Specify input and output files
aws-sam-tools template process --template src/template.yaml --output dist/template.yaml

# Convert tags for AWS deployment
aws-sam-tools template process --template template.yaml --output aws-template.yaml --replace-tags

# Output to stdout for pipeline integration
aws-sam-tools template process --template template.yaml | aws cloudformation deploy ...
```

### OpenAPI Processing

```bash
aws-sam-tools openapi process [OPTIONS]
```

**Options:**
- `--input PATH`: Input OpenAPI specification (default: stdin with `-`)
- `--output PATH`: Output file (default: stdout with `-`)
- `--rule TEXT`: Processing rule (can be specified multiple times)
- `--format [json|yaml|default]`: Output format (default: same as input)

**Rule Syntax:**
```
<node_type> : <action> : <filter_expression>
```

**Examples:**

```bash
# Remove all operations without security requirements
aws-sam-tools openapi process \
  --rule "path/method : delete : resource.security == 'none'" \
  --input api.yaml \
  --output filtered-api.yaml

# Multiple filtering rules
aws-sam-tools openapi process \
  --rule "path/method : delete : resource.security == 'none'" \
  --rule "path/method : delete : method == 'options'" \
  --input api.yaml \
  --format json

# Remove internal endpoints
aws-sam-tools openapi process \
  --rule "path/method : delete : path.startswith('/internal')" \
  --input api.yaml
```

## 🏷️ CFNTools Processing Tags

Enhance your CloudFormation templates with powerful processing capabilities:

### File Inclusion (`!CFNToolsIncludeFile`)

Include content from external files into your templates:

```yaml
# Include shell script for EC2 UserData
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      UserData: !CFNToolsIncludeFile scripts/setup.sh

# Include JSON configuration
  AppConfig:
    Type: AWS::SSM::Parameter
    Properties:
      Value: !CFNToolsIncludeFile config/app-config.json

# Include nested CloudFormation template
  NestedStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateBody: !CFNToolsIncludeFile templates/nested.yaml
```

**Features:**
- Supports relative and absolute paths
- Automatically detects file format (JSON, YAML, text)
- Processes nested CloudFormation tags in included YAML files

### String Conversion (`!CFNToolsToString`)

Convert data structures to strings for various use cases:

```yaml
# Convert policy document to JSON string
Resources:
  MyRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument: !CFNToolsToString
        - Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Principal:
                Service: lambda.amazonaws.com
              Action: sts:AssumeRole
        - ConvertTo: JSONString
          OneLine: true

# Convert configuration to YAML string
  ConfigParameter:
    Type: AWS::SSM::Parameter
    Properties:
      Value: !CFNToolsToString
        - database:
            host: !Ref DatabaseHost
            port: 5432
            ssl: true
        - ConvertTo: YAMLString
```

**Options:**
- `ConvertTo`: `"JSONString"` (default) or `"YAMLString"`
- `OneLine`: `true` or `false` (default) - compress to single line

### UUID Generation (`!CFNToolsUUID`)

Generate unique identifiers for resources:

```yaml
Resources:
  S3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub
        - "my-app-${UniqueId}"
        - UniqueId: !CFNToolsUUID

  DeploymentId:
    Type: AWS::SSM::Parameter
    Properties:
      Name: /app/deployment-id
      Value: !CFNToolsUUID
```

### Version Information (`!CFNToolsVersion`)

Include git version information in your infrastructure:

```yaml
Parameters:
  AppVersion:
    Type: String
    Default: !CFNToolsVersion

  BuildVersion:
    Type: String
    Default: !CFNToolsVersion
      Style: pep440

Resources:
  VersionParameter:
    Type: AWS::SSM::Parameter
    Properties:
      Name: /app/version
      Value: !Ref AppVersion
```

**Options:**
- `Source`: `"Git"` (default) or `"Any"`
- `Style`: `"semver"` (default) or `"pep440"`

### Timestamp Generation (`!CFNToolsTimestamp`)

Add timestamps to track deployments and expiry:

```yaml
Parameters:
  DeploymentTime:
    Type: String
    Default: !CFNToolsTimestamp

  ExpiryDate:
    Type: String
    Default: !CFNToolsTimestamp
      Offset: 30
      OffsetUnit: days
      Format: '%Y-%m-%d'

Resources:
  DeploymentMetadata:
    Type: AWS::SSM::Parameter
    Properties:
      Name: /app/deployed-at
      Value: !CFNToolsTimestamp
        Format: '%Y-%m-%d %H:%M:%S UTC'
```

**Options:**
- `Format`: Python strftime format (default: ISO-8601 UTC)
- `Offset`: Integer offset from current time (default: 0)
- `OffsetUnit`: `"seconds"`, `"minutes"`, `"hours"`, `"days"`, `"weeks"`, `"months"`, `"years"`

### Checksum Calculation (`!CFNToolsCRC`)

Calculate checksums for configuration integrity:

```yaml
Resources:
  ConfigHash:
    Type: AWS::SSM::Parameter
    Properties:
      Name: /app/config-hash
      Value: !CFNToolsCRC
        - !CFNToolsIncludeFile config/production.json
        - Algorithm: sha256
          Encoding: hex

  ScriptIntegrity:
    Type: AWS::SSM::Parameter
    Properties:
      Value: !CFNToolsCRC
        - "file://scripts/deployment.sh"
        - Algorithm: md5
          Encoding: base64
```

**Options:**
- `Algorithm`: `"md5"`, `"sha1"`, `"sha256"` (default), `"sha512"`
- `Encoding`: `"hex"` (default) or `"base64"`

**Value Types:**
- String values are hashed directly
- Objects/arrays are converted to JSON before hashing
- `"file://path"` reads and hashes file content

## 🔄 Template Conversion

Convert between CloudFormation tag formats:

### Input Template (with shorthand tags):
```yaml
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketParameter
      Policy: !Sub |
        {
          "Statement": [{
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "${MyBucket}/*"
          }]
        }
```

### With `--replace-tags` (AWS-compatible):
```yaml
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName:
        Ref: BucketParameter
      Policy:
        Fn::Sub: |
          {
            "Statement": [{
              "Effect": "Allow", 
              "Principal": "*",
              "Action": "s3:GetObject",
              "Resource": "${MyBucket}/*"
            }]
          }
```

## 🛠️ Development Workflows

### CI/CD Pipeline Integration

```bash
# In your CI/CD pipeline
aws-sam-tools template process --template template.yaml --output processed.yaml --replace-tags
aws cloudformation deploy --template-file processed.yaml --stack-name my-stack
```

### Multi-Environment Deployments

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: !CFNToolsToString
  - Deployed: !CFNToolsTimestamp
    Version: !CFNToolsVersion
    Environment: !Ref Environment
  - ConvertTo: JSONString
    OneLine: true

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]

Resources:
  AppConfig:
    Type: AWS::SSM::Parameter
    Properties:
      Name: !Sub "/app/${Environment}/config"
      Value: !CFNToolsIncludeFile config/${Environment}.json
```

### Configuration Management

```yaml
# Ensure configuration changes trigger updates
Resources:
  LambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      Environment:
        Variables:
          CONFIG_HASH: !CFNToolsCRC
            - !CFNToolsIncludeFile config/lambda-config.json
          DEPLOYMENT_ID: !CFNToolsUUID
```

## 📖 Development

### Requirements
- Python 3.13+
- uv (package manager)

### Setup
```bash
git clone <repository-url>
cd aws-sam-tools
make init
make test
```

### Commands
```bash
make test      # Run all tests
make format    # Format code
make build     # Build package
make clean     # Clean artifacts
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/martin-macak/aws-sam-tools/issues)
- 💬 [Discussions](https://github.com/martin-macak/aws-sam-tools/discussions)