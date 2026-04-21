"""
AWS Deployment Generator for ADAM DNA Specification.
Generates Terraform + CloudFormation templates for AWS warm standby.
"""

from typing import Dict, Any
from .base_generator import BaseGenerator

class AWSGenerator(BaseGenerator):
    PLATFORM_NAME = "aws"
    PLATFORM_DISPLAY = "Amazon Web Services (Warm Standby / Primary)"

    def generate_iac(self) -> Dict[str, str]:
        files = {}
        files[self.write_file("terraform/main.tf", self._terraform_main())] = "Terraform root module"
        files[self.write_file("terraform/variables.tf", self._terraform_variables())] = "Terraform variables"
        files[self.write_file("terraform/modules/networking/main.tf", self._tf_networking())] = "VPC networking module"
        files[self.write_file("terraform/modules/eks/main.tf", self._tf_eks())] = "EKS cluster module"
        files[self.write_file("terraform/modules/neptune/main.tf", self._tf_neptune())] = "Neptune (CORE Graph standby)"
        files[self.write_file("terraform/modules/s3-evidence/main.tf", self._tf_s3_evidence())] = "S3 Flight Recorder"
        files[self.write_file("terraform/modules/kms/main.tf", self._tf_kms())] = "KMS (Crypto Vault)"
        files[self.write_file("terraform/modules/bedrock/main.tf", self._tf_bedrock())] = "Bedrock AI services"
        files[self.write_file("cloudformation/adam-stack.yaml", self._cloudformation())] = "CloudFormation stack"
        return files

    def generate_configs(self) -> Dict[str, str]:
        files = {}
        files[self.write_json("config/adam-aws-config.json", self._aws_config())] = "AWS deployment config"
        files[self.write_yaml("config/adam-aws-values.yaml", self._aws_values())] = "AWS Helm values"
        return files

    def _terraform_main(self) -> str:
        return f'''{self.header_comment("#")}

terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }}
  }}
  backend "s3" {{
    bucket         = "adam-tfstate-{self.company_slug}"
    key            = "adam/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "adam-tfstate-lock"
  }}
}}

provider "aws" {{
  region = var.primary_region
  default_tags {{
    tags = {{
      "adam-company"  = "{self.company_name}"
      "adam-platform" = "aws-standby"
      "managed-by"    = "adam-dna-deployment-tool"
      "environment"   = var.environment
    }}
  }}
}}

# ============================================================
# Module: Networking (VPC with isolation zones)
# ============================================================
module "networking" {{
  source      = "./modules/networking"
  environment = var.environment
  company_slug = "{self.company_slug}"
  vpc_cidr    = var.vpc_cidr
}}

# ============================================================
# Module: EKS (Agent Mesh container orchestration)
# ============================================================
module "eks" {{
  source           = "./modules/eks"
  environment      = var.environment
  company_slug     = "{self.company_slug}"
  vpc_id           = module.networking.vpc_id
  private_subnets  = module.networking.private_subnet_ids
  total_vcpus      = {self.total_vcpus()}
  gpu_agent_count  = {self.gpu_agents_count()}
}}

# ============================================================
# Module: Neptune (CORE Graph - Gremlin API standby)
# ============================================================
module "neptune" {{
  source          = "./modules/neptune"
  environment     = var.environment
  company_slug    = "{self.company_slug}"
  vpc_id          = module.networking.vpc_id
  subnet_ids      = module.networking.data_subnet_ids
}}

# ============================================================
# Module: S3 Evidence Store (Flight Recorder)
# ============================================================
module "s3_evidence" {{
  source       = "./modules/s3-evidence"
  environment  = var.environment
  company_slug = "{self.company_slug}"
}}

# ============================================================
# Module: KMS (Cryptographic Authorization Vault)
# ============================================================
module "kms" {{
  source       = "./modules/kms"
  environment  = var.environment
  company_slug = "{self.company_slug}"
}}

# ============================================================
# Module: Bedrock (AI Services)
# ============================================================
module "bedrock" {{
  source       = "./modules/bedrock"
  environment  = var.environment
  company_slug = "{self.company_slug}"
}}
'''

    def _terraform_variables(self) -> str:
        return f'''{self.header_comment("#")}

variable "environment" {{
  description = "Deployment environment"
  type        = string
  default     = "production"
}}

variable "primary_region" {{
  description = "Primary AWS region"
  type        = string
  default     = "us-east-1"
}}

variable "secondary_regions" {{
  description = "Secondary AWS regions"
  type        = list(string)
  default     = ["eu-west-1", "ap-northeast-1"]
}}

variable "vpc_cidr" {{
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/8"
}}
'''

    def _tf_networking(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM VPC Networking - Isolation zones for sovereignty

variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "vpc_cidr" {{ type = string }}

resource "aws_vpc" "adam" {{
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {{ Name = "vpc-adam-${{var.company_slug}}-${{var.environment}}" }}
}}

# Governance Subnets (private, no internet)
resource "aws_subnet" "governance" {{
  count             = 3
  vpc_id            = aws_vpc.adam.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = {{ Name = "snet-adam-governance-${{count.index}}" }}
}}

# Agent Mesh Subnets
resource "aws_subnet" "agents" {{
  count             = 3
  vpc_id            = aws_vpc.adam.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = {{ Name = "snet-adam-agents-${{count.index}}" }}
}}

# Data Plane Subnets
resource "aws_subnet" "data" {{
  count             = 3
  vpc_id            = aws_vpc.adam.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 20)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = {{ Name = "snet-adam-data-${{count.index}}" }}
}}

data "aws_availability_zones" "available" {{
  state = "available"
}}

output "vpc_id" {{ value = aws_vpc.adam.id }}
output "private_subnet_ids" {{ value = aws_subnet.agents[*].id }}
output "data_subnet_ids" {{ value = aws_subnet.data[*].id }}
'''

    def _tf_eks(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM EKS Module - Container orchestration for agent mesh

variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "vpc_id" {{ type = string }}
variable "private_subnets" {{ type = list(string) }}
variable "total_vcpus" {{ type = number }}
variable "gpu_agent_count" {{ type = number }}

resource "aws_eks_cluster" "adam" {{
  name     = "eks-adam-${{var.company_slug}}-${{var.environment}}"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.29"

  vpc_config {{
    subnet_ids              = var.private_subnets
    endpoint_private_access = true
    endpoint_public_access  = false
  }}

  encryption_config {{
    provider {{ key_arn = aws_kms_key.eks.arn }}
    resources = ["secrets"]
  }}
}}

resource "aws_kms_key" "eks" {{
  description = "ADAM EKS secrets encryption"
}}

resource "aws_iam_role" "eks_cluster" {{
  name = "adam-eks-cluster-role-${{var.environment}}"
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{ Action = "sts:AssumeRole", Effect = "Allow",
      Principal = {{ Service = "eks.amazonaws.com" }} }}]
  }})
}}

# Governance Node Group
resource "aws_eks_node_group" "governance" {{
  cluster_name    = aws_eks_cluster.adam.name
  node_group_name = "adam-governance"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = var.private_subnets
  instance_types  = ["m6i.4xlarge"]

  scaling_config {{
    desired_size = 3
    min_size     = 3
    max_size     = 10
  }}

  labels = {{ "adam/plane" = "governance", "adam/tier" = "sovereign" }}
}}

# Agent Mesh Node Group
resource "aws_eks_node_group" "agent_mesh" {{
  cluster_name    = aws_eks_cluster.adam.name
  node_group_name = "adam-agents"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = var.private_subnets
  instance_types  = ["m6i.8xlarge"]

  scaling_config {{
    desired_size = 5
    min_size     = 3
    max_size     = 50
  }}

  labels = {{ "adam/plane" = "execution", "adam/agent-type" = "cpu" }}
}}

# GPU Node Group
resource "aws_eks_node_group" "gpu" {{
  cluster_name    = aws_eks_cluster.adam.name
  node_group_name = "adam-gpu"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = var.private_subnets
  instance_types  = ["p4d.24xlarge"]
  ami_type        = "AL2_x86_64_GPU"

  scaling_config {{
    desired_size = 2
    min_size     = 1
    max_size     = 20
  }}

  labels = {{ "adam/plane" = "execution", "adam/agent-type" = "gpu" }}
}}

resource "aws_iam_role" "eks_node" {{
  name = "adam-eks-node-role-${{var.environment}}"
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{ Action = "sts:AssumeRole", Effect = "Allow",
      Principal = {{ Service = "ec2.amazonaws.com" }} }}]
  }})
}}
'''

    def _tf_neptune(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Neptune - CORE Graph standby (Gremlin-compatible)

variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}
variable "vpc_id" {{ type = string }}
variable "subnet_ids" {{ type = list(string) }}

resource "aws_neptune_subnet_group" "adam" {{
  name       = "adam-neptune-${{var.environment}}"
  subnet_ids = var.subnet_ids
}}

resource "aws_neptune_cluster" "adam_core" {{
  cluster_identifier                  = "adam-core-${{var.company_slug}}-${{var.environment}}"
  engine                              = "neptune"
  engine_version                      = "1.3.1.0"
  neptune_subnet_group_name           = aws_neptune_subnet_group.adam.name
  storage_encrypted                   = true
  deletion_protection                 = true
  iam_database_authentication_enabled = true
  backup_retention_period             = 35
  preferred_backup_window             = "02:00-03:00"
  enable_cloudwatch_logs_exports      = ["audit"]
}}

resource "aws_neptune_cluster_instance" "adam_core" {{
  count              = 3
  cluster_identifier = aws_neptune_cluster.adam_core.id
  instance_class     = "db.r6g.4xlarge"
  engine             = "neptune"
}}
'''

    def _tf_s3_evidence(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM S3 Evidence Store - Flight Recorder (immutable)

variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}

resource "aws_s3_bucket" "flight_recorder" {{
  bucket = "adam-flight-recorder-${{var.company_slug}}-${{var.environment}}"
}}

resource "aws_s3_bucket_versioning" "flight_recorder" {{
  bucket = aws_s3_bucket.flight_recorder.id
  versioning_configuration {{ status = "Enabled" }}
}}

resource "aws_s3_bucket_server_side_encryption_configuration" "flight_recorder" {{
  bucket = aws_s3_bucket.flight_recorder.id
  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.evidence.arn
    }}
  }}
}}

resource "aws_s3_bucket_object_lock_configuration" "flight_recorder" {{
  bucket = aws_s3_bucket.flight_recorder.id
  rule {{
    default_retention {{
      mode = "GOVERNANCE"
      days = 2555  # 7 years
    }}
  }}
}}

resource "aws_s3_bucket_public_access_block" "flight_recorder" {{
  bucket                  = aws_s3_bucket.flight_recorder.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}}

resource "aws_kms_key" "evidence" {{
  description         = "ADAM Flight Recorder encryption"
  enable_key_rotation = true
}}
'''

    def _tf_kms(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM KMS - Cryptographic Authorization Vault

variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}

resource "aws_kms_key" "adam_vault" {{
  description             = "ADAM Cryptographic Authorization Vault"
  key_usage               = "SIGN_VERIFY"
  customer_master_key_spec = "RSA_4096"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {{ Name = "adam-crypto-vault-${{var.environment}}" }}
}}

resource "aws_kms_alias" "adam_vault" {{
  name          = "alias/adam-crypto-vault-${{var.environment}}"
  target_key_id = aws_kms_key.adam_vault.key_id
}}

resource "aws_kms_key" "adam_data" {{
  description         = "ADAM data encryption key"
  enable_key_rotation = true
  tags = {{ Name = "adam-data-key-${{var.environment}}" }}
}}
'''

    def _tf_bedrock(self) -> str:
        return f'''{self.header_comment("#")}
# ADAM Bedrock - AI services for agent reasoning

variable "environment" {{ type = string }}
variable "company_slug" {{ type = string }}

# Note: AWS Bedrock model access is configured via the console.
# This Terraform provisions the guardrails and custom model imports.

resource "aws_bedrock_guardrail" "adam" {{
  name        = "adam-governance-guardrail-${{var.environment}}"
  description = "ADAM governance guardrail for agent reasoning"

  blocked_input_messaging  = "This request violates ADAM governance policy."
  blocked_outputs_messaging = "This response was blocked by ADAM governance."

  content_policy_config {{
    filters_config {{
      type            = "SEXUAL"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }}
    filters_config {{
      type            = "VIOLENCE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }}
    filters_config {{
      type            = "HATE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }}
  }}
}}
'''

    def _cloudformation(self) -> str:
        return f'''{self.header_comment("#")}
AWSTemplateFormatVersion: '2010-09-09'
Description: >
  ADAM DNA Deployment Specification - AWS Stack
  Company: {self.company_name}
  Platform: AWS (Warm Standby / Primary)

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [dev, staging, production]
  CompanySlug:
    Type: String
    Default: {self.company_slug}
  PrimaryRegion:
    Type: String
    Default: us-east-1

Resources:
  # VPC for ADAM
  AdamVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsSupport: true
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub "vpc-adam-${{CompanySlug}}-${{Environment}}"
        - Key: adam-company
          Value: "{self.company_name}"

  # Neptune Cluster for CORE Graph
  CoreGraphCluster:
    Type: AWS::Neptune::DBCluster
    Properties:
      DBClusterIdentifier: !Sub "adam-core-${{CompanySlug}}-${{Environment}}"
      EngineVersion: "1.3.1.0"
      StorageEncrypted: true
      DeletionProtection: true
      BackupRetentionPeriod: 35
      Tags:
        - Key: adam-component
          Value: core-graph

  # S3 Bucket for Flight Recorder
  FlightRecorderBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "adam-flight-recorder-${{CompanySlug}}-${{Environment}}"
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: aws:kms
      ObjectLockEnabled: true
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

  # EKS Cluster for Agent Mesh
  AgentMeshCluster:
    Type: AWS::EKS::Cluster
    Properties:
      Name: !Sub "eks-adam-${{CompanySlug}}-${{Environment}}"
      Version: "1.29"
      RoleArn: !GetAtt EKSClusterRole.Arn
      ResourcesVpcConfig:
        SubnetIds:
          - !Ref PrivateSubnet1
          - !Ref PrivateSubnet2
          - !Ref PrivateSubnet3
        EndpointPrivateAccess: true
        EndpointPublicAccess: false
      EncryptionConfig:
        - Provider:
            KeyArn: !GetAtt EKSKey.Arn
          Resources: [secrets]

  EKSClusterRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub "adam-eks-cluster-${{Environment}}"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: eks.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

  EKSKey:
    Type: AWS::KMS::Key
    Properties:
      Description: ADAM EKS secrets encryption
      EnableKeyRotation: true

  # Private Subnets
  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref AdamVPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs ""]

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref AdamVPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs ""]

  PrivateSubnet3:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref AdamVPC
      CidrBlock: 10.0.3.0/24
      AvailabilityZone: !Select [2, !GetAZs ""]

Outputs:
  VPCId:
    Value: !Ref AdamVPC
  EKSClusterName:
    Value: !Ref AgentMeshCluster
  CoreGraphEndpoint:
    Value: !GetAtt CoreGraphCluster.Endpoint
  FlightRecorderBucket:
    Value: !Ref FlightRecorderBucket
'''

    def _aws_config(self) -> Dict[str, Any]:
        return {
            "adam_deployment": {
                "platform": "aws",
                "company": self.company_name,
                "version": "1.1",
                "generated": self.timestamp,
                "role": "warm-standby",
            },
            "governance_plane": {
                "core_engine": {
                    "database": "neptune-gremlin",
                    "instance_class": "db.r6g.4xlarge",
                    "replicas": 3,
                },
                "flight_recorder": {
                    "storage": "s3-object-lock",
                    "encryption": "kms",
                    "retention_years": 7,
                },
                "crypto_vault": {"service": "kms", "key_spec": "RSA_4096"},
            },
            "agent_mesh": {
                "orchestration": "eks",
                "total_agents": self.total_agents(),
                "node_groups": {
                    "governance": {"instance_type": "m6i.4xlarge", "min": 3, "max": 10},
                    "agent_mesh": {"instance_type": "m6i.8xlarge", "min": 3, "max": 50},
                    "gpu": {"instance_type": "p4d.24xlarge", "min": 1, "max": 20},
                },
            },
            "ai_services": {
                "provider": "bedrock",
                "models": {
                    "reasoning": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "execution": "anthropic.claude-3-haiku-20240307-v1:0",
                    "deep_reasoning": "anthropic.claude-3-opus-20240229-v1:0",
                },
            },
            "boss_config": {
                "dimensions": self.get_boss_dimensions(),
                "thresholds": self.get_boss_thresholds(),
            },
        }

    def _aws_values(self) -> Dict[str, Any]:
        return {
            "global": {
                "company": self.company_name,
                "platform": "aws",
                "role": "warm-standby",
            },
            "coreEngine": {
                "neptune": {"enabled": True, "instanceClass": "db.r6g.4xlarge"},
            },
            "bossScoring": {
                "dimensions": self.get_boss_dimensions(),
                "thresholds": self.get_boss_thresholds(),
            },
            "agentMesh": {"replicaCount": 3},
        }
