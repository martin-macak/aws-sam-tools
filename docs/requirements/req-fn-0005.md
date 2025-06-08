# REQ-FN-0005 - OpenAPI processing

This adds support for processing OpenAPI specification files for AWS API Gateway.
Processing supports variuous rules that can be applied to the parts of the specification.

New command is `openapi`.
The processing is done by `cfn-tools openapi process` subcommand.

## Processing Command

The command accepts following parameters:

- `--rule` - the rule to apply to the specification. Multiple rules can be specified by repeating the parameter.
- `--input` - the input file to process. If the input is `-` then the specification is read from the standard input. Default is `-`.
- `--output` - the output file to write the processed specification to. If the output is `-` then the specification is written to the standard output. Default is `-`.
- `--format` - the format of the output specification. It is an enumeration of supported formats. Supported formats are:
  - `json` - the output is written in JSON format.
  - `yaml` - the output is written in YAML format.
  - `default` - the output is written in the same format as the input. Default is `default`.

The processing command tris to detect the format of the input specification by the file extension.
When the file name is specified, it uses the file extension to detect the format. 
For yaml files it uses `yaml` or `yml` extension.
For json files it uses `json` extension.
If the file extension is not specified, it uses the `--format` parameter to detect the format.
If the format is not specified, it first tries to load the specification as JSON and if it fails, it tries to load the specification as YAML. If both fail, it fails with an error.
The output format is by default the same as the input format.

## Processing Rules

Rules are set by `--rule` parameter. Multiple rules can be specified by repeating the parameter.

### Rule Syntax

Rule syntax is:
```
<node_type> : <action> : <filter_expression>
```

- **node_type** - the type of the node to apply the rule to. It is an enumeration of supported node types.
  - `path/method` - the rule applies to all HTTP methods of a path.
- **action** - the action to take when the rule matches. It is an enumeration of supported actions.
  - `delete` - this action removes the node from the parent node.
- **filter_expression** - the filter expression used to determine if the rule matches. The filter is a python expression.

The rule finds all nodes that match the node type and then applies the filter expression to the node.
If the filter expression evaluates to `True` then the action is applied to the node.

Example:
```
path/method : delete : resource.security is not None and resource.security != 'auth'
```
This rule removes all operations that have a security scheme set and it is not `auth`.

## Acceptance Criteria

- `cfn-tools openapi process` command is implemented.
- processing is performed without changing the original specification.
- the command supports input and output in JSON and YAML formats.
- the command supports multiple rules.
- the command supports filter expressions.
- the command supports an automatic detection of the input format
  - first it tries to check if an extension matches supported formats
    - `yaml` or `yml` extension is YAML
    - `json` extension is JSON
  - if the extension is not specified, it uses the `--format` parameter to detect the format.
  - if the format is not specified, it first tries to load the specification as JSON and if it fails, it tries to load the specification as YAML. If both fail, it fails with an error.

## Implementation Notes

- use `pyyaml` library to load and dump YAML files.
- use `json` library to load and dump JSON files.
- use `cfn_tools.openapi` module to process the OpenAPI specification. 
- check the `cfn_tools.openapi` module for the implementation details.
- don't put any logic into click command implementation. use `cfn_tools.openapi` module to implement the processing logic.
- the rules are evaluated as python
- python evaluation is done in safe and isolated mode
- python evaluation uses context to isolate the evaluation
- the context is defined in `cfn_tools.openapi.RuleContext` class
- the context supports safe dot notation navigation that does not fail for non-existing keys or None values or indexes out of range

## Test scenarios

### Remove all operations that have a security scheme set and it is not `auth`

Input:
```yaml
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /do-not-delete:
    get:
      summary: Test operation
  /do-not-delete-as-well:
    get:
      summary: Test operation
      security:
        - auth: []
  /delete-me:
    get:
      summary: Test operation
      security:
        - api_key: []
```

Command:
```
cfn-tools openapi process --rule "path/method : delete : resource.security is not None and resource.security != 'auth'" --input - --output - --format yaml
```

Output:
```yaml
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /do-not-delete:
    get:
      summary: Test operation
  /do-not-delete-as-well:
    get:
      summary: Test operation
      security:
        - auth: []
```
