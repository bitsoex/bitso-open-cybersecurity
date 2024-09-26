provider "aws" {
  region = "us-east-2"
  assume_role {
    role_arn     = "arn:aws:iam::183832830806:role/aws-provisioner"
    session_name = "mysession"
  }
  default_tags {
    tags = local.default_tags
  }
}
