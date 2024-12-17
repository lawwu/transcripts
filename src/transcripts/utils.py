import re
import time
from pathlib import Path
from functools import wraps
import json
import pandas as pd
from datetime import datetime
import sqlite3

project_dir = Path(__file__).resolve().parents[2]
data_dir = project_dir / "data"
raw_dir = data_dir / "raw"
interim_dir = data_dir / "interim"
processed_dir = data_dir / "processed"
external_dir = data_dir / "external"
model_dir = project_dir / "models"
transcripts_dir = data_dir / "transcripts"
videos_dir = data_dir / "videos"
html_dir = project_dir / "docs"
whispercpp_dir = project_dir / "whisper.cpp"
configs_dir = project_dir / "configs"


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(
            f"{func.__name__} completed. Time elapsed: {elapsed_time:.2f} seconds."
        )
        return result

    return wrapper


def dump_json_to_file(json_object, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_object, f, ensure_ascii=False, indent=4)


def convert_cache_to_dataframe(cache):
    # Initialize list to store flattened dictionaries
    flattened_data = []

    # Flatten dictionary structure
    for _, attributes in cache.items():
        # print(video)
        id_ = attributes["id"]
        title = attributes["title"]
        upload_date = attributes["upload_date"]
        if upload_date is None:
            upload_date_formatted = None
        else:
            upload_date_formatted = datetime.strptime(
                upload_date, "%Y%m%d"
            ).strftime("%Y-%m-%d")
        flattened_dict = {
            "id": id_,
            "title": title,
            "upload_date": upload_date_formatted,
        }
        flattened_data.append(flattened_dict)

    df = pd.DataFrame(flattened_data)
    df = df.sort_values(["upload_date"], ascending=False)
    return df


def extract_yt_id(url):
    # Define the regex pattern to find the video ID
    pattern = r"v=([^&]+)"
    # Search for the pattern in the URL
    match = re.search(pattern, url)
    # If a match is found, return the video ID (first capturing group)
    if match:
        return match.group(1)
    else:
        # Return None or an appropriate message if no video ID is found
        return None


def connect_to_db():
    try:
        conn = sqlite3.connect(data_dir / "transcripts.db")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database: {e}")
        return None


def fetch_transcript_from_db(video_id):
    conn = connect_to_db()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT transcript FROM transcripts WHERE video_id=?", (video_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"Error fetching transcript from database: {e}")
        return None
    finally:
        conn.close()


def insert_transcript_to_db(video_id, transcript):
    conn = connect_to_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transcripts (video_id, transcript) VALUES (?, ?)",
            (video_id, transcript),
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error inserting transcript into database: {e}")
    finally:
        conn.close()


def insert_video_details_to_db(video_id, title, upload_date, duration, channel_name):
    conn = connect_to_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO video_details (video_id, title, upload_date, duration, channel_name) VALUES (?, ?, ?, ?, ?)",
            (video_id, title, upload_date, duration, channel_name),
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error inserting video details into database: {e}")
    finally:
        conn.close()
