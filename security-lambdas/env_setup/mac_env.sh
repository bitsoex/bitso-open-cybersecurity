#!/bin/bash

# Function to check if Homebrew is installed, and install it if necessary
install_homebrew() {
  if ! command -v brew &>/dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  else
    echo "Homebrew is already installed."
  fi
}

# Function to install Terraform
install_terraform() {
  if ! command -v terraform &>/dev/null; then
    echo "Installing Terraform..."
    brew tap hashicorp/tap
    brew install hashicorp/tap/terraform
  else
    echo "Terraform is already installed."
  fi
}

# Function to install Python 3.10
install_python() {
  if ! command -v python3.10 &>/dev/null; then
    echo "Installing Python 3.10..."
    brew install python@3.10
  else
    echo "Python 3.10 is already installed."
  fi
}

# Function to install AWS CLI
install_awscli() {
  if ! command -v aws &>/dev/null; then
    echo "Installing AWS CLI..."
    brew install awscli
  else
    echo "AWS CLI is already installed."
  fi
}

# Function to install specific Python libraries using pip3.10
install_python_libraries() {
  echo "Installing Python libraries (boto3, requests)..."
  pip3.10 install boto3 requests
}

# Main script execution
echo "Starting installation process..."

# Install Homebrew (if not already installed)
install_homebrew

# Install Terraform
install_terraform

# Install Python 3.10
install_python

# Install AWS CLI
install_awscli

# Install Python libraries
install_python_libraries

echo "Installation completed."