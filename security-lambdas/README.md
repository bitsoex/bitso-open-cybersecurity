# Bitso - Open Security Lambdas

This respository contains a basic structure of AWS Lambdas to execute security tasks.

# Local Environment 

To be able to execute and create lambdas we need to have the next tools and libraries installed:

Python3
Terraform
AWS CLI


In order to set up the requirements, run the shell script for your OS the directory: 
./env_set_up

For Linux execute:
linux_env.sh

For MacOS execute:

mac_env.sh

# Lamnda layers

In order to create an updated lambda layer to add new librearies needed for the python lambdas.

1.- go to directory "lambda layers"

2.- modify the layer_creation.sh file on line 12 and add the needed libraries.

3.- execute the script layer_creation.sh and a new layer will be created with the new librearies included.

# AWS Console 

For Nerdear.la workshop atendees, we will be providing temporal users for our AWS test console.

For nont Nerdear.la workshop atendees, AWS Console and users can be created using the next references.

An AWS account and a AWS user with propper permissions and Programatic Access is needed.

The next links shows how to create a AWS Account, create programatic access and configure AWS CLI.

aws acccount creation:
https://docs.aws.amazon.com/streams/latest/dev/setting-up.html

granting programatic access:

https://docs.aws.amazon.com/workspaces-web/latest/adminguide/getting-started-iam-user-access-keys.html

AWS CLI configuration: 

https://docs.aws.amazon.com/cli/v1/userguide/cli-chap-configure.html
