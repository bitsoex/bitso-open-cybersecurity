resource "aws_iam_policy" "intmon-lambda-policy" {
  name   = "intmon-lambda-policy-${var.owner}-${random_id.random_string.hex}"
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
              "${aws_secretsmanager_secret.intel-otx-key1.arn}",
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

resource "aws_iam_role" "intmon-lambda-role" {
  name               = "intmon-lambda-role-${var.owner}-${random_id.random_string.hex}"
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

resource "aws_iam_role_policy_attachment" "intmon-lambda-role-attachment" {
  role       = aws_iam_role.intmon-lambda-role.name
  policy_arn = aws_iam_policy.intmon-lambda-policy.arn
}

resource "aws_cloudwatch_log_group" "intmon-lambda-loggroup" {
  name              = "/aws/lambda/${aws_lambda_function.intmon-lambda.function_name}-${var.owner}-${random_id.random_string.hex}"
  retention_in_days = "365"
}

data "archive_file" "intmon-lambda-package" {
  type        = "zip"
  source_file = "${path.module}/intmon-lambda.py"
  output_path = "intmon-lambda.zip"
}

resource "aws_lambda_function" "intmon-lambda" {
  filename         = "intmon-lambda.zip"
  function_name    = "intmon-lambda-${var.owner}-${random_id.random_string.hex}"
  description      = "Lambda function to retrieve intelligence pulses from different sources"
  role             = aws_iam_role.intmon-lambda-role.arn
  handler          = "intmon-lambda.main"
  source_code_hash = data.archive_file.intmon-lambda-package.output_base64sha256
  memory_size      = 1024
  runtime          = "python3.10"
  timeout          = 900
  layers           = [aws_lambda_layer_version.open-pocketsoc-deps-layer.arn]
}

# Trigger resources and configurations
resource "aws_cloudwatch_event_rule" "intmon-lambda-hourly-schedule" {
  name                = "intmon-hourly-schedule-cloudwatch-event-${var.owner}-${random_id.random_string.hex}"
  description         = "Executes INTMon Lambda function hourly"
  schedule_expression = "cron(0 12 ? * * *)"
  is_enabled          = "true"
}

resource "aws_cloudwatch_event_target" "intmon-cloudwatch-target" {
  arn  = aws_lambda_function.intmon-lambda.arn
  rule = aws_cloudwatch_event_rule.intmon-lambda-hourly-schedule.id
}

resource "aws_lambda_permission" "intmon-lambda-allow-cloudwatch-event" {
  statement_id  = "AllowExecutionFromCloudWatchWeekly-${var.owner}-${random_id.random_string.hex}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.intmon-lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.intmon-lambda-hourly-schedule.arn
}