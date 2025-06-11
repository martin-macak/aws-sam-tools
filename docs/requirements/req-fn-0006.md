# REQ-FN-0006 - Store dict loaded from YAML in valid YAML format

## Acceptance Criteria

- all CloudFormationTag instances are serialized to YAML in the same format as they were loaded from YAML
- new dump_yaml function is added to cfn_yaml.py
- new Dumper class is added to cfn_yaml.py
- all classes and functions are covered by tests

### Test Cases

Each CloudFormationTag is tested with a source YAML file and an expected YAML output file.

#### Test Case 1 - RefTag

Source YAML:

```yaml
MyStack:
  Def: !Ref MyBucket
```

Expected YAML output:

```yaml
MyStack:
  Def: !Ref MyBucket
```

#### Test Case 2 - GetAttTag

Source YAML:

```yaml
MyStack:
  Def: !GetAtt MyBucket.DomainName
```

Expected YAML output:

```yaml
MyStack:
  Def: !GetAtt MyBucket.DomainName
```

## Implementation Notes

- use parameterised tests for each CloudFormationTag
