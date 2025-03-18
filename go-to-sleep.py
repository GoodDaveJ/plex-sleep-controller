"""
Script Name: Plex Sleep Controller
Description: Python script to monitor Plex activity and put the server to sleep when idle
Author: David Joudrey
Version: 1.3
"""
import subprocess
import requests
import xml.etree.ElementTree as ET
import time
import os
import threading
from datetime import datetime
import configparser
import platform

# Check if running in a graphical environment
is_graphical = os.environ.get('DISPLAY') is not None

if is_graphical:
    from pynput import mouse, keyboard

# Read configuration from config.ini
config = configparser.ConfigParser()
config_file = 'config.ini'
config.read(config_file)

# Extract values from config
server_ip = config['Settings'].get('serverIp', '')
server_port = config['Settings'].get('serverPort', '')
plex_token = config['Settings'].get('plexToken', '')
sleep_timer_minutes = config['Settings'].get('sleepTimer', '')
primeTimeStart = config['Settings'].get('primeTimeStart', '')
primeTimeEnd = config['Settings'].get('primeTimeEnd', '')

minute = 60

SLEEP_TIMEOUT = int(sleep_timer_minutes) * minute if sleep_timer_minutes.isdigit() else 15 * minute  # Convert minutes to seconds

# Check for empty or unreadable variables
if not all([server_ip, server_port, plex_token]):
    missing_variables = [var for var, value in zip(['serverIp', 'serverPort', 'plexToken'], [server_ip, server_port, plex_token]) if not value]
    print(f"Error: Missing or empty values for the following variables: {missing_variables}")
    exit(1)

# Check and set default value for sleepTimer
if not sleep_timer_minutes or not sleep_timer_minutes.isdigit():
    print("Warning: sleepTimer not defined or unreadable. Defaulting to 15 minutes.")
    sleep_timer_minutes = 15

# Construct PLEX_URL
PLEX_URL = f"http://{server_ip}:{server_port}/status/sessions?X-Plex-Token={plex_token}"

class ActivityMonitor:
    def __init__(self):
        self.last_activity_time = time.time()

    def on_activity(self, *_):
        self.last_activity_time = time.time()

    def start(self):
        if is_graphical:
            with mouse.Listener(on_move=self.on_activity, on_click=self.on_activity) as mouse_listener, \
                 keyboard.Listener(on_press=self.on_activity) as keyboard_listener:
                try:
                    mouse_listener.join()
                    keyboard_listener.join()
                except Exception as e:
                    print(f"[{getTime()}] Error in activity listener: {e}")

def checkPrimeTime():
    current_time = datetime.now().time()
    start_time = datetime.strptime(primeTimeStart, "%H:%M").time()
    end_time = datetime.strptime(primeTimeEnd, "%H:%M").time()

    return start_time <= current_time <= end_time

def getTime():
    current_datetime = datetime.now()
    timestamp = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

def check_active_sessions():
    try:
        response = requests.get(PLEX_URL)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
    except requests.exceptions.RequestException as e:
        print(f"[{getTime()}] Error checking active sessions: {e}")
        return False

    try:
        root = ET.fromstring(response.content)
        return len(root.findall('.//Video')) > 0
    except ET.ParseError as e:
        print(f"[{getTime()}] Error parsing XML response: {e}")
        return False

def printSessionData(active_sessions):
    for session in active_sessions:
        print(f"  - User: {session['user']}, Type: {session['type']}, "
            f"Title: {session['title']}, "
            f"{'Artist: ' + session['artist'] + ', ' if 'artist' in session else ''}"
            f"Machine: {session['player_title']}, "
        )

def putToSleep():
    system_platform = platform.system()

    if system_platform == 'Windows':
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"])
    elif system_platform == 'Linux':
        subprocess.run(["systemctl", "suspend"])
    elif system_platform == 'Darwin':  # MacOS
        subprocess.run(["pmset", "sleepnow"])
    else:
        print(f"Sleep functionality not supported on {system_platform}.")

def main():
    inactive_time = 0
    activity_monitor = ActivityMonitor()
    did_sleep = False  # Variable to track if the machine went to sleep

    # Start the activity monitor in a separate thread
    if is_graphical:
        activity_thread = threading.Thread(target=activity_monitor.start)
        activity_thread.daemon = True
        activity_thread.start()

    while True:
        active_sessions = check_active_sessions()

        if checkPrimeTime():
            print(f"[{getTime()}] It is currently prime time - do not sleep right now.")
        else:
            # Check if the machine went to sleep
            if inactive_time >= SLEEP_TIMEOUT and not active_sessions:
                print(f"[{getTime()}] 15 minutes of inactivity detected. Setting did_sleep to true.")
                did_sleep = True
                putToSleep()

            if active_sessions or time.time() - activity_monitor.last_activity_time < minute:
                print(f"[{getTime()}] Active session(s) detected:")
                printSessionData(active_sessions)
                inactive_time = 0  # Reset the timer
                print("Sleep timer reset")
            else:
                print(f"[{getTime()}] No active sessions and no activity. Inactive for {inactive_time} seconds.")

            # Check for the did_sleep flag
            if did_sleep:
                print(f"[{getTime()}] Machine woke up. Resetting timers.")
                did_sleep = False
                inactive_time = 0

        #using sleep.time rather than threading.Event.wait() to ensure hard 60 second check
        time.sleep(minute)
        inactive_time += minute

if __name__ == "__main__":
    main()
