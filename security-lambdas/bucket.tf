data "aws_caller_identity" "current" {
}

data "aws_region" "current" {
}

resource "aws_s3_bucket" "open-pocketsoc-files-bucket" {
  bucket        = "open-pocketsoc-files-${var.owner}"
  force_destroy = "true"
}

resource "aws_s3_bucket_ownership_controls" "open-pocketsoc-files-bucket-ownership-controls" {
  bucket = aws_s3_bucket.open-pocketsoc-files-bucket.id
  rule {
    object_ownership = "ObjectWriter"
  }
  depends_on = [aws_s3_bucket.open-pocketsoc-files-bucket]
}

resource "aws_s3_bucket_acl" "open-pocketsoc-files-bucket-acl" {
  bucket     = aws_s3_bucket.open-pocketsoc-files-bucket.id
  acl        = "private"
  depends_on = [aws_s3_bucket_ownership_controls.open-pocketsoc-files-bucket-ownership-controls]
}

resource "aws_s3_bucket_public_access_block" "open-pocketsoc-files-bucket-public-access-block" {
  bucket                  = aws_s3_bucket.open-pocketsoc-files-bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  depends_on              = [aws_s3_bucket_acl.open-pocketsoc-files-bucket-acl]
}

resource "aws_s3_bucket_versioning" "open-pocketsoc-files-bucket-versioning" {
  bucket = aws_s3_bucket.open-pocketsoc-files-bucket.id
  versioning_configuration {
    status = "Enabled"
  }
  depends_on = [aws_s3_bucket.open-pocketsoc-files-bucket]
}

resource "aws_s3_bucket_server_side_encryption_configuration" "open-pocketsoc-files-bucket-encryption" {
  bucket = aws_s3_bucket.open-pocketsoc-files-bucket.bucket
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
  depends_on = [aws_s3_bucket.open-pocketsoc-files-bucket]
}

resource "aws_s3_object" "config-files-objects" {
  for_each = fileset("config_files/", "*")
  bucket   = aws_s3_bucket.open-pocketsoc-files-bucket.id
  key      = each.value
  source   = "config_files/${each.value}"
  etag     = filemd5("config_files/${each.value}")
}

