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

# Default configuration
default_config = {
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "smtp_username": "user@example.com",
    "smtp_password": "",
    "recipient": "alert@example.com"
}

script_dir = os.path.dirname(os.path.abspath(__file__))
script_name = sys.argv[0]
venv_path = os.path.join(script_dir, ".env/bin/activate")
config_file = os.path.join(script_dir, "config.cfg")
service_name = "pi_startup_info"

def is_service_installed():
    result = subprocess.run(['systemctl', 'list-units', '--type=service', '--all'], stdout=subprocess.PIPE)
    return f'{service_name}.service' in result.stdout.decode()

def load_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
    else:
        return default_config

def save_config(config):
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    if args.verbose:
        print("Configuration saved.")

def configure():
    config = load_config()
    config['smtp_host'] = input(f"SMTP Server (current: {config['smtp_host']}): ") or config['smtp_host']
    config['smtp_port'] = int(input(f"SMTP Port (current: {config['smtp_port']}): ") or config['smtp_port'])
    config['smtp_username'] = input(f"SMTP Username (current: {config['smtp_username']}): ") or config['smtp_username']
    config['smtp_password'] = input("SMTP Password: ") or config['smtp_password']
    config['recipient'] = input(f"Recipient (current: {config['recipient']}): ") or config['recipient']
    save_config(config)
    if args.verbose:
        print("Configuration saved.")

def log_error(message):
    with open(os.path.join(script_dir, 'error.log'), 'a') as f:
        f.write(f"{datetime.datetime.now()} - {message}\n")

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
        if args.verbose:
            print("Email sent successfully!")
    except Exception as e:
        log_error(f"Failed to send email: {e}")
        if args.verbose:
            print(f"Failed to send email: {e}")

# Function to install the script as a systemd service
def create_service():
    service_content = f"""
    [Unit]
    Description=Send Raspberry Pi Startup Information
    After=network.target

    [Service]
    Type=simple
    WorkingDirectory={script_dir}
    ExecStart=/usr/bin/python3 {script_dir}/monitor.py

    [Install]
    WantedBy=multi-user.target
    """
    service_file_path = f'/etc/systemd/system/{service_name}.service'

    try:
        # Write the service file using sudo
        with open(f'/tmp/{service_name}.service', 'w') as service_file:
            service_file.write(service_content)

        subprocess.run(['sudo', 'mv', f'/tmp/{service_name}.service', service_file_path], check=True)
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', f'{service_name}.service'], check=True)
        subprocess.run(['sudo', 'systemctl', 'start', f'{service_name}.service'], check=True)
        if args.verbose:
            print("Service installed, enabled and started.")
    except Exception as e:
        log_error(f"Failed to install service: {e}")
        if args.verbose:
            print(f"Failed to install service: {e}")
        sys.exit(1)

def remove_service():
    if is_service_installed():
        os.system(f'sudo systemctl stop {service_name}.service')
        os.system(f'sudo systemctl disable {service_name}.service')
        os.system(f'sudo rm /etc/systemd/system/{service_name}.service')
        os.system('sudo systemctl daemon-reload')
        if args.verbose:
            print("Service removed.")
    else:
        if args.verbose:
            print(f"Service '{service_name}.service' is not installed.")

def start_service():
    if is_service_installed():
        subprocess.run(['sudo', 'systemctl', 'start', f'{service_name}.service'])
        if args.verbose:
            print("Service started.")
    else:
        if args.verbose:
            print(f"Service '{service_name}.service' is not installed.")

def stop_service():
    if is_service_installed():
        subprocess.run(['sudo', 'systemctl', 'stop', f'{service_name}.service'])
        if args.verbose:
            print("Service stopped.")
    else:
        if args.verbose:
            print(f"Service '{service_name}.service' is not installed.")

# Function to check network connectivity
def wait_for_network(timeout=60, interval=5):
    start_time = time.time()
    while True:
        try:
            # Attempt to connect to Google's DNS server
            socket.create_connection(("8.8.8.8", 53))
            if args.verbose
                print("Network connected.")
            return True
        except OSError:
            if args.verbose
                print("Network not connected, waiting...")
            if time.time() - start_time >= timeout:
                log_error("Network connection timed out.")
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

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Raspberry Pi Startup Info Script",
        epilog=f"Examples:\n"
               f"  python3 {script_name} --verbose\n"
               f"  python3 {script_name} --console\n"
               f"  python3 {script_name} --console --verbose\n"
               f"  python3 {script_name}\n\n"
               "The script allows you to:\n"
               "- Display the information without sending the notification --console\n"
               "- Print the readings to the console with --verbose\n"
               "- Install the script as a service with --install\n"
               "- Uninstall the service with --uninstall\n"
               "- start the service with --start\n"
               "- stop the service with --stop\n"
               "- Configure the script with --configure",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("--console", action="store_true", help="Only display the information without sending the notification.")
    parser.add_argument("--verbose", action="store_true", help="Echo the sensor readings to the console.")
    parser.add_argument("--install", action="store_true", help="Install the script as a systemd service.")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall the script as a systemd service.")
    parser.add_argument("--configure", action="store_true", help="Configure the script settings.")
    parser.add_argument("--start", action="store_true", help="Start the service if installed.")
    parser.add_argument("--stop", action="store_true", help="Stop the service if installed.")
    parser.add_argument("--add", metavar="HOST", help="Add a host to the monitoring list.")
    parser.add_argument("--remove", metavar="HOST", help="Remove a host from the monitoring list.")

    args = parser.parse_args()

    if args.configure:
        configure()
    else:
        config = load_config()

        if args.install:
            create_service()
        elif args.uninstall:
            remove_service()
        elif args.start:
            start_service()
        elif args.stop:
            stop_service()
        else:
            try:
                if not wait_for_network():
                    print("Network is not available. Exiting.")
                    return

                system_info = get_system_info()

                if args.verbose:
                    print(system_info)

                if not args.console:
                    send_email("Raspberry Pi Startup Info", system_info, config)
            except KeyboardInterrupt:
                if args.verbose:
                    print("\nStopping...")
