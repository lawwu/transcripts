import argparse
import json
import logging
import re
import pandas as pd
from yt_dlp import YoutubeDL
from datetime import datetime

from transcripts.utils import (
    transcripts_dir,
    data_dir,
    html_dir,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize or load the cache
cache_file = data_dir / "video_details_cache.json"
try:
    with open(cache_file, "r") as f:
        video_details_cache = json.load(f)
    logging.info("Cache loaded")
except FileNotFoundError:
    video_details_cache = {}
    logging.info("Cache not found, initializing empty cache")


def save_cache():
    with open(cache_file, "w") as f:
        json.dump(video_details_cache, f)


def read_ids_from_file(filename):
    logging.info(f"Reading video IDs from {filename}")
    with open(filename, "r") as f:
        return [line.strip() for line in f.readlines()]


def read_and_clean_whisper_file(file_path):
    cleaned_text = []
    with open(file_path, "r") as file:
        lines = file.readlines()
        for line in lines:
            # Remove timestamps
            cleaned_line = re.sub(
                r"\[\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\]\s*",
                "",
                line,
            )
            # Remove text enclosed in square brackets
            cleaned_line = re.sub(r"\[[^\]]*\]", "", cleaned_line)
            cleaned_text.append(cleaned_line.strip())
    return " ".join(cleaned_text).strip()


# Additional function to generate standalone transcript pages.
def generate_transcript_page(video_id):
    logging.info(f"Generating Transcript page for video ID {video_id}")

    details = fetch_video_details(video_id)
    video_url = details["webpage_url"]
    thumbnail_url = details["thumbnail"]
    title = details["title"]
    chapters = details.get("chapters", [])
    transcript_link = f"transcript_{video_id}.html"
    whisper_transcript_file = f"{video_id}.html"

    output_file = html_dir / f"transcript_{video_id}.html"
    input_file = transcripts_dir / f"{video_id}.txt"

    clean_transcript = read_and_clean_whisper_file(input_file)

    with open(output_file, "w") as f:
        f.write("<html><head><title>{}</title></head><body>".format(title))
        f.write(
            '<a href="index.html">back to index</a><h2>{}</h2>'.format(title)
        )
        f.write(
            f'<a href="{video_url}"><img src="{thumbnail_url}" style="width:50%;"></a><div><br></div>'
        )

        if chapters:
            f.write("<h3>Chapters</h3>")
            for chapter in chapters:
                start_time = int(chapter["start_time"])
                f.write(
                    f'<a href="{video_url}&t={start_time}">{start_time // 60}:{start_time % 60}</a> {chapter["title"]}<br>'
                )

        f.write(
            '<div style="text-align: left;">'
        )  # Start a div with left-aligned text
        f.write(
            f'<a href="./{whisper_transcript_file}">Whisper Transcript</a> | <a href="./{transcript_link}">Transcript Only Page</a>'
        )
        f.write("</div>")  # Close the div
        f.write("<br>")

        f.write("<h3>Transcript</h3>")
        f.write(
            '<div style="max-width: 600px;">'
        )  # Limit the width for readability
        f.write("<p>{}</p>".format(clean_transcript))
        f.write("</div>")  # Close the max-width div
        f.write("</body></html>")


def timestamp_to_seconds(timestamp):
    hours, minutes, seconds = map(int, timestamp.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def fetch_video_details(video_id):
    logging.info(f"Fetching details for video ID {video_id}")
    if video_id in video_details_cache:
        logging.info("Using cached details")
        return video_details_cache[video_id]

    ydl_opts = {"quiet": True}
    # Check for YouTube-like pattern (11 alphanumeric characters)
    youtube_match = re.search(r"([a-zA-Z0-9_-]{11})", video_id)
    if youtube_match:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
            # slim the info_dict
            info_dict = {
                "id": info_dict["id"],
                "title": info_dict["title"],
                "upload_date": info_dict["upload_date"],
                "duration": info_dict["duration"],
                "webpage_url": info_dict["webpage_url"],
                "thumbnail": info_dict["thumbnail"],
                "chapters": info_dict.get("chapters", []),
            }

            video_details_cache[video_id] = info_dict
            save_cache()
            return info_dict

    # Check for Vimeo URL pattern
    vimeo_match = re.search(r"(\d+)", video_id)
    if vimeo_match:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(
                f"https://www.vimeo.com/{video_id}", download=False
            )
            video_details_cache[video_id] = info_dict
            save_cache()
            return info_dict


def generate_index_page(video_ids, channel_name):
    logging.info("Generating index page")
    index_html = html_dir / f"index_{channel_name}.html"
    with open(index_html, "w") as f:
        f.write(
            '<html><head><title>Transcripts</title></head><body><h1>Transcripts</h1><table style="width:100%; border-collapse: collapse;">'
        )
        f.write("These transcripts are automatically generated using Whisper.")
        f.write(
            "<tr><th>Date</th><th>Title</th><th>Duration</th><th>Whisper Transcript</th><th>Transcript Only</th></tr>"
        )  # Added a new table header for "Transcript Only"

        for index, video_id in enumerate(video_ids):
            details = fetch_video_details(video_id)
            duration_in_minutes = details["duration"] // 60

            if duration_in_minutes < 1:
                # don't generate transcript, these are likely test videos
                continue
            whisper_transcript_file = f"{video_id}.html"
            transcript_file = (
                f"transcript_{video_id}.html"  # File name for Transcript Only
            )
            formatted_date = datetime.strptime(
                details["upload_date"], "%Y%m%d"
            ).strftime(
                "%Y-%m-%d"
            )  # New date format

            f.write(
                '<tr style="{}">'.format(
                    "background-color: #f2f2f2;" if index % 2 == 0 else ""
                )
            )
            f.write(f"<td>{formatted_date}</td>")  # Using the new date format
            f.write(f'<td>{details["title"]}</td>')
            f.write(f"<td>{duration_in_minutes} min</td>")
            f.write(
                f'<td><a href="./{whisper_transcript_file}">Whisper Transcript</a></td>'
            )  # Link to the Whisper Transcript
            f.write(
                f'<td><a href="./{transcript_file}">Transcript Only</a></td>'
            )  # New column for Transcript Only
            f.write("</tr>")

        f.write("</table></body></html>")


def generate_html(video_id):
    logging.info(f"Generating HTML for video ID {video_id}")
    youtube_match = re.search(r"([a-zA-Z0-9_-]{11})", video_id)

    details = fetch_video_details(video_id)
    video_url = details["webpage_url"]
    if youtube_match:
        thumbnail_url = details["thumbnail"]
    # else is just vimeo
    else:
        thumbnail_url = details["thumbnails"][0]["url"]
    title = details["title"]
    if youtube_match:
        chapters = details.get("chapters", [])
    else:
        chapters = None
    input_file = transcripts_dir / f"{video_id}.txt"
    output_file = html_dir / f"{video_id}.html"
    transcript_link = f"transcript_{video_id}.html"
    whisper_transcript_file = f"{video_id}.html"

    with open(input_file, "r") as f:
        lines = f.readlines()

    with open(output_file, "w") as f:
        f.write("<html><head><title>{}</title></head><body>".format(title))
        f.write(
            '<a href="index.html">back to index</a><h2>{}</h2>'.format(title)
        )
        f.write(
            f'<a href="{video_url}"><img src="{thumbnail_url}" style="width:50%;"></a><div><br></div>'
        )

        if chapters:
            f.write("<h3>Chapters</h3>")
            for chapter in chapters:
                start_time = int(chapter["start_time"])
                f.write(
                    f'<a href="{video_url}&t={start_time}">{start_time // 60}:{start_time % 60}</a> {chapter["title"]}<br>'
                )
            f.write("<br>")

        f.write(
            '<div style="text-align: left;">'
        )  # Start a div with left-aligned text
        f.write(
            f'<a href="./{whisper_transcript_file}">Whisper Transcript</a> | <a href="./{transcript_link}">Transcript Only Page</a>'
        )
        f.write("</div>")  # Close the div
        f.write("<br>")

        f.write(
            '<div style="max-width: 800px;">'
        )  # Limit the width for readability
        for line in lines:
            if "-->" in line:
                timestamp, content = re.split(r"]\s+", line, maxsplit=1)
                timestamp = timestamp[1:]
                start_timestamp, end_timestamp = timestamp.split(" --> ")
                total_seconds = timestamp_to_seconds(start_timestamp[:-4])
                f.write('<div class="c">')
                if youtube_match:
                    f.write(
                        '<span class="s"><a href="{}&t={}">{}</a></span> | '.format(
                            video_url, total_seconds, start_timestamp
                        )
                    )
                else:
                    f.write(
                        # vimeo url looks like: https://vimeo.com/24690039#t=90s
                        '<span class="s"><a href="{}#t={}s">{}</a></span> | '.format(
                            video_url, total_seconds, start_timestamp
                        )
                    )
                f.write(
                    '<span class="t">{}</span></div>'.format(content.strip())
                )
        f.write("</div>")  # Close the max-width div
        f.write("</body></html>")


def generate_master_index(config, html_dir=html_dir):
    index_html = html_dir / "index.html"
    with open(index_html, "w") as f:
        f.write("<html><head><title>Channel Index</title></head><body>")
        f.write("<h1>YouTube Channel Transcripts</h1>")
        f.write("These transcripts are automatically generated using Whisper.")
        f.write("<ul>")

        # TODO: this won't work for Google Podcasts (RPF)
        for channel in config:
            channel_index_file = f'index_{channel["name"]}.html'
            channel_link = channel_index_file
            f.write(
                f'<li><a href="{channel_link}">{channel["name"].replace("_", " ").title()}</a></li>'
            )

        f.write("</ul></body></html>")

    logging.info(f"Master index page generated at {index_html}")


def convert_cache_to_dataframe(cache):
    # Initialize list to store flattened dictionaries
    flattened_data = []

    # Flatten dictionary structure
    for _, attributes in cache.items():
        # print(video)
        id_ = attributes["id"]
        title = attributes["title"]
        upload_date = attributes["upload_date"]
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate HTML from YouTube transcript"
    )

    config = [
        {
            "name": "ai_explained",
            "url": None,
            "file": "aiexplained_video_ids_done.txt",
        },
        {"name": "all_in", "url": None, "file": "allin_video_ids_done.txt"},
        {"name": "lex_fridman", "url": None, "file": "video_ids_done.txt"},
        # {
        #     "name": "radical_personal_finance",
        #     "url": None,
        #     "file": "rpf_ids_done.txt",
        # },
        # {
        #     "name": "grace to you",
        #     "url": None,
        #     "file": "gracetoyou_ids_done.txt"
        # }
    ]

    for channel in config:
        video_ids = read_ids_from_file(data_dir / channel["file"])

        logging.info(f"Found {len(video_ids)} video IDs")

        # generate html for youtube videos
        for id in video_ids:
            # Generate individual transcript pages
            generate_html(id)
            # Generate individual transcript-only pages
            generate_transcript_page(id)

        exclude_list = []

        all_ids = video_ids
        # exclude videos in exclude list
        filtered_ids = [id for id in all_ids if id not in exclude_list]

        logging.info("Generate index page")
        generate_index_page(filtered_ids, channel["name"])
        logging.info(f"Total videos: {len(filtered_ids)}")

    generate_master_index(config)

    logging.info("All tasks completed")
