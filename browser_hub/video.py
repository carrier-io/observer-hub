import os
import tempfile

from requests import get


def start_recording(host):
    get(f'http://{host}/record/start')


def stop_recording(host):
    print("Stop recording...")
    video_results = get(f'http://{host}/record/stop').content
    video_folder = tempfile.mkdtemp()
    video_path = os.path.join(video_folder, "video.mp4")
    with open(video_path, 'w+b') as f:
        f.write(video_results)
    print(f"Video file {video_path}")
    return video_folder, video_path
