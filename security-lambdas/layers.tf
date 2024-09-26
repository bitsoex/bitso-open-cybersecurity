
resource "aws_s3_object" "pocketsoc-deps-layer-zip" {
  bucket = aws_s3_bucket.pocketsoc-files-bucket.id
  key    = "lambda_layers/${local.layer_name}.zip"
  source = "${local.layer_zip_path}${local.layer_name}.zip"
  etag   = "${local.layer_zip_path}${local.layer_name}.zip.output_md5"
}

# create lambda layer from s3 object
resource "aws_lambda_layer_version" "pocketsoc-deps-layer" {
  s3_bucket           = aws_s3_bucket.pocketsoc-files-bucket.id
  s3_key              = aws_s3_object.pocketsoc-deps-layer-zip.key
  layer_name          = local.layer_name
  compatible_runtimes = ["python3.10"]
  skip_destroy        = true
  source_code_hash    = "${local.layer_zip_path}${local.layer_name}.zip.output_base64sha256"
  depends_on          = [aws_s3_object.pocketsoc-deps-layer-zip]
}
