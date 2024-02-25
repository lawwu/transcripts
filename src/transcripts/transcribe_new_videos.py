import subprocess
import json
import logging
import os
from transcripts.utils import data_dir, configs_dir
from datetime import datetime

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)

# open channels.json in configs_dir
with open(configs_dir / "channels.json", "r") as f:
    channels = json.load(f)

for channel in channels:
    channels_to_skip_download = ["ask_pastor_john", "ask_the_compound", "all_the_hacks"]
    if channel["name"] in channels_to_skip_download:
        continue
    # Step 1: Get all video list from the channel
    # Use ID for YouTube, Google Podcast, use URL
    logging.info(f"Processing: {channel['name']}")
    if channel["name"] in ["radical_personal_finance", "latent_space", 
                           "all_the_hacks", "financial_samurai"]:
        cmd = f"yt-dlp -v --flat-playlist --print url {channel['url']}"
    else:
        cmd = f"yt-dlp --flat-playlist --print id {channel['url']}"
    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, text=True)
    video_ids = result.stdout.strip().split("\n")
    total_videos = len(video_ids)
    logging.info(f"Total videos fetched: {total_videos}")

    # Step 2: Load existing video ids from the done file
    try:
        with open(data_dir / channel["file"], "r") as f:
            existing_ids = f.readlines()
        existing_ids = [x.strip() for x in existing_ids]
    except FileNotFoundError:
        existing_ids = []

    # Step 3: Find new video ids by comparing
    new_ids = [vid for vid in video_ids if vid not in existing_ids]
    new_videos_count = len(new_ids)
    logging.info(f"New videos found: {new_videos_count}")

    # Step 4: Update the *_done.txt by adding new ids at the top
    if new_ids:
        with open(data_dir / channel["file"], "w") as f:
            for vid in reversed(new_ids):
                f.write(f"{vid}\n")
            for existing in existing_ids:
                f.write(f"{existing}\n")

        # Step 5: Write new video ids to in_file.txt
        with open(data_dir / channel["in_file"], "w") as f:
            for vid in reversed(new_ids):
                f.write(f"{vid}\n")
    else:
        logging.info("No new videos found")
        # make sure in_file.txt is blank
        with open(data_dir / channel["in_file"], "w") as f:
            f.write("")

    # Check if in_file.txt is empty
    if os.path.getsize(f"./data/{channel['in_file']}") > 0:
        # Transcribe new videos
        subprocess.run(["./bash_transcribe.sh", f"./data/{channel['in_file']}"])

# Generate html and output to docs/
subprocess.run(["python", "src/transcripts/generate_html.py"])

# Commit files
subprocess.run(["git", "add", "./data/*.txt"])
subprocess.run(["git", "add", "./docs/*.html"])
subprocess.run(["git", "add", "./data/video_details_cache.json"])
subprocess.run(
    [
        "git",
        "commit",
        "-m",
        f"AUTO: adding latest transcripts from {datetime.now().strftime('%Y-%m-%d')}",
    ]
)
subprocess.run(["git", "push"])
