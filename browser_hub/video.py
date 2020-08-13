import os
import tempfile
from time import time

from requests import get

from browser_hub.constants import VIDEO_PATH
from browser_hub.util import logger


def start_video_recording(video_host):
    start_time = time()
    start_recording(video_host)
    current_time = time() - start_time
    return int(current_time)


def start_recording(host):
    get(f'http://{host}/record/start')


def stop_recording(host):
    logger.info("Stop recording...")
    os.makedirs(VIDEO_PATH, exist_ok=True)
    video_results = get(f'http://{host}/record/stop').content
    video_folder = tempfile.mkdtemp(dir=VIDEO_PATH)
    video_path = os.path.join(video_folder, "video.mp4")
    with open(video_path, 'w+b') as f:
        f.write(video_results)
    logger.info(f"Video file {video_path}")
    return video_folder, video_path
