#!/bin/bash

# Variables
PYTHON_VERSION="3.10"
LAYER_DIR="layer/python/lib/python${PYTHON_VERSION}/site-packages"
ZIP_FILE="bitso-open-lambda-layer.zip"

# Create the necessary directory structure
mkdir -p $LAYER_DIR

# Install Python dependencies (modify the packages as needed)
pip3.10 install requests boto3 websocket websocket-client feedparser ssl json socket -t $LAYER_DIR

# Create a zip file named bits-open-lambda-layer.zip
cd layer
zip -r ../$ZIP_FILE .
cd ..

# Output the result
echo "Lambda layer for Python ${PYTHON_VERSION} created and zipped as $ZIP_FILE."
