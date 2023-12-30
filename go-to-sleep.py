import subprocess
import requests
import xml.etree.ElementTree as ET
import time
import os
import threading
from pynput import mouse, keyboard
from datetime import datetime
import configparser

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Extract values from config
server_ip = config['Settings']['serverIp']
server_port = config['Settings']['serverPort']
plex_token = config['Settings']['plexToken']
sleep_timer_minutes = int(config['Settings']['sleepTimer'])
SLEEP_TIMEOUT = sleep_timer_minutes * 60  # Convert minutes to seconds

# Construct PLEX_URL
PLEX_URL = f"http://{server_ip}:{server_port}/status/sessions?X-Plex-Token={plex_token}"

class ActivityMonitor:
    def __init__(self):
        self.last_activity_time = time.time()

    def on_activity(self, *_):
        self.last_activity_time = time.time()

    def start(self):
        with mouse.Listener(on_move=self.on_activity, on_click=self.on_activity) as mouse_listener, \
             keyboard.Listener(on_press=self.on_activity) as keyboard_listener:
            try:
                mouse_listener.join()
                keyboard_listener.join()
            except Exception as e:
                print(f"[{getTime()}] Error in activity listener: {e}")


def getTime():
    current_datetime = datetime.now()
    timestamp = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp


def check_active_sessions():
    response = requests.get(PLEX_URL)
    tree = ET.fromstring(response.text)
    active_sessions = []

    for video_node in tree.findall(".//Video"):
        user_node = video_node.find(".//User")
        player_node = video_node.find(".//Player")

        session_info = {
            "user": user_node.get("title") if user_node is not None else "Unknown User",
            "title": video_node.get("title"),
            "type": "Video",
            "player_title": player_node.get("title") if player_node is not None else "Unknown Player",
        }
        active_sessions.append(session_info)

    for track_node in tree.findall(".//Track"):
        user_node = track_node.find(".//User")
        player_node = track_node.find(".//Player")

        session_info = {
            "user": user_node.get("title") if user_node is not None else "Unknown User",
            "title": track_node.get("title"),
            "type": "Track",
            "player_title": player_node.get("title") if player_node is not None else "Unknown Player",
            "artist": track_node.get("grandparentTitle") if track_node is not None else "Unknown Artist",
        }
        active_sessions.append(session_info)

    return active_sessions


def main():
    inactive_time = 0
    activity_monitor = ActivityMonitor()
    did_sleep = False  # Variable to track if the machine went to sleep

    # Start the activity monitor in a separate thread
    activity_thread = threading.Thread(target=activity_monitor.start)
    activity_thread.start()

    while True:
        active_sessions = check_active_sessions()

        # Check if the machine went to sleep
        if inactive_time >= SLEEP_TIMEOUT and not active_sessions:
            print(f"[{getTime()}] 15 minutes of inactivity detected. Setting did_sleep to true.")
            did_sleep = True
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"])
            inactive_time = 0  # Reset the timer after initiating sleep

        if active_sessions or time.time() - activity_monitor.last_activity_time < 60:
            print(f"[{getTime()}] Active session(s) detected:")
            for session in active_sessions:
                print(f"  - User: {session['user']}, Type: {session['type']}, "
                    f"Title: {session['title']}, "
                    f"{'Artist: ' + session['artist'] + ', ' if 'artist' in session else ''}"
                    f"Machine: {session['player_title']}, "
                )

            print("Resetting timer.")
            inactive_time = 0  # Reset the timer
        else:
            print(f"[{getTime()}] No active sessions and no activity. Inactive for {inactive_time} seconds.")

        # Check for the did_sleep flag
        if did_sleep:
            print(f"[{getTime()}] Machine woke up. Resetting timers.")
            did_sleep = False
            inactive_time = 0

        time.sleep(60)  # Sleep for 1 minute
        inactive_time += 60


if __name__ == "__main__":
    main()
