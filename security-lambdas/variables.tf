variable "owner" {
  default = "ownername"
}

resource "random_id" "random_string" {
  byte_length = 7
}