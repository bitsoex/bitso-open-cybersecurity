resource "aws_iam_policy" "rssmon-lambda-policy" {
  name   = "rssmon-lambda-policy"
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
              "${aws_secretsmanager_secret.slack-channel-rss-int.arn}"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
              "s3:PutObject",
              "s3:GetObject"
            ],
            "Resource": [
              "${aws_s3_bucket.pocketsoc-files-bucket.arn}/*"
            ]
        }
      ]
}
EOF
}

resource "aws_iam_role" "rssmon-lambda-role" {
  name               = "rssmon-lambda-role"
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

resource "aws_iam_role_policy_attachment" "rssmon-lambda-role-attachment" {
  role       = aws_iam_role.rssmon-lambda-role.name
  policy_arn = aws_iam_policy.rssmon-lambda-policy.arn
}

resource "aws_cloudwatch_log_group" "rssmon-lambda-loggroup" {
  name              = "/aws/lambda/${aws_lambda_function.rssmon-lambda.function_name}"
  retention_in_days = 365
}

data "archive_file" "rssmon-lambda-package" {
  type        = "zip"
  source_file = "${path.module}/rssmon-lambda.py"
  output_path = "rssmon-lambda.zip"
}

resource "aws_lambda_function" "rssmon-lambda" {
  filename         = "rssmon-lambda.zip"
  function_name    = "rssmon-lambda"
  description      = "Lambda function to retrieve RSS news from different sources"
  role             = aws_iam_role.rssmon-lambda-role.arn
  handler          = "rssmon-lambda.main"
  source_code_hash = data.archive_file.rssmon-lambda-package.output_base64sha256
  memory_size      = 1024
  runtime          = "python3.10"
  timeout          = 900
  layers           = [aws_lambda_layer_version.pocketsoc-deps-layer.arn]
}

# Trigger resources and configurations
resource "aws_cloudwatch_event_rule" "rssmon-lambda-hourly-schedule" {
  name                = "rssmon-hourly-schedule-cloudwatch-event"
  description         = "Executes RSSMon Lambda function hourly"
  schedule_expression = "cron(0 * * * ? *)"
  is_enabled          = true
}

resource "aws_cloudwatch_event_target" "rssmon-cloudwatch-target" {
  arn  = aws_lambda_function.rssmon-lambda.arn
  rule = aws_cloudwatch_event_rule.rssmon-lambda-hourly-schedule.id
}

resource "aws_lambda_permission" "rssmon-lambda-allow-cloudwatch-event" {
  statement_id  = "AllowExecutionFromCloudWatchHourly"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rssmon-lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rssmon-lambda-hourly-schedule.arn
}