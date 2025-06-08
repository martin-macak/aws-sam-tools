"""Tests for CloudFormation tag replacement functionality."""

import pytest
import yaml

from aws_sam_tools.cfn_processing import load_yaml, load_yaml_file


class TestCloudFormationTagReplacement:
    """Test cases for CloudFormation tag replacement functionality."""

    def test_replace_ref_tag(self) -> None:
        """Test replacing !Ref tags with Ref intrinsic function."""
        yaml_content = """Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketParam"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Resources": {
                "MyBucket": {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {"BucketName": {"Ref": "BucketParam"}},
                }
            }
        }
        assert result == expected

    def test_replace_getatt_tag(self) -> None:
        """Test replacing !GetAtt tags with Fn::GetAtt intrinsic function."""
        yaml_content = """Outputs:
  BucketArn:
    Value: !GetAtt
      - MyBucket
      - Arn"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Outputs": {"BucketArn": {"Value": {"Fn::GetAtt": ["MyBucket", "Arn"]}}}}
        assert result == expected

    def test_replace_getatt_tag_dot_notation(self) -> None:
        """Test replacing !GetAtt tags with dot notation."""
        yaml_content = """Outputs:
  BucketArn:
    Value: !GetAtt MyBucket.Arn
  QueueArn:
    Value: !GetAtt MyQueue.Arn"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Outputs": {
                "BucketArn": {"Value": {"Fn::GetAtt": ["MyBucket", "Arn"]}},
                "QueueArn": {"Value": {"Fn::GetAtt": ["MyQueue", "Arn"]}},
            }
        }
        assert result == expected

    def test_replace_sub_tag(self) -> None:
        """Test replacing !Sub tags with Fn::Sub intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      Name: !Sub 'Hello ${AWS::Region}'"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"Name": {"Fn::Sub": "Hello ${AWS::Region}"}}}}}
        assert result == expected

    def test_replace_join_tag(self) -> None:
        """Test replacing !Join tags with Fn::Join intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      Value: !Join
        - '-'
        - - 'prefix'
          - !Ref Param
          - 'suffix'"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"Value": {"Fn::Join": ["-", ["prefix", {"Ref": "Param"}, "suffix"]]}}}}}
        assert result == expected

    def test_replace_select_tag(self) -> None:
        """Test replacing !Select tags with Fn::Select intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      Az: !Select
        - 0
        - !GetAZs ''"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"Az": {"Fn::Select": [0, {"Fn::GetAZs": ""}]}}}}}
        assert result == expected

    def test_replace_split_tag(self) -> None:
        """Test replacing !Split tags with Fn::Split intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      Items: !Split
        - ','
        - 'a,b,c'"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"Items": {"Fn::Split": [",", "a,b,c"]}}}}}
        assert result == expected

    def test_replace_getazs_tag(self) -> None:
        """Test replacing !GetAZs tags with Fn::GetAZs intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      AvailabilityZones: !GetAZs ''"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"AvailabilityZones": {"Fn::GetAZs": ""}}}}}
        assert result == expected

    def test_replace_importvalue_tag(self) -> None:
        """Test replacing !ImportValue tags with Fn::ImportValue intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      VpcId: !ImportValue SharedVpcId"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {"Resources": {"MyResource": {"Properties": {"VpcId": {"Fn::ImportValue": "SharedVpcId"}}}}}
        assert result == expected

    def test_nested_tag_replacement(self) -> None:
        """Test replacing nested CloudFormation tags."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      Name: !Sub
        - '${Prefix}-${!Ref Suffix}'
        - Prefix: !Ref PrefixParam"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Resources": {
                "MyResource": {
                    "Properties": {
                        "Name": {
                            "Fn::Sub": [
                                "${Prefix}-${!Ref Suffix}",
                                {"Prefix": {"Ref": "PrefixParam"}},
                            ]
                        }
                    }
                }
            }
        }
        assert result == expected

    def test_complex_nested_tags(self) -> None:
        """Test complex nested tag structures."""
        yaml_content = """Resources:
  MyResource:
    Properties:
      ComplexValue: !Join
        - '-'
        - - !Select
            - 0
            - !Split
              - ','
              - !Ref CSVParam
          - !GetAtt
            - MyBucket
            - Arn
          - !Sub '${AWS::Region}'"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Resources": {
                "MyResource": {
                    "Properties": {
                        "ComplexValue": {
                            "Fn::Join": [
                                "-",
                                [
                                    {
                                        "Fn::Select": [
                                            0,
                                            {"Fn::Split": [",", {"Ref": "CSVParam"}]},
                                        ]
                                    },
                                    {"Fn::GetAtt": ["MyBucket", "Arn"]},
                                    {"Fn::Sub": "${AWS::Region}"},
                                ],
                            ]
                        }
                    }
                }
            }
        }
        assert result == expected

    def test_without_replace_tags_flag(self) -> None:
        """Test that tags are preserved when replace_tags is False."""
        yaml_content = """Resources:
  MyBucket:
    Properties:
      BucketName: !Ref BucketParam"""

        result = load_yaml(yaml_content, replace_tags=False)
        # Check that the RefTag object is preserved
        assert hasattr(result["Resources"]["MyBucket"]["Properties"]["BucketName"], "value")
        assert result["Resources"]["MyBucket"]["Properties"]["BucketName"].value == "BucketParam"

    def test_replace_tags_in_file(self, tmp_path) -> None:
        """Test replacing tags when loading from file."""
        yaml_content = """Resources:
  MyFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-function'
      Role: !GetAtt
        - LambdaRole
        - Arn
      Environment:
        Variables:
          BUCKET_NAME: !Ref S3Bucket
          REGION: !Ref AWS::Region"""

        template_file = tmp_path / "template.yaml"
        template_file.write_text(yaml_content)

        result = load_yaml_file(str(template_file), replace_tags=True)
        expected = {
            "Resources": {
                "MyFunction": {
                    "Type": "AWS::Lambda::Function",
                    "Properties": {
                        "FunctionName": {"Fn::Sub": "${AWS::StackName}-function"},
                        "Role": {"Fn::GetAtt": ["LambdaRole", "Arn"]},
                        "Environment": {
                            "Variables": {
                                "BUCKET_NAME": {"Ref": "S3Bucket"},
                                "REGION": {"Ref": "AWS::Region"},
                            }
                        },
                    },
                }
            }
        }
        assert result == expected

    def test_replace_tags_preserves_other_content(self) -> None:
        """Test that non-tag content is preserved during replacement."""
        yaml_content = """Description: Test Template
Parameters:
  BucketName:
    Type: String
    Default: my-bucket
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Ref BucketName
      Tags:
        - Key: Name
          Value: !Sub '${AWS::StackName}-bucket'
        - Key: Environment
          Value: production"""

        result = load_yaml(yaml_content, replace_tags=True)

        # Check that non-tag content is preserved
        assert result["Description"] == "Test Template"
        assert result["Parameters"]["BucketName"]["Type"] == "String"
        assert result["Parameters"]["BucketName"]["Default"] == "my-bucket"
        assert result["Resources"]["MyBucket"]["Type"] == "AWS::S3::Bucket"

        # Check that tags are replaced
        assert result["Resources"]["MyBucket"]["Properties"]["BucketName"] == {"Ref": "BucketName"}
        assert result["Resources"]["MyBucket"]["Properties"]["Tags"][0]["Value"] == {"Fn::Sub": "${AWS::StackName}-bucket"}
        assert result["Resources"]["MyBucket"]["Properties"]["Tags"][1]["Value"] == "production"

    def test_replace_findinmap_tag(self) -> None:
        """Test replacing !FindInMap tags with Fn::FindInMap intrinsic function."""
        yaml_content = """Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: !FindInMap
        - RegionMap
        - !Ref AWS::Region
        - AMI"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Resources": {
                "MyInstance": {
                    "Type": "AWS::EC2::Instance",
                    "Properties": {"ImageId": {"Fn::FindInMap": ["RegionMap", {"Ref": "AWS::Region"}, "AMI"]}},
                }
            }
        }
        assert result == expected

    def test_replace_transform_tag(self) -> None:
        """Test replacing !Transform tags with Fn::Transform intrinsic function."""
        yaml_content = """Resources:
  MyResource:
    Type: AWS::CloudFormation::CustomResource
    Properties:
      Data: !Transform
        Name: MyTransform
        Parameters:
          Param1: Value1"""

        result = load_yaml(yaml_content, replace_tags=True)
        expected = {
            "Resources": {
                "MyResource": {
                    "Type": "AWS::CloudFormation::CustomResource",
                    "Properties": {"Data": {"Fn::Transform": {"Name": "MyTransform", "Parameters": {"Param1": "Value1"}}}},
                }
            }
        }
        assert result == expected

    def test_replace_conditional_tags(self) -> None:
        """Test replacing conditional function tags."""
        yaml_content = """Conditions:
  IsProduction: !Equals
    - !Ref Environment
    - production
  HasMultiAZ: !And
    - !Equals [!Ref Environment, production]
    - !Not [!Equals [!Ref Region, us-east-1]]
  UseCustomVpc: !Or
    - !Equals [!Ref VpcId, ""]
    - !Condition IsProduction
Resources:
  MyResource:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !If
        - IsProduction
        - t3.large
        - t3.micro"""

        result = load_yaml(yaml_content, replace_tags=True)

        # Check conditions
        assert result["Conditions"]["IsProduction"] == {"Fn::Equals": [{"Ref": "Environment"}, "production"]}
        assert result["Conditions"]["HasMultiAZ"] == {
            "Fn::And": [
                {"Fn::Equals": [{"Ref": "Environment"}, "production"]},
                {"Fn::Not": [{"Fn::Equals": [{"Ref": "Region"}, "us-east-1"]}]},
            ]
        }
        assert result["Conditions"]["UseCustomVpc"] == {"Fn::Or": [{"Fn::Equals": [{"Ref": "VpcId"}, ""]}, {"Condition": "IsProduction"}]}

        # Check If function
        assert result["Resources"]["MyResource"]["Properties"]["InstanceType"] == {"Fn::If": ["IsProduction", "t3.large", "t3.micro"]}

    def test_complex_nested_with_new_tags(self) -> None:
        """Test complex nested structures with new tags."""
        yaml_content = """Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Condition: !And
      - !Not [!Equals [!Ref Environment, dev]]
      - !Or
        - !Equals [!Ref CreateBucket, "true"]
        - !Condition IsProduction
    Properties:
      BucketName: !If
        - IsProduction
        - !Sub '${AWS::StackName}-prod-${!GetAtt MyResource.Id}'
        - !Join
          - '-'
          - - !Ref AWS::StackName
            - dev
            - !Select [0, !Split ['-', !Ref Identifier]]"""

        result = load_yaml(yaml_content, replace_tags=True)

        # Check condition
        assert result["Resources"]["MyBucket"]["Condition"] == {
            "Fn::And": [
                {"Fn::Not": [{"Fn::Equals": [{"Ref": "Environment"}, "dev"]}]},
                {
                    "Fn::Or": [
                        {"Fn::Equals": [{"Ref": "CreateBucket"}, "true"]},
                        {"Condition": "IsProduction"},
                    ]
                },
            ]
        }

        # Check nested If with Sub and Join
        bucket_name = result["Resources"]["MyBucket"]["Properties"]["BucketName"]
        assert bucket_name["Fn::If"][0] == "IsProduction"
        assert bucket_name["Fn::If"][1] == {"Fn::Sub": "${AWS::StackName}-prod-${!GetAtt MyResource.Id}"}
        assert bucket_name["Fn::If"][2]["Fn::Join"][0] == "-"
