resource "aws_secretsmanager_secret" "haveibeenpwned_key" {
  name = "bitso/open_pocketsoc/haveibeenpwned_api_key"
}

resource aws_secretsmanager_secret intel-otx-key{
name = "bitso/open_pocketsoc/intel_otx_key"
}

resource aws_secretsmanager_secret slack-channel-rss-int{
name = "bitso/open_pocketsoc/slack_channel_rss_int"
}

resource aws_secretsmanager_secret whale-tx{
  name = "bitso/open_pocketsoc/whale-tx"
}

