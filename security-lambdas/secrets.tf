resource "aws_secretsmanager_secret" "haveibeenpwned_key1" {
  name = "bitso/open_pocketsoc/haveibeenpwned_api_key-${var.owner}"
}

resource aws_secretsmanager_secret intel-otx-key1{
name = "bitso/open_pocketsoc/intel_otx_key-${var.owner}"
}

resource aws_secretsmanager_secret slack-channel-rss-int1{
name = "bitso/open_pocketsoc/slack_channel_rss_int-${var.owner}"
}

resource aws_secretsmanager_secret whale-tx1{
  name = "bitso/open_pocketsoc/whale-tx-${var.owner}"
}
