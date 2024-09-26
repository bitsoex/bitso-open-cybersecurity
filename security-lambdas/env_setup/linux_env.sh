#!/bin/bash

# Function to check the OS type and package manager
detect_os() {
  if [ -f /etc/debian_version ]; then
    echo "Debian-based OS detected."
    OS="debian"
  elif [ -f /etc/redhat-release ]; then
    echo "RPM-based OS detected."
    OS="rpm"
  else
    echo "Unsupported OS."
    exit 1
  fi
}

# Function to install packages on Debian-based systems
install_debian() {
  sudo apt-get update

  # Install Python 3.10
  if ! command -v python3.10 &>/dev/null; then
    echo "Installing Python 3.10..."
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install -y python3.10 python3.10-pip
  else
    echo "Python 3.10 is already installed."
  fi

  # Install AWS CLI
  if ! command -v aws &>/dev/null; then
    echo "Installing AWS CLI..."
    sudo apt-get install -y awscli
  else
    echo "AWS CLI is already installed."
  fi

  # Install Terraform
  if ! command -v terraform &>/dev/null; then
    echo "Installing Terraform..."
    sudo apt-get install -y gnupg software-properties-common curl
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
    sudo apt-get update && sudo apt-get install -y terraform
  else
    echo "Terraform is already installed."
  fi

  # Install specific Python libraries
  echo "Installing Python libraries (boto3, requests)..."
  pip3.10 install boto3 requests
}

# Function to install packages on RPM-based systems
install_rpm() {
  sudo yum update -y

  # Install Python 3.10
  if ! command -v python3.10 &>/dev/null; then
    echo "Installing Python 3.10..."
    sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel
    sudo yum install -y wget
    cd /usr/src
    wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz
    tar xzf Python-3.10.0.tgz
    cd Python-3.10.0
    sudo ./configure --enable-optimizations
    sudo make altinstall
    cd ~
  else
    echo "Python 3.10 is already installed."
  fi

  # Install AWS CLI
  if ! command -v aws &>/dev/null; then
    echo "Installing AWS CLI..."
    sudo yum install -y awscli
  else
    echo "AWS CLI is already installed."
  fi

  # Install Terraform
  if ! command -v terraform &>/dev/null; then
    echo "Installing Terraform..."
    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
    sudo yum -y install terraform
  else
    echo "Terraform is already installed."
  fi

  # Install specific Python libraries
  echo "Installing Python libraries (boto3, requests)..."
  pip3.10 install boto3 requests
}

# Main script execution
echo "Starting installation process..."

# Detect OS type
detect_os

# Run the appropriate installation function based on OS type
if [ "$OS" = "debian" ]; then
  install_debian
elif [ "$OS" = "rpm" ]; then
  install_rpm
fi

echo "Installation completed."