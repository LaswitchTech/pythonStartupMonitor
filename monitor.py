#!/usr/bin/env python3

import smtplib
import socket
import psutil
import json
import os
import sys
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import datetime
import time
from email.utils import formatdate

# Function to load the configuration file
def load_config(config_file='config.cfg'):
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
        return config
    else:
        print(f"Configuration file {config_file} not found.")
        return None

# Function to check network connectivity
def wait_for_network(timeout=60, interval=5):
    start_time = time.time()
    while True:
        try:
            # Attempt to connect to Google's DNS server
            socket.create_connection(("8.8.8.8", 53))
            print("Network connected.")
            return True
        except OSError:
            print("Network not connected, waiting...")
            if time.time() - start_time >= timeout:
                print("Network connection timed out.")
                return False
            time.sleep(interval)

# Function to get system information
def get_system_info():
    hostname = socket.gethostname()

    # Getting the primary IP address
    ip_address = None
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                ip_address = addr.address
                break
        if ip_address:
            break

    if not ip_address:
        ip_address = "Unavailable"

    # Converting uptime to a human-readable format
    uptime_seconds = psutil.boot_time()
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(uptime_seconds)
    uptime_str = str(uptime).split('.')[0]  # Removing microseconds

    return f"""
    Hostname: {hostname}
    IP Address: {ip_address}
    Uptime: {uptime_str}
    """

# Function to send an email
def send_email(subject, body, config):
    msg = MIMEMultipart()
    msg['From'] = config['smtp_username']
    msg['To'] = config['recipient']
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)  # Adding Date header

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(config['smtp_host'], config['smtp_port'])
        server.starttls()
        server.login(config['smtp_username'], config['smtp_password'])
        text = msg.as_string()
        server.sendmail(config['smtp_username'], config['recipient'], text)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Function to install the script as a systemd service
def install_service():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    service_content = f"""
    [Unit]
    Description=Send Raspberry Pi Startup Information
    After=network.target

    [Service]
    WorkingDirectory={script_directory}
    ExecStart=/usr/bin/python3 {script_directory}/monitor.py

    [Install]
    WantedBy=multi-user.target
    """
    service_file_path = '/etc/systemd/system/pi_startup_info.service'

    try:
        # Write the service file using sudo
        with open('/tmp/pi_startup_info.service', 'w') as service_file:
            service_file.write(service_content)

        subprocess.run(['sudo', 'mv', '/tmp/pi_startup_info.service', service_file_path], check=True)
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'pi_startup_info.service'], check=True)
        print("Service installed and enabled.")
    except Exception as e:
        print(f"Failed to install service: {e}")
        sys.exit(1)

# Function to uninstall the systemd service
def uninstall_service():
    subprocess.run(['sudo', 'systemctl', 'disable', 'pi_startup_info.service'])
    subprocess.run(['sudo', 'rm', '/etc/systemd/system/pi_startup_info.service'])
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'])
    print("Service uninstalled.")

# Function to configure the script settings
def configure_settings():
    config_file = 'config.cfg'
    smtp_host = input("Please specify the host to be used for the SMTP Connection: ")
    smtp_port = input("Please specify the port to be used for the SMTP Connection: ")
    smtp_username = input("Please specify the username to be used for the SMTP Connection: ")
    smtp_password = input("Please specify the password to be used for the SMTP Connection: ")
    recipient = input("Please specify the recipient of the notifications: ")

    config = {
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_username": smtp_username,
        "smtp_password": smtp_password,
        "recipient": recipient
    }

    with open(config_file, 'w') as file:
        json.dump(config, file, indent=4)

    print(f"Configuration saved to {config_file}.")

# Main function
def main():
    parser = argparse.ArgumentParser(description="Raspberry Pi Startup Info Script")
    parser.add_argument('--console', action='store_true', help="Only display the information without sending the notification.")
    parser.add_argument('--verbose', action='store_true', help="Echo the information to the console.")
    parser.add_argument('--install', action='store_true', help="Install the script as a systemd service.")
    parser.add_argument('--uninstall', action='store_true', help="Uninstall the script as a systemd service.")
    parser.add_argument('--configure', action='store_true', help="Configure the script settings.")

    args = parser.parse_args()

    if args.install:
        install_service()
    elif args.uninstall:
        uninstall_service()
    elif args.configure:
        configure_settings()
    else:
        if not wait_for_network():
            print("Network is not available. Exiting.")
            return

        config = load_config()
        if not config:
            print("Configuration file not found. Please run with --configure to set up.")
            return

        system_info = get_system_info()

        if args.verbose or args.console:
            print(system_info)

        if not args.console:
            send_email("Raspberry Pi Startup Info", system_info, config)

if __name__ == "__main__":
    main()
