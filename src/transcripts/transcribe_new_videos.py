import subprocess
import json
import logging
import os
from transcripts.utils import data_dir, configs_dir
from pathlib import Path

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)

# open channels.json in configs_dir
with open(configs_dir / "channels.json", "r") as f:
    channels = json.load(f)


def load_existing_ids(file):
    try:
        with open(data_dir / file, "r") as f:
            existing_ids = f.readlines()
        existing_ids = [x.strip() for x in existing_ids]
    except FileNotFoundError:
        existing_ids = []
    return existing_ids


def update_video_files(new_ids, existing_ids, done_file_path, in_file_path):
    """
    Updates video files with new and existing video IDs.

    Args:
    - new_ids (list): List of new video IDs to add.
    - existing_ids (list): List of existing video IDs.
    - done_file_path (Path or str): Path to the file for storing done video IDs.
    - in_file_path (Path or str): Path to the file for processing new video IDs.
    """
    # Convert string paths to Path objects if necessary
    done_file_path = (
        Path(done_file_path)
        if not isinstance(done_file_path, Path)
        else done_file_path
    )
    in_file_path = (
        Path(in_file_path)
        if not isinstance(in_file_path, Path)
        else in_file_path
    )

    if new_ids:
        # Update the file with done video IDs, adding new IDs at the top
        with open(done_file_path, "w") as f:
            print(f"writing videos to done file: {done_file_path}")
            for vid in reversed(new_ids):
                print("writing new vid")
                print(f"{vid}\n")
                f.write(f"{vid}\n")
            for existing in existing_ids:
                print("writing existing vid")
                print(f"{existing}\n")
                f.write(f"{existing}\n")

        # Write new video IDs to the file for processing
        with open(in_file_path, "w") as f:
            for vid in reversed(new_ids):
                f.write(f"{vid}\n")
    else:
        logging.info("No new videos found")
        # Ensure the file for processing new videos is blank if no new videos are found
        with open(in_file_path, "w") as f:
            f.write("")


# Download other videos (manual list)
# Step 2: Load existing video ids from the done file
other_done_ids = load_existing_ids("other_ids_done.txt")
other_ids = load_existing_ids("other_ids.txt")

# get new ids
new_other_ids = [vid for vid in other_ids if vid not in other_done_ids]
new_other_videos_count = len(new_other_ids)
logging.info(f"New other videos found: {new_other_videos_count}")

# download videos
if new_other_videos_count > 0:
    subprocess.run(["./bash_transcribe.sh", "./data/other_ids.txt"])

# Step 4: Update the *_done.txt by adding new ids at the top
if new_other_videos_count > 0:
    all_videos = new_other_ids + other_done_ids
    print(all_videos)
    with open(data_dir / "other_ids_done.txt", "w") as f:
        for existing in all_videos:
            f.write(f"{existing}\n")
else:
    logging.info("No new videos found")
    # make sure in_file.txt is blank
    with open(data_dir / "other_ids.txt", "w") as f:
        f.write("")


# update_video_files(new_other_ids, other_done_ids, "other_ids_done.txt", "other_ids.txt")


for channel in channels:
    channels_to_skip_download = [
        "ask_pastor_john",
        "ask_the_compound",
        "all_the_hacks",
    ]
    if channel["name"] in channels_to_skip_download:
        continue
    # Step 1: Get all video list from the channel
    # Use ID for YouTube, Google Podcast, use URL
    logging.info(f"Processing: {channel['name']}")
    if channel["name"] in [
        "all_the_hacks",
        "everyday_educator",
        "financial_samurai",
        "latent_space",
        "radical_personal_finance",
        "surpassing_value",
    ]:
        cmd = f"yt-dlp -v --flat-playlist --print url {channel['url']}"
    else:
        cmd = f"yt-dlp --flat-playlist --print id {channel['url']}"
    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, text=True)
    video_ids = result.stdout.strip().split("\n")
    total_videos = len(video_ids)
    logging.info(f"Total videos fetched: {total_videos}")

    # Step 2: Load existing video ids from the done file
    existing_ids = load_existing_ids(channel["file"])

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

# # Commit files
# subprocess.run(["git", "add", "./data/*.txt"])
# subprocess.run(["git", "add", "./docs/*.html"])
# subprocess.run(["git", "add", "./data/video_details_cache.json"])
# subprocess.run(
#     [
#         "git",
#         "commit",
#         "-m",
#         f"AUTO: adding latest transcripts from {datetime.now().strftime('%Y-%m-%d')}",
#     ]
# )
# subprocess.run(["git", "push"])
