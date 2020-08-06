import os

SCHEDULER_INTERVAL = int(os.environ.get("SCHEDULER_INTERVAL", 30))
TIMEOUT = int(os.environ.get("TIMEOUT", 60))
SELENIUM_PORT = int(os.environ.get("SELENIUM_PORT", 4444))
VIDEO_PORT = int(os.environ.get("SELENIUM_PORT", 9999))
SCREEN_RESOLUTION = os.environ.get("RESOLUTION", "1920x1080")

CONTAINERS = {
    "chrome": "getcarrier/observer-chrome:latest",
    "firefox": "getcarrier/observer-firefox:latest"
}