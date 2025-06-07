# REQ-FN-0004 - Add replace-tags to `template process`

Running the `template process` command should support `--replace-tags` switch. When toggled on, all CloudFormation tags are replaced by intrinsic functions.

## Acceptance Criteria

- `template process` command supports `--replace-tags` switch
- `--replace-tags` switch is off by default
- when `--replace-tags` switch is on, all CloudFormation tags are replaced by intrinsic functions

### List of tags and their couterparts

The intrinsic functions are documented at https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/intrinsic-function-reference.html

The list covers:

- !Ref -> Ref
- !GetAtt -> Fn::GetAtt
- !GetAZs -> Fn::GetAZs
- !ImportValue -> Fn::ImportValue
- !Join -> Fn::Join
- !Select -> Fn::Select
- !Split -> Fn::Split
- !Sub -> Fn::Sub
- !ImportValue -> Fn::ImportValue
- !FindInMap -> Fn::FindInMap
- !Transform -> Fn::Transform

Also the conditional functions are covered:
- !And -> Fn::And
- !Equals -> Fn::Equals
- !If -> Fn::If
- !Not -> Fn::Not
- !Or -> Fn::Or

## Implementation notes

- this must work recursively, so if the tag is inside another tag then the tag should be replaced by the intrinsic function
- GetAtt behaves differently in tag mode, because it supports dot notation

### GetAtt

GetAtt behaves differently in tag mode, because it supports dot notation.

Example:
```yaml
MyStack:
  GetAtt: !GetAtt MyResource.MyAttribute
```
equals to:
```yaml
MyStack:
  Fn::GetAtt:
    - !Ref MyResource
    - MyAttribute
```
