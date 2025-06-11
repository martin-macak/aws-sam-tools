"""Tests for the cfn_yaml module."""

import pytest

from aws_sam_tools.cfn_yaml import (
    Base64Tag,
    CidrTag,
    EqualsTag,
    FindInMapTag,
    GetAttTag,
    GetAZsTag,
    ImportValueTag,
    JoinTag,
    RefTag,
    SelectTag,
    SplitTag,
    SubTag,
    dump_yaml,
    load_yaml,
)


class TestCloudFormationTagParsing:
    """Test cases for CloudFormation tag parsing functionality."""

    # Test data for valid YAML inputs
    VALID_YAML_TESTS = [
        # Ref tag tests
        (
            """
            Resources:
              MyBucket:
                Type: AWS::S3::Bucket
                Properties:
                  BucketName: !Ref MyBucketName
            """,
            {"Resources": {"MyBucket": {"Type": "AWS::S3::Bucket", "Properties": {"BucketName": RefTag("MyBucketName")}}}},
        ),
        # GetAtt tag tests
        (
            """
            Resources:
              MyInstance:
                Type: AWS::EC2::Instance
                Properties:
                  UserData: !GetAtt 
                    - MyInstance
                    - PublicDnsName
            """,
            {"Resources": {"MyInstance": {"Type": "AWS::EC2::Instance", "Properties": {"UserData": GetAttTag(["MyInstance", "PublicDnsName"])}}}},
        ),
        # Sub tag tests
        (
            """
            Resources:
              MyBucket:
                Type: AWS::S3::Bucket
                Properties:
                  BucketName: !Sub ${AWS::StackName}-my-bucket
            """,
            {"Resources": {"MyBucket": {"Type": "AWS::S3::Bucket", "Properties": {"BucketName": SubTag(["${AWS::StackName}-my-bucket"])}}}},
        ),
        # Join tag tests
        (
            """
            Resources:
              MyBucket:
                Type: AWS::S3::Bucket
                Properties:
                  BucketName: !Join 
                    - '-'
                    - - !Ref AWS::StackName
                      - my-bucket
            """,
            {"Resources": {"MyBucket": {"Type": "AWS::S3::Bucket", "Properties": {"BucketName": JoinTag(["-", [RefTag("AWS::StackName"), "my-bucket"]])}}}},
        ),
        # Split tag tests
        (
            """
            Resources:
              MyFunction:
                Type: AWS::Lambda::Function
                Properties:
                  Handler: !Split 
                    - '.'
                    - index.handler
            """,
            {"Resources": {"MyFunction": {"Type": "AWS::Lambda::Function", "Properties": {"Handler": SplitTag([".", "index.handler"])}}}},
        ),
        # Select tag tests
        (
            """
            Resources:
              MyFunction:
                Type: AWS::Lambda::Function
                Properties:
                  Runtime: !Select 
                    - 0
                    - - python3.9
                      - python3.8
            """,
            {"Resources": {"MyFunction": {"Type": "AWS::Lambda::Function", "Properties": {"Runtime": SelectTag([0, ["python3.9", "python3.8"]])}}}},
        ),
        # FindInMap tag tests
        (
            """
            Resources:
              MyInstance:
                Type: AWS::EC2::Instance
                Properties:
                  InstanceType: !FindInMap 
                    - RegionMap
                    - !Ref AWS::Region
                    - InstanceType
            """,
            {"Resources": {"MyInstance": {"Type": "AWS::EC2::Instance", "Properties": {"InstanceType": FindInMapTag(["RegionMap", RefTag("AWS::Region"), "InstanceType"])}}}},
        ),
        # Base64 tag tests
        (
            """
            Resources:
              MyFunction:
                Type: AWS::Lambda::Function
                Properties:
                  Code: !Base64 |
                    def handler(event, context):
                        return {'statusCode': 200}
            """,
            {"Resources": {"MyFunction": {"Type": "AWS::Lambda::Function", "Properties": {"Code": Base64Tag("def handler(event, context):\n    return {'statusCode': 200}\n")}}}},
        ),
        # Cidr tag tests
        (
            """
            Resources:
              MyVPC:
                Type: AWS::EC2::VPC
                Properties:
                  CidrBlock: !Cidr 
                    - 10.0.0.0/16
                    - 8
                    - 8
            """,
            {"Resources": {"MyVPC": {"Type": "AWS::EC2::VPC", "Properties": {"CidrBlock": CidrTag(["10.0.0.0/16", 8, 8])}}}},
        ),
        # ImportValue tag tests
        (
            """
            Resources:
              MyBucket:
                Type: AWS::S3::Bucket
                Properties:
                  BucketName: !ImportValue MyExportedBucketName
            """,
            {"Resources": {"MyBucket": {"Type": "AWS::S3::Bucket", "Properties": {"BucketName": ImportValueTag("MyExportedBucketName")}}}},
        ),
        # GetAZs tag tests
        (
            """
            Resources:
              MyVPC:
                Type: AWS::EC2::VPC
                Properties:
                  AvailabilityZones: !GetAZs us-east-1
            """,
            {"Resources": {"MyVPC": {"Type": "AWS::EC2::VPC", "Properties": {"AvailabilityZones": GetAZsTag("us-east-1")}}}},
        ),
    ]

    # Test data for invalid YAML inputs
    INVALID_YAML_TESTS = [
        # Invalid Ref tag (missing value)
        """
        Resources:
          MyBucket:
            Type: AWS::S3::Bucket
            Properties:
              BucketName: !Ref
        """,
        # Invalid GetAtt tag (wrong number of arguments)
        """
        Resources:
          MyInstance:
            Type: AWS::EC2::Instance
            Properties:
              UserData: !GetAtt MyInstance
        """,
        # Invalid Sub tag (missing value)
        """
        Resources:
          MyBucket:
            Type: AWS::S3::Bucket
            Properties:
              BucketName: !Sub
        """,
        # Invalid Join tag (missing delimiter)
        """
        Resources:
          MyBucket:
            Type: AWS::S3::Bucket
            Properties:
              BucketName: !Join
                - my-bucket
        """,
        # Invalid Split tag (missing delimiter)
        """
        Resources:
          MyFunction:
            Type: AWS::Lambda::Function
            Properties:
              Handler: !Split index.handler
        """,
        # Invalid Select tag (wrong index type)
        """
        Resources:
          MyFunction:
            Type: AWS::Lambda::Function
            Properties:
              Runtime: !Select 
                - "0"
                - - python3.9
                  - python3.8
        """,
        # Invalid FindInMap tag (missing arguments)
        """
        Resources:
          MyInstance:
            Type: AWS::EC2::Instance
            Properties:
              InstanceType: !FindInMap RegionMap
        """,
        # Invalid Cidr tag (wrong number of arguments)
        """
        Resources:
          MyVPC:
            Type: AWS::EC2::VPC
            Properties:
              CidrBlock: !Cidr 10.0.0.0/16
        """,
    ]

    @pytest.mark.parametrize("yaml_content,expected", VALID_YAML_TESTS)
    def test_valid_yaml_parsing(self, yaml_content, expected):
        """Test parsing of valid YAML content with CloudFormation tags."""
        result = load_yaml(yaml_content)
        assert result == expected

    @pytest.mark.parametrize("yaml_content", INVALID_YAML_TESTS)
    def test_invalid_yaml_parsing(self, yaml_content):
        """Test that invalid YAML content raises appropriate exceptions."""
        with pytest.raises(Exception):
            load_yaml(yaml_content)

    def test_nested_tags(self):
        """Test parsing of nested CloudFormation tags."""
        yaml_content = """
        Resources:
          MyBucket:
            Type: AWS::S3::Bucket
            Properties:
              BucketName: !Join 
                - '-'
                - - !Ref AWS::StackName
                  - !Sub ${Environment}-bucket
        """
        result = load_yaml(yaml_content)
        assert isinstance(result["Resources"]["MyBucket"]["Properties"]["BucketName"], JoinTag)
        join_tag = result["Resources"]["MyBucket"]["Properties"]["BucketName"]
        assert join_tag.value[0] == "-"
        assert isinstance(join_tag.value[1][0], RefTag)
        assert isinstance(join_tag.value[1][1], SubTag)

    def test_empty_yaml(self):
        """Test parsing of empty YAML content."""
        result = load_yaml("")
        assert result is None

    def test_yaml_without_tags(self):
        """Test parsing of YAML content without CloudFormation tags."""
        yaml_content = """
        Resources:
          MyBucket:
            Type: AWS::S3::Bucket
            Properties:
              BucketName: my-bucket
        """
        result = load_yaml(yaml_content)
        assert result["Resources"]["MyBucket"]["Properties"]["BucketName"] == "my-bucket"

    def test_yaml_with_comments(self):
        """Test parsing of YAML content with comments."""
        yaml_content = """
        # This is a comment
        Resources:
          MyBucket:
            Type: AWS::S3::Bucket
            Properties:
              # Another comment
              BucketName: !Ref MyBucketName
        """
        result = load_yaml(yaml_content)
        assert isinstance(result["Resources"]["MyBucket"]["Properties"]["BucketName"], RefTag)


class TestCloudFormationYAMLDump:
    """Test CloudFormation YAML dumping functionality."""

    @pytest.mark.parametrize(
        "yaml_content,expected_yaml",
        [
            # RefTag test case
            ("MyStack:\n  Def: !Ref MyBucket", "MyStack:\n  Def: !Ref MyBucket\n"),
            # GetAttTag test case
            ("MyStack:\n  Def: !GetAtt MyBucket.DomainName", "MyStack:\n  Def: !GetAtt MyBucket.DomainName\n"),
            # SubTag scalar test case
            ("MyStack:\n  Def: !Sub 'Hello ${Name}'", "MyStack:\n  Def: !Sub Hello ${Name}\n"),
            # SubTag sequence test case
            ("MyStack:\n  Def: !Sub\n    - 'Hello ${Name}'\n    - Name: World", "MyStack:\n  Def: !Sub\n  - Hello ${Name}\n  - Name: World\n"),
            # JoinTag test case
            ("MyStack:\n  Def: !Join\n    - ','\n    - [a, b, c]", "MyStack:\n  Def: !Join\n  - ','\n  - - a\n    - b\n    - c\n"),
            # SplitTag test case
            ("MyStack:\n  Def: !Split\n    - ','\n    - 'a,b,c'", "MyStack:\n  Def: !Split\n  - ','\n  - a,b,c\n"),
            # SelectTag test case
            ("MyStack:\n  Def: !Select\n    - 0\n    - [a, b, c]", "MyStack:\n  Def: !Select\n  - 0\n  - - a\n    - b\n    - c\n"),
            # FindInMapTag test case
            ("MyStack:\n  Def: !FindInMap\n    - RegionMap\n    - us-east-1\n    - AMI", "MyStack:\n  Def: !FindInMap\n  - RegionMap\n  - us-east-1\n  - AMI\n"),
            # Base64Tag test case
            ("MyStack:\n  Def: !Base64 'Hello World'", "MyStack:\n  Def: !Base64 Hello World\n"),
            # CidrTag test case
            ("MyStack:\n  Def: !Cidr\n    - 10.0.0.0/16\n    - 6\n    - 5", "MyStack:\n  Def: !Cidr\n  - 10.0.0.0/16\n  - 6\n  - 5\n"),
            # ImportValueTag test case
            ("MyStack:\n  Def: !ImportValue NetworkStackVPC", "MyStack:\n  Def: !ImportValue NetworkStackVPC\n"),
            # GetAZsTag test case
            ("MyStack:\n  Def: !GetAZs us-east-1", "MyStack:\n  Def: !GetAZs us-east-1\n"),
            # TransformTag test case
            (
                "MyStack:\n  Def: !Transform\n    Name: AWS::Include\n    Parameters:\n      Location: s3://bucket/template.yaml",
                "MyStack:\n  Def: !Transform\n    Name: AWS::Include\n    Parameters:\n      Location: s3://bucket/template.yaml\n",
            ),
            # AndTag test case
            ("MyStack:\n  Def: !And\n    - !Condition Condition1\n    - !Condition Condition2", "MyStack:\n  Def: !And\n  - !Condition Condition1\n  - !Condition Condition2\n"),
            # EqualsTag test case
            ("MyStack:\n  Def: !Equals\n    - !Ref Environment\n    - Production", "MyStack:\n  Def: !Equals\n  - !Ref Environment\n  - Production\n"),
            # IfTag test case
            ("MyStack:\n  Def: !If\n    - !Condition CreateProdResources\n    - ProdValue\n    - DevValue", "MyStack:\n  Def: !If\n  - !Condition CreateProdResources\n  - ProdValue\n  - DevValue\n"),
            # NotTag test case
            ("MyStack:\n  Def: !Not\n    - !Condition CreateDevResources", "MyStack:\n  Def: !Not\n  - !Condition CreateDevResources\n"),
            # OrTag test case
            ("MyStack:\n  Def: !Or\n    - !Condition Condition1\n    - !Condition Condition2", "MyStack:\n  Def: !Or\n  - !Condition Condition1\n  - !Condition Condition2\n"),
            # ConditionTag test case
            ("MyStack:\n  Def: !Condition CreateProdResources", "MyStack:\n  Def: !Condition CreateProdResources\n"),
        ],
    )
    def test_round_trip_yaml_dump(self, yaml_content: str, expected_yaml: str):
        """Test that loading and dumping YAML preserves the original format."""
        # Load YAML with CloudFormation tags
        loaded_data = load_yaml(yaml_content)

        # Dump back to YAML
        dumped_yaml = dump_yaml(loaded_data)

        # Compare with expected output
        assert dumped_yaml == expected_yaml

    def test_nested_tags(self):
        """Test dumping of nested CloudFormation tags."""
        yaml_content = """
Resources:
  MyResource:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub
        - "${StackName}-${Suffix}"
        - StackName: !Ref "AWS::StackName"
          Suffix: !Ref BucketSuffix
"""
        expected = """Resources:
  MyResource:
    Properties:
      BucketName: !Sub
      - ${StackName}-${Suffix}
      - StackName: !Ref AWS::StackName
        Suffix: !Ref BucketSuffix
    Type: AWS::S3::Bucket
"""

        loaded_data = load_yaml(yaml_content)
        dumped_yaml = dump_yaml(loaded_data)

        assert dumped_yaml == expected

    def test_complex_template(self):
        """Test dumping of a complex CloudFormation template."""
        yaml_content = """
AWSTemplateFormatVersion: '2010-09-09'
Description: Test template
Parameters:
  Environment:
    Type: String
    Default: dev
Conditions:
  IsProd: !Equals [!Ref Environment, prod]
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${AWS::StackName}-bucket"
      Tags:
        - Key: Environment
          Value: !Ref Environment
Outputs:
  BucketArn:
    Value: !GetAtt MyBucket.Arn
    Export:
      Name: !Sub "${AWS::StackName}-BucketArn"
"""

        # Test that we can load and dump without errors
        loaded_data = load_yaml(yaml_content)
        dumped_yaml = dump_yaml(loaded_data)

        # Verify it can be loaded again
        reloaded_data = load_yaml(dumped_yaml)

        # Check some key values are preserved
        assert isinstance(reloaded_data["Conditions"]["IsProd"], EqualsTag)
        assert isinstance(reloaded_data["Resources"]["MyBucket"]["Properties"]["BucketName"], SubTag)
        assert isinstance(reloaded_data["Outputs"]["BucketArn"]["Value"], GetAttTag)
