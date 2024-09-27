resource "aws_iam_policy" "vulmon-lambda-policy" {
  name   = "vulmon-lambda-policy-${var.owner}-${random_id.random_string.hex}"
  policy = <<EOF
{
      "Version": "2012-10-17",
      "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "events:DisableRule"
            ],
            "Resource": [
              "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
              "${aws_secretsmanager_secret.slack-channel-rss-int1.arn}"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
              "s3:PutObject",
              "s3:GetObject"
            ],
            "Resource": [
              "${aws_s3_bucket.open-pocketsoc-files-bucket.arn}/*"
            ]
        }
      ]
}
EOF
}

resource "aws_iam_role" "vulmon-lambda-role" {
  name               = "vulmon-lambda-role-${var.owner}-${random_id.random_string.hex}"
  description        = "Role to allow Lambda write logs"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "vulmon-lambda-role-attachment" {
  role       = aws_iam_role.vulmon-lambda-role.name
  policy_arn = aws_iam_policy.vulmon-lambda-policy.arn
}

resource "aws_cloudwatch_log_group" "vulmon-lambda-loggroup" {
  name              = "/aws/lambda/${aws_lambda_function.vulmon-lambda.function_name}-${var.owner}-${random_id.random_string.hex}"
  retention_in_days = "365"
}

data "archive_file" "vulmon-lambda-package" {
  type        = "zip"
  source_file = "${path.module}/vulmon-lambda.py"
  output_path = "vulmon-lambda.zip"
}

resource "aws_lambda_function" "vulmon-lambda" {
  filename         = "vulmon-lambda.zip"
  function_name    = "vulmon-lambda-${var.owner}-${random_id.random_string.hex}"
  description      = "Lambda function to retrieve Vulnerabilities Feeds from different sources"
  role             = aws_iam_role.vulmon-lambda-role.arn
  handler          = "vulmon-lambda.main"
  source_code_hash = data.archive_file.vulmon-lambda-package.output_base64sha256
  memory_size      = 1024
  runtime          = "python3.10"
  timeout          = 900
  layers           = [aws_lambda_layer_version.open-pocketsoc-deps-layer.arn]
}

# Trigger resources and configurations
resource "aws_cloudwatch_event_rule" "vulmon-lambda-hourly-schedule" {
  name                = "vulmon-hourly-schedule-cloudwatch-event-${var.owner}-${random_id.random_string.hex}"
  description         = "Executes VULMon Lambda function hourly"
  schedule_expression = "cron(0 12 ? * * *)"
  is_enabled          = "true"
}

resource "aws_cloudwatch_event_target" "vulmon-cloudwatch-target" {
  arn  = aws_lambda_function.vulmon-lambda.arn
  rule = aws_cloudwatch_event_rule.vulmon-lambda-hourly-schedule.id
}

resource "aws_lambda_permission" "vulmon-lambda-allow-cloudwatch-event" {
  statement_id  = "AllowExecutionFromCloudWatchWeekly-${var.owner}-${random_id.random_string.hex}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.vulmon-lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.vulmon-lambda-hourly-schedule.arn
}