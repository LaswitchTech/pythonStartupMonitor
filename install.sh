#!/bin/bash

# Function to prompt the user for MariaDB installation
prompt_smtp() {
  while true; do
    read -p "Please specify the host to be used for the SMTP Connection: " smtp_host
    if [[ -n "$smtp_host" ]]; then break; fi
    echo "SMTP Host cannot be empty."
  done

  while true; do
    read -p "Please specify the port to be used for the SMTP Connection: " smtp_port
    if [[ "$smtp_port" =~ ^[0-9]+$ ]]; then break; fi
    echo "Please enter a valid port number."
  done

  while true; do
    read -p "Please specify the username to be used for the SMTP Connection: " smtp_username
    if [[ -n "$smtp_username" ]]; then break; fi
    echo "SMTP Username cannot be empty."
  done

  while true; do
    read -sp "Please specify the password to be used for the SMTP Connection: " smtp_password
    echo
    if [[ -n "$smtp_password" ]]; then break; fi
    echo "SMTP Password cannot be empty."
  done

  while true; do
    read -p "Please specify the recipient of the notifications: " recipient
    if [[ "$recipient" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$ ]]; then break; fi
    echo "Please enter a valid email address."
  done
}

# Function to update the system
update_system() {
  echo "Updating the system..."
  sudo apt-get update && sudo apt-get upgrade -y
  if [[ $? -ne 0 ]]; then
    echo "System update failed. Exiting."
    exit 1
  fi
  echo "System update completed."
}

# Function to install dependencies
install_dependencies() {
  echo "Installing dependencies..."
  sudo apt-get install -y git python3 python3-pip
  if [[ $? -ne 0 ]]; then
    echo "Failed to install dependencies. Exiting."
    exit 1
  fi

  echo "Installing python libraries..."
  sudo apt-get install -y python3-psutil
  if [[ $? -ne 0 ]]; then
    echo "Failed to install Python libraries. Exiting."
    exit 1
  fi

  echo "Dependencies installation completed."
}

# Function to create the configuration file
create_config_file() {
  config_file="config.cfg"
  if [ ! -f "$config_file" ]; then
    echo "Creating configuration file: $config_file"
    cat <<EOF > $config_file
{
    "smtp_host": "$smtp_host",
    "smtp_port": "$smtp_port",
    "smtp_username": "$smtp_username",
    "smtp_password": "$smtp_password",
    "recipient": "$recipient"
}
EOF
    echo "Configuration file created."
  else
    echo "Configuration file already exists."
  fi
}

# Main script execution
update_system
install_dependencies
prompt_smtp
create_config_file

echo "Installation process completed."
