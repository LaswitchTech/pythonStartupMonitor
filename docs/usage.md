# Usage
To use the script, the virtual environment must be loaded. A ``run.sh`` bash wrapper is included.
## Help Message
```
$ ./run.sh --help
usage: monitor.py [-h] [--console] [--verbose] [--install] [--uninstall] [--start] [--stop] [--configure]

Raspberry Pi Startup Info Script

options:
  -h, --help   show this help message and exit
  --console    Only display the information without sending the notification.
  --verbose    Echo the sensor readings to the console.
  --install    Install the script as a systemd service.
  --uninstall  Uninstall the script as a systemd service.
  --start      Start the service if installed.
  --stop       Stop the service if installed.
  --configure  Configure the script settings.

Examples:
  python3 ./monitor.py --verbose
  python3 ./monitor.py --console
  python3 ./monitor.py --console --verbose
  python3 ./monitor.py

The script allows you to:
- Display the information without sending the notification --console
- Print the readings to the console with --verbose
- Install the script as a service with --install
- Uninstall the service with --uninstall
- start the service with --start
- stop the service with --stop
- Configure the script with --configure
```
