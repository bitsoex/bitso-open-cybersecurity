resource "aws_iam_policy" "pwnmon-lambda-policy" {
  name   = "pwnmon-lambda-policy-${var.owner}-${random_id.random_string.hex}"
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
              "${aws_secretsmanager_secret.slack-channel-rss-int1.arn}",
              "${aws_secretsmanager_secret.haveibeenpwned_key1.arn}"
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

resource "aws_iam_role" "pwnmon-lambda-role" {
  name               = "pwnmon-lambda-role-${var.owner}-${random_id.random_string.hex}"
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

resource "aws_iam_role_policy_attachment" "pwnmon-lambda-role-attachment" {
  role       = aws_iam_role.pwnmon-lambda-role.name
  policy_arn = aws_iam_policy.pwnmon-lambda-policy.arn
}

resource "aws_cloudwatch_log_group" "pwnmon-lambda-loggroup" {
  name              = "/aws/lambda/${aws_lambda_function.pwnmon-lambda.function_name}-${var.owner}-${random_id.random_string.hex}"
  retention_in_days = "365"
}

data "archive_file" "pwnmon-lambda-package" {
  type        = "zip"
  source_file = "${path.module}/pwnmon-lambda.py"
  output_path = "pwnmon-lambda.zip"
}

resource "aws_lambda_function" "pwnmon-lambda" {
  filename         = "pwnmon-lambda.zip"
  function_name    = "pwnmon-lambda-${var.owner}-${random_id.random_string.hex}"
  description      = "Lambda function to identify if an email has been found in a data breach"
  role             = aws_iam_role.pwnmon-lambda-role.arn
  handler          = "pwnmon-lambda.main"
  source_code_hash = data.archive_file.pwnmon-lambda-package.output_base64sha256
  memory_size      = 1024
  runtime          = "python3.10"
  timeout          = 900
  layers           = [aws_lambda_layer_version.open-pocketsoc-deps-layer.arn]
}

# Trigger resources and configurations
resource "aws_cloudwatch_event_rule" "pwnmon-lambda-hourly-schedule" {
  name                = "pwnmon-hourly-schedule-cloudwatch-event-${var.owner}-${random_id.random_string.hex}"
  description         = "Executes VULMon Lambda function hourly"
  schedule_expression = "cron(0 12 ? * * *)"
  is_enabled          = "true"
}

resource "aws_cloudwatch_event_target" "pwnmon-cloudwatch-target" {
  arn  = aws_lambda_function.pwnmon-lambda.arn
  rule = aws_cloudwatch_event_rule.pwnmon-lambda-hourly-schedule.id
}

resource "aws_lambda_permission" "pwnmon-lambda-allow-cloudwatch-event" {
  statement_id  = "AllowExecutionFromCloudWatchWeekly-${var.owner}-${random_id.random_string.hex}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pwnmon-lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.pwnmon-lambda-hourly-schedule.arn
}