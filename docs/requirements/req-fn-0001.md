# REQ-FN-0001 - Basic processing tags for CloudFormation yaml

New class with custom CloudFormation yaml processing.

## Acceptance Criteria

### !CFNToolsIncludeFile

`!CFNToolsIncludeFile` is new processing tag that loads a file from the local file system. This tag supports optional parameters that allow additional processing of the file.

Parameters:
- **FilePath** : str - mandatory positional parameter, this is the path to the file. When the relative path is used then the path starts from the yaml file that contains this tag.

Example:
```yaml
!CFNToolsIncludeFile src/api/openapi.yaml
```

- this function respects the file mime type
- when the file is a structured data (yaml, json) then the file is appended as a valid yaml block

For example: 

```yaml
MyStack:
  Def: !CFNToolsIncludeFile src/api/openapi.yaml
```
and `src/api/openapi.yaml` contains:
```yaml
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0
```
results in:
```yaml
MyStack:
  Def:
    openapi: 3.0.0
    info:
      title: My API
      version: 1.0.0
```

For example: 

```yaml
MyStack:
  Def: !CFNToolsIncludeFile src/api/openapi.json
```
and `src/api/openapi.json` contains:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "My API",
    "version": "1.0.0"
  }
}
```
results in:
```yaml
MyStack:
  Def:
    openapi: 3.0.0
    info:
      title: My API
      version: 1.0.0
```

### !CFNToolsToString 

`!CFNToolsToString` is new processing tag that converts a anything to a string.
This function processes additional parameters, so the input must be a list to avoid invalid type errors.

Parameters:
- **Value** : any - mandatory positional parameter, this is the value to convert to a string.

Optional parameters:
- **ConvertTo** : enum["YAMLString", "JSONString"] - optional parameter, when the input is a structured data (yaml, json) then the input is converted to a string. Default is "JSONString".
- **OneLine** : bool - optional parameter, when this is true then the output will be a single line string. Default is False.

Example:
```yaml
MyStack:
  Def: !CFNToolsToString [ "Hello, World!" ]
```
results in:
```yaml
MyStack:
  Def: "Hello, World!"
```

Example:
```yaml
MyStack:
  Def: !CFNToolsToString [ { "name": "John", "age": 30 }, { ConvertTo: "YAMLString" } ]
```
results in:
```yaml
MyStack:
  Def: |
    name: John
    age: 30
```

Example:
```yaml
MyStack:
  Def: !CFNToolsToString [ { "name": "John", "age": 30 }, { ConvertTo: "JSONString" } ]
```
results in:
```yaml
MyStack:
  Def: |
    {
      "name": "John",
      "age": 30
    }
```

Example:
```yaml
MyStack:
  Def: !CFNToolsToString [ { "name": "John", "age": 30 }, { ConvertTo: "JSONString", OneLine: true } ]
```
results in:
```yaml
MyStack:
  Def: "{\"name\":\"John\",\"age\":30}"
```

Example:
```yaml
MyStack:
  Def: !CFNToolsToString [ "Hello\nWorld!", { OneLine: true } ]
```
results in:
```yaml
MyStack:
  Def: "Hello World!"
```

## Implementation notes

- create new module `cfn_tools.cfn_processing`
- inherit the loader from `cfn_tools.cfn_yaml.CloudFormationLoader` so the CloudFormation tags are supported and the loading of the yaml file is supported
- write the unit tests for the new functions
- put the unit tests to `tests/test_cfn_processing.py`
  - for each tag, create a test class to keep the code organized
  - use acceptance criteria as test cases
  - add additional test cases as needed