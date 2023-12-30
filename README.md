# Plex Sleep Controller

Python script to monitor Plex activity and put the server to sleep when idle.

## Description

Save money and save the planet! This Python script checks Plex server activity via the Plex server API and tracks mouse/keyboard activity. When the server is idle, a sleep timer is initiated based on the config settings. At the end of the timer, the machine is put to sleep. This is designed for Plex server owners who do not want their server running 24/7 for environmental or financial reasons.

This script can probably be modified for use with other server software, such as Jellyfin, which I am happy for you to do but please reference this. I may even add this in the future.

With the use of Wake On Lan, the user can remotely wake up the server to access the Plex server. This will depend on your hardware and a fair bit of setup which I will not cover here. However, I recommend [WOLSkill](https://www.wolskill.com/) and [WakeOnLan](https://www.nirsoft.net/utils/wake_on_lan.html). I will also not be giving usage instructions for these.

The instructions below offer basic usage for:

## Features

- Monitors active Plex sessions.
- Resets the system sleep timer if there is active Plex user activity.
- Prevents the system from going to sleep during active sessions.
- Customizable sleep timer.

## Usage

1. If not already installed, install Python.

2. Press the Windows key + type CMD to open command prompt

2. Install the required Python packages on your Plex server by typing the following in CMD:

    ```
    pip install requests pynput
    ```

3. Press the windows key and type 'Edit Power Plan' and set 'Put the computer to sleep' to never – we don't want Windows to force a sleep during playback.

4. In Windows, navigate to the location of 'go-to-sleep.py' and create a shortcut; feel free to put it on the desktop.

5. Press the Windows key + R and type `shell:startup`.

6. Move the shortcut into the startup folder and then close this.

7. Edit the `config.ini` file to add your server address (not tested remotely) as well as the port.

8. You will need to also add your Plex token. You can find this by viewing the info of any media item. This should load some XML data. The token is in the URL – there are plenty of detailed guides available for this.

9. The `sleepTimer` option allows you to define how many minutes the script will wait before putting the server to sleep. The default is 15 minutes.

10. Once the script is updated, you can either run the script manually or restart, and the script should run automatically.
