resource "aws_iam_policy" "whale-tx-policy" {
  name   = "whale-tx-policy-${var.owner}-${random_id.random_string.hex}"
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
              "${aws_secretsmanager_secret.whale-tx1.arn}",
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

resource "aws_iam_role" "whale-tx-role" {
  name               = "whale-tx-role-${var.owner}-${random_id.random_string.hex}"
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

resource "aws_iam_role_policy_attachment" "whale-tx-role-attachment" {
  role       = aws_iam_role.whale-tx-role.name
  policy_arn = aws_iam_policy.whale-tx-policy.arn
}

resource "aws_cloudwatch_log_group" "whale-tx-loggroup" {
  name              = "/aws/lambda/${aws_lambda_function.whale-tx.function_name}-${var.owner}-${random_id.random_string.hex}"
  retention_in_days = 365
}

data "archive_file" "whale-tx-package" {
  type        = "zip"
  source_file = "${path.module}/whale-tx.py"
  output_path = "whale-tx.zip"
}

resource "aws_lambda_function" "whale-tx" {
  filename         = "whale-tx.zip"
  function_name    = "whale-tx-${var.owner}-${random_id.random_string.hex}"
  description      = "Lambda function to retrieve whale transactions"
  role             = aws_iam_role.whale-tx-role.arn
  handler          = "whale-tx.main"
  source_code_hash = data.archive_file.whale-tx-package.output_base64sha256
  memory_size      = 1024
  runtime          = "python3.10"
  timeout          = 900
  layers           = [aws_lambda_layer_version.open-pocketsoc-deps-layer.arn]
}

# Trigger resources and configurations
resource "aws_cloudwatch_event_rule" "whale-tx-hourly-schedule" {
  name                = "rssmon-hourly-schedule-cloudwatch-event-${var.owner}-${random_id.random_string.hex}"
  description         = "Executes whale-tx Lambda function hourly"
  schedule_expression = "cron(0 * * * ? *)"
  is_enabled          = true
}

resource "aws_cloudwatch_event_target" "whale-tx-cloudwatch-target" {
  arn  = aws_lambda_function.whale-tx.arn
  rule = aws_cloudwatch_event_rule.whale-tx-hourly-schedule.id
}

resource "aws_lambda_permission" "whale-tx-allow-cloudwatch-event" {
  statement_id  = "AllowExecutionFromCloudWatchHourly-${var.owner}-${random_id.random_string.hex}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.whale-tx.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.whale-tx-hourly-schedule.arn
}