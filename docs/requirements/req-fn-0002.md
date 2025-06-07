# REQ-FN-0002 - Build and utility tags

New class with custom CloudFormation yaml processing.

## Acceptance Criteria

### !CFNToolsUUID

`!CFNToolsUUID` is new processing tag that generates a UUID v4.


Example:
```yaml
!CFNToolsUUID
```

For example: 

```yaml
MyStack:
  Id: !CFNToolsUUID
```
results in:
```yaml
MyStack:
  Id: 123e4567-e89b-12d3-a456-426614174000
```

### !CFNToolsVersion

`!CFNToolsVersion` is new processing tag that generates a version string.

Optional parameters:
- **Source** : enum["Git", "Any"], optional parameter, this is the source of the version string. Default is "Git".
- **Style** : enum["semver", "pep440"], optional parameter, this is the style of the version string. Default is "semver".

Example:
```yaml
!CFNToolsVersion
```
results in:
```yaml
MyStack:
  Version: 1.0.0-dev.1+123e4567
```

This function uses dunamai to generate the version string.

### !CFNToolsTimestamp

`!CFNToolsTimestamp` is new processing tag that generates a timestamp string.

Optional parameters:
- **Format** : str - optional parameter, this is the format of the timestamp string. If no format is specified then ISO-8601 format is used in UTC timezone.
- **Offset** : int - optional parameter, this is the offset in OffsetUnit from current time. Default is 0.
- **OffsetUnit** : enum["seconds", "minutes", "hours", "days", "weeks", "months", "years"], optional parameter, this is the unit of the offset. Default is "seconds".

Example:
```yaml
!CFNToolsTimestamp
```
results in:
```yaml
MyStack:
  Timestamp: 2021-01-01T00:00:00Z
```

Example:
```yaml
!CFNToolsTimestamp { Format: "%Y-%m-%d %H:%M:%S" }
```
results in:
```yaml
MyStack:
  Timestamp: 2021-01-01 00:00:00
```

Example:
```yaml
!CFNToolsTimestamp { Offset: 1, OffsetUnit: "minutes" }
```
results in:
```yaml
MyStack:
  Timestamp: 2021-01-01T00:01:00Z
```

### !CFNToolsCRC

`!CFNToolsCRC` is new processing tag that generates a checksum of the input string.
This function processes additional parameters, so the input must be a list to avoid invalid type errors.

Parameters:
- **Value** : any - mandatory positional parameter, this is the value to generate the checksum for.

Optional parameters:
- **Algorithm** : enum["md5", "sha1", "sha256", "sha512"], optional parameter, this is the algorithm to use for the checksum. Default is "sha256".
- **Encoding** : enum["hex", "base64"], optional parameter, this is the encoding of the checksum. Default is "hex".

The Value parameter can be anything. If the valud is a structured data like dict or list then the checksum is generated from the string representation of the data.
If the Value is a string then the checksum is generated from the string.
If the string Value starts with `file://` then the checksum is generated from the file that is located at the path specified after `file://`.

Example:
```yaml
MyStack:
  CRC: !CFNToolsCRC [ "Hello, World!" ]
```
results in:
```yaml
MyStack:
  CRC: 123e4567-e89b-12d3-a456-426614174000 # an SHA-256 checksum of the string "Hello, World!"
```

Example:
```yaml
MyStack:
  CRC: !CFNToolsCRC [ { "name": "John", "age": 30 } ]
```
results in:
```yaml
MyStack:
  CRC: 123e4567-e89b-12d3-a456-426614174000 # an SHA-256 checksum of the string "{"name":"John","age":30}"
```

Example:
```yaml
MyStack:
  CRC: !CFNToolsCRC [ "file://README.md" ]
```
results in:
```yaml
MyStack:
  CRC: 123e4567-e89b-12d3-a456-426614174000 # an SHA-256 checksum of the file "README.md"
```

Example:
```yaml
MyStack:
  CRC: !CFNToolsCRC [ "file://README.md", { Algorithm: "md5" } ]
```
results in:
```yaml
MyStack:
  CRC: 123e4567-e89b-12d3-a456-426614174000 # an MD5 checksum of the file "README.md"
```

## Implementation notes

- create new module `cfn_tools.cfn_processing`
- inherit the loader from `cfn_tools.cfn_yaml.CloudFormationLoader` so the CloudFormation tags are supported and the loading of the yaml file is supported
- write the unit tests for the new functions
- put the unit tests to `tests/test_cfn_processing.py`
  - for each tag, create a test class to keep the code organized
  - use acceptance criteria as test cases
  - add additional test cases as needed
- check how dunamai works and how to use it at https://github.com/mtkennerly/dunamai
- mock dunamai to return the version string