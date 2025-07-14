import argparse
import json
import logging
import re
import os
import concurrent.futures
from yt_dlp import YoutubeDL
from datetime import datetime
from pathlib import Path

from transcripts.utils import (
    transcripts_dir,
    data_dir,
    html_dir,
    configs_dir,
    extract_yt_id,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# used for everything except index.html
css_styles = """
<style>
    body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        background-color: #f4f4f4;
        color: #333;
    }
    .container {
        width: 95%;  /* Increased width to use more space */
        margin: auto;
        overflow: auto;  /* Added to handle overflow by adding a scrollbar if necessary */
    }
    h2, h3 {
        color: #333;
        text-align: center;
    }
    a {
        color: #0000FF;  /* Traditional blue color for links */
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    img {
        display: block;
        margin: auto;
        max-width: 100%;
    }
    .c {
        margin: 10px 0;
    }
    .s, .t {
        display: inline-block;
        margin-right: 5px;
    }
    .max-width {
        max-width: 800px;
        margin: auto;
        padding-left: 20px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;  /* Ensure text alignment is consistent */
    }
    tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    tr:nth-child(odd) {
        background-color: #e6e6e6;
    }
</style>
"""

css_styles_index = """
<style>
    body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        background-color: #f4f4f4;
        color: #333;
    }
    .container {
        width: 80%;
        margin: auto;
        overflow: hidden;
    }
    h1 {
        color: #333;
        text-align: center;
        padding: 20px 0;
    }
    ul {
        list-style: none;
        padding: 0;
    }
    ul li {
        background: #fff;
        margin: 5px 0;
        padding: 10px;
        border-radius: 5px;
    }
    ul li a {
        text-decoration: none;
        color: #0000FF;  /* Traditional blue color for links */
    }
    ul li a:hover {
        color: #0275d8;
        text-decoration: underline;
    }
    footer {
        text-align: center;
        padding: 20px 0;
        font-size: 0.8em;
    }
    footer a {
        color: #0275d8;
        text-decoration: none;
    }
    footer a:hover {
        text-decoration: underline;
    }
</style>
"""

# Initialize or load the cache
cache_file = data_dir / "video_details_cache.json"
try:
    with open(cache_file, "r") as f:
        video_details_cache = json.load(f)
    logging.info("Cache loaded")
except FileNotFoundError:
    video_details_cache = {}
    logging.info("Cache not found, initializing empty cache")

# Add a new cache file for tracking file modification times
modification_cache_file = data_dir / "modification_cache.json"
modification_times_cache = {}

# Load modification times cache if it exists
try:
    with open(modification_cache_file, "r") as f:
        modification_times_cache = json.load(f)
    logging.info(f"Loaded modification times cache with {len(modification_times_cache)} entries")
except FileNotFoundError:
    modification_times_cache = {}
    logging.info("Modification times cache not found, initializing empty cache")

def save_cache():
    with open(cache_file, "w") as f:
        json.dump(video_details_cache, f)

def save_modification_cache():
    """Save the modification times cache to disk"""
    with open(modification_cache_file, "w") as f:
        json.dump(modification_times_cache, f)

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


def calculate_audio_duration(file_path):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()

        # Find the last line with a timestamp
        last_line_with_timestamp = None
        for line in reversed(lines):
            if "-->" in line:
                last_line_with_timestamp = line
                break

        if not last_line_with_timestamp:
            raise ValueError("No timestamp found in the file.")

        # Extract the last timestamp
        last_timestamp = last_line_with_timestamp.split("-->")[-1].strip()
        h, m, s = last_timestamp.split(":")
        seconds = int(h) * 3600 + int(m) * 60 + round(float(s))

        return seconds

    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


def add_google_analytics():
    return """
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-69VLBMTTP0"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-69VLBMTTP0');
    </script>
    """


def timestamp_to_seconds(timestamp):
    hours, minutes, seconds = map(int, timestamp.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def get_minimum_info_dict(info_dict):
    return {
        "id": info_dict.get("id", None),
        "title": info_dict.get("title", None),
        "upload_date": info_dict.get("upload_date", None),
        "duration": info_dict.get("duration", None),
        "webpage_url": info_dict.get("webpage_url", None),
        "thumbnail": info_dict.get("thumbnail", None),
        "chapters": info_dict.get("chapters", []),
    }


def fetch_video_details(
    video_id, video_details_cache=video_details_cache, 
    ydl_opts={"quiet": True,
                "cookiesfrombrowser": ("firefox",),  # Replace "chrome" with your browser name
              # 'cookiefile': '/Users/lawrencewu/github/transcripts/src/transcripts/yt_cookie.txt',
              }
):
    if video_id is None or video_id == "":
        logging.info("Video ID is empty")
        return None
    logging.info(f"Fetching details for video ID {video_id}")
    if video_id in video_details_cache:
        logging.info("Using cached details")
        return video_details_cache[video_id]

    # check if video_id starts with "http"
    if video_id.startswith("http"):
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_id, download=False)
            info_dict = get_minimum_info_dict(info_dict)
            video_details_cache[video_id] = info_dict
            save_cache()
            return info_dict

    # Check for YouTube-like pattern (11 alphanumeric characters)
    youtube_match = re.search(r"([a-zA-Z0-9_-]{11})", video_id)
    if youtube_match:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
            info_dict = get_minimum_info_dict(info_dict)
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
            info_dict = get_minimum_info_dict(info_dict)
            video_details_cache[video_id] = info_dict
            save_cache()
            return info_dict


def generate_master_index(
    config, html_dir=html_dir, css_styles=css_styles_index
):
    """Main Index Page - index.html"""
    index_html = html_dir / "index.html"
    with open(index_html, "w") as f:
        # Writing the HTML content
        f.write("<!DOCTYPE html><html><head><title>Channel Index</title>")
        f.write(css_styles)  # Include CSS styles
        f.write('<script async src="https://cse.google.com/cse.js?cx=2770efcdf5435447c"></script>')  # Google CSE script
        f.write("</head><body>")
        f.write("<div class='container'>")
        f.write("<h1>Whisper Transcripts</h1>")
        f.write('<div class="gcse-search"></div>')  # Google CSE Search Box
        f.write("<p>These transcripts are automatically generated using Whisper.</p>")
        f.write("<ul>")

        # Add link to the all channels index page
        f.write('<li><a href="index_all_channels.html">All Channels</a></li>')

        # Add all transcripts to the index page
        for channel in config:
            channel_index_file = f'index_{channel["name"]}.html'
            channel_link = channel_index_file
            f.write(
                f'<li><a href="{channel_link}">{channel["name"].replace("_", " ").title()}</a></li>'
            )

        f.write("</ul>")
        f.write("</div>")
        f.write(
            "<footer>Source Code: <a href='https://github.com/lawwu/transcripts' target='_blank'>transcripts</a> on GitHub</footer>"
        )
        f.write("</body></html>")

    logging.info(f"Master index page generated at {index_html}")


def generate_all_video_index(
    ids, html_dir=html_dir, css_styles=css_styles
):
    """Generate a single index page for all channels"""
    logging.info("Generating index page for all channels")

    video_details_list = []

    # Collect all video details
    for video_id in ids:
        if video_id is None or video_id == "":
            continue

        details = video_details_cache.get(video_id, {})
        if details:
            formatted_date = datetime.strptime(details.get("upload_date", "19000101"), "%Y%m%d").strftime("%Y-%m-%d") if details.get("upload_date") else "1900-01-01"
            duration_minutes = details.get('duration', 0)
            if duration_minutes is not None:
                duration_minutes = duration_minutes // 60
            else:
                duration_minutes = 0  # Default to 0 if duration is None
            video_details_list.append({
                "date": formatted_date,
                "title": details.get("title", "Unknown Title"),
                "channel": details.get("channel_name", ""), # TODO: need to add channel_name to the details
                "duration": duration_minutes,
                "whisper_transcript_file": f"{video_id}.html",
                "transcript_file": f"transcript_{video_id}.html",
                "formatted_date": formatted_date
            })

    # Sort the list by date in descending order
    video_details_list.sort(key=lambda x: x["date"], reverse=True)

    index_html = html_dir / "index_all_channels.html"
    with open(index_html, "w") as f:
        f.write("<html><head><title>All Channels Transcripts</title>")
        f.write(css_styles)  # Use the updated CSS styles
        f.write(add_google_analytics())
        f.write('</head><body><div class="container"><h1>All Channels Transcripts</h1><table style="width:100%; border-collapse: collapse;">')
        f.write("<tr><th>Date</th><th>Title</th><th>Channel</th><th>Duration</th><th>Whisper Transcript</th><th>Transcript Only</th></tr>")

        for details in video_details_list:
            f.write('<tr style="{}">'.format("background-color: #f2f2f2;" if video_details_list.index(details) % 2 == 0 else ""))
            f.write(f"<td>{details['formatted_date']}</td>")
            f.write(f'<td>{details["title"]}</td>')
            f.write(f"<td>{details['channel']}</td>")
            f.write(f"<td>{details['duration']} min</td>")
            f.write(f'<td><a href="./{details["whisper_transcript_file"]}">Whisper Transcript</a></td>')
            f.write(f'<td><a href="./{details["transcript_file"]}">Transcript Only</a></td>')
            f.write("</tr>")

        f.write("</table></div>")
        f.write("<footer>Source Code: <a href='https://github.com/lawwu/transcripts' target='_blank'>transcripts</a> on GitHub</footer>")
        f.write("</body></html>")


def generate_index_page(video_ids, channel_name):
    """Channel Index Page"""
    logging.info("Generating channel index page")
    index_html = html_dir / f"index_{channel_name}.html"
    with open(index_html, "w") as f:
        channel_title = channel_name.replace("_", " ").title()
        f.write(f"<html><head><title>{channel_title} Transcripts</title>")
        f.write(css_styles)
        f.write(add_google_analytics())
        f.write(
            f'</head><body><h1>{channel_title} Transcripts</h1><table style="width:100%; border-collapse: collapse;">'
        )
        f.write('<a href="index.html">back to index</a>')
        f.write(
            "<tr><th>Date</th><th>Title</th><th>Duration</th><th>Whisper Transcript</th><th>Transcript Only</th></tr>"
        )  # Added a new table header for "Transcript Only"

        for index, video_id in enumerate(video_ids):
            if video_id is None or video_id == "":
                continue

            if video_id.startswith(
                "https://www.youtube.com/"
            ) or video_id.startswith("http://youtube.com/"):
                video_id = extract_yt_id(video_id)
            details = fetch_video_details(video_id)

            if details is None:
                logging.warning(f"Could not fetch details for video ID {video_id}, skipping.")
                continue

            video_id = details["id"]
            whisper_transcript_file = f"{video_id}.html"

            if details["duration"]:
                duration_in_minutes = details["duration"] // 60

                if duration_in_minutes < 1:
                    # don't generate transcript, these are likely test videos
                    continue
            else:
                duration_in_minutes = 0
                # TODO use transcript file to get length
                # input_file = transcripts_dir / f"{video_id}.txt"
                # duration_in_minutes = calculate_audio_duration(input_file) // 60

            transcript_file = (
                f"transcript_{video_id}.html"  # File name for Transcript Only
            )
            if details["upload_date"]:
                formatted_date = datetime.strptime(
                    details["upload_date"], "%Y%m%d"
                ).strftime(
                    "%Y-%m-%d"
                )  # New date format
            else:
                # TODO parse date from video_id
                formatted_date = ""

            # logging.info(f"Generating row in index page for video ID {video_id}")
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
    video_id = details["id"]
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
        f.write("<html><head><title>{}</title>".format(title))
        f.write(css_styles)  # Include CSS styles
        f.write(add_google_analytics())  # Include Google Analytics
        f.write("</head><body>")
        f.write("<div class='container'>")
        # TODO should go to channel index, not index.html
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
                        '<span class="s"><a href="{}&t={}" target="_blank">{}</a></span> | '.format(
                            video_url, total_seconds, start_timestamp
                        )
                    )
                else:
                    f.write(
                        # vimeo url looks like: https://vimeo.com/24690039#t=90s
                        '<span class="s"><a href="{}#t={}s">{} target="_blank"</a></span> | '.format(
                            video_url, total_seconds, start_timestamp
                        )
                    )
                f.write(
                    '<span class="t">{}</span></div>'.format(content.strip())
                )
        f.write("</div>")  # Close the max-width div
        f.write("</body></html>")


def generate_transcript_page(video_id):
    logging.info(f"Generating Transcript page for video ID {video_id}")

    details = fetch_video_details(video_id)
    video_id = details["id"]
    video_url = details["webpage_url"]
    thumbnail_url = details["thumbnail"]
    title = details["title"]
    chapters = details.get("chapters", [])

    output_file = html_dir / f"transcript_{video_id}.html"
    input_file = transcripts_dir / f"{video_id}.txt"

    clean_transcript = read_and_clean_whisper_file(input_file)

    with open(output_file, "w") as f:
        f.write("<html><head><title>{}</title>".format(title))
        f.write(css_styles)  # Include the CSS styles
        f.write(add_google_analytics())  # Include Google Analytics
        f.write("</head><body>")
        f.write("<div class='container'>")
        f.write(
            '<a href="index.html">Back to Index</a><h2>{}</h2>'.format(title)
        )
        f.write(
            f'<a href="{video_url}" target="_blank"><img src="{thumbnail_url}" style="width:50%;"></a><div><br></div>'
        )

        if chapters:
            f.write("<h3>Chapters</h3>")
            for chapter in chapters:
                start_time = int(chapter["start_time"])
                f.write(
                    f'<a href="{video_url}&t={start_time} target="_blank"">{start_time // 60}:{start_time % 60}</a> {chapter["title"]}<br>'
                )

        f.write("<h3>Transcript</h3>")
        f.write("<div class='max-width'>")  # Use max-width class for transcript
        sentences = re.split(r"(?<=[.!?]) +", clean_transcript)
        paragraph = ""
        for sentence in sentences:
            paragraph += sentence + " "
            # Optionally, define a condition to group sentences into paragraphs more naturally
            if (
                len(paragraph.split()) > 50
            ):  # For example, group by number of words
                f.write(f"<p>{paragraph.strip()}</p>")
                paragraph = ""
        if paragraph:  # Add any remaining text as a paragraph
            f.write(f"<p>{paragraph.strip()}</p>")
        f.write("</div>")  # Close the transcript div
        f.write("</div>")  # Close the container div
        f.write("</body></html>")

    logging.info(f"Transcript page generated at {output_file}")


def should_regenerate_html(video_id):
    """
    Determine if HTML files for a video should be regenerated based on:
    1. If the transcript file has been modified since last HTML generation
    2. If the HTML files don't exist
    
    Returns True if regeneration is needed, False otherwise
    """
    transcript_file = transcripts_dir / f"{video_id}.txt"
    html_file = html_dir / f"{video_id}.html"
    transcript_only_file = html_dir / f"transcript_{video_id}.html"
    
    # If transcript file doesn't exist, skip
    if not transcript_file.exists():
        logging.info(f"Transcript file for {video_id} doesn't exist, skipping")
        return False
    
    # Get the modification time of the transcript file
    mod_time = os.path.getmtime(transcript_file)
    
    # If HTML files don't exist, regenerate
    if not html_file.exists() or not transcript_only_file.exists():
        logging.info(f"HTML files for {video_id} don't exist, will generate")
        modification_times_cache[video_id] = mod_time
        return True
    
    # If transcript file has been modified since last generation, regenerate
    if video_id not in modification_times_cache or mod_time > modification_times_cache[video_id]:
        logging.info(f"Transcript file for {video_id} has been modified, will regenerate")
        modification_times_cache[video_id] = mod_time
        return True
    
    logging.info(f"HTML files for {video_id} are up to date, skipping")
    return False


def should_regenerate_index(channel_file, filtered_ids):
    """
    Determine if an index page should be regenerated based on:
    1. If any of the transcript files have been modified
    2. If the index file doesn't exist
    
    Returns True if regeneration is needed, False otherwise
    """
    channel_name = channel_file["name"]
    index_file = html_dir / f"{channel_name.lower()}_index.html"
    
    # If index file doesn't exist, regenerate
    if not index_file.exists():
        logging.info(f"Index file for {channel_name} doesn't exist, will generate")
        return True
    
    # Get the modification time of the index file
    index_mod_time = os.path.getmtime(index_file)
    
    # Check if any transcript files have been modified since the index was last generated
    for video_id in filtered_ids:
        if video_id in modification_times_cache:
            if modification_times_cache[video_id] > index_mod_time:
                logging.info(f"Transcript for {video_id} has been modified, will regenerate index for {channel_name}")
                return True
    
    logging.info(f"Index file for {channel_name} is up to date, skipping")
    return False


def should_regenerate_master_index(config_channels):
    """
    Determine if the master index page should be regenerated based on:
    1. If any channel index has been modified
    2. If the master index file doesn't exist
    
    Returns True if regeneration is needed, False otherwise
    """
    master_index_file = html_dir / "index.html"
    
    # If master index file doesn't exist, regenerate
    if not master_index_file.exists():
        logging.info("Master index file doesn't exist, will generate")
        return True
    
    # Get the modification time of the master index file
    master_mod_time = os.path.getmtime(master_index_file)
    
    # Check if any channel index files have been modified since the master index was last generated
    for channel in config_channels:
        channel_name = channel["name"]
        channel_index_file = html_dir / f"{channel_name.lower()}_index.html"
        
        if channel_index_file.exists():
            channel_mod_time = os.path.getmtime(channel_index_file)
            if channel_mod_time > master_mod_time:
                logging.info(f"Channel index for {channel_name} has been modified, will regenerate master index")
                return True
    
    logging.info("Master index file is up to date, skipping")
    return False


def should_regenerate_all_videos_index(list_all_videos):
    """
    Determine if the all videos index page should be regenerated based on:
    1. If any transcript has been modified
    2. If the all videos index file doesn't exist
    
    Returns True if regeneration is needed, False otherwise
    """
    all_videos_index_file = html_dir / "all_videos.html"
    
    # If all videos index file doesn't exist, regenerate
    if not all_videos_index_file.exists():
        logging.info("All videos index file doesn't exist, will generate")
        return True
    
    # Get the modification time of the all videos index file
    all_videos_mod_time = os.path.getmtime(all_videos_index_file)
    
    # Check if any transcript files have been modified since the all videos index was last generated
    for video_id in list_all_videos:
        if video_id in modification_times_cache:
            if modification_times_cache[video_id] > all_videos_mod_time:
                logging.info(f"Transcript for {video_id} has been modified, will regenerate all videos index")
                return True
    
    logging.info("All videos index file is up to date, skipping")
    return False


def force_rebuild_from_file(rebuild_file):
    """
    Force rebuild HTML files for video IDs listed in a file
    
    Args:
        rebuild_file: Path to a file containing video IDs to rebuild
    """
    if not rebuild_file.exists():
        logging.error(f"Rebuild file {rebuild_file} does not exist")
        return
        
    video_ids = read_ids_from_file(rebuild_file)
    logging.info(f"Found {len(video_ids)} video IDs to rebuild")
    
    for video_id in video_ids:
        if video_id is None or video_id == "" or video_id[0] == "-":
            continue
            
        logging.info(f"Force rebuilding HTML for video ID {video_id}")
        generate_html(video_id)
        generate_transcript_page(video_id)
        
        # Update the modification cache
        transcript_file = transcripts_dir / f"{video_id}.txt"
        if transcript_file.exists():
            mod_time = os.path.getmtime(transcript_file)
            modification_times_cache[video_id] = mod_time
    
    # Save the modification times cache
    save_modification_cache()


def process_video_id(id, force_all=False):
    """Process a single video ID - for parallel processing"""
    if id is None or id == "" or id[0] == "-":
        return
        
    # these videos are private
    private_videos = [
        "LvGJeivoJ_U",
        "_YgOjzrZook",
        "4vI4iKLSP5c",
        "9dz2t3CbkzI",
        "hstHUxkkBSQ",
        "BM33MCMfBd4",
        "Qv0YGAAJkmI",
        "LE10gdGnFS4",
        "uWediDOjcSA",
        "RSw12R-UARk",
        "gSEJOE1pCEA",
        "rViJJ_XQQlM",
        "whcUYpv3cz0",
        "Knk90Kw0Ypc",
        "2NG8L57eTBg",
        "CbugxdPscyg",
        "-rBtM6F9Hgs",
        "yeFc3wn5S3g",
        "Hj8_6SRNd7M",
        "I0rH86ForOc",
        "3RQkbByS3VU",
        "0vXdMhwAfTk",
        "JaMVzW9yiBc",
        "qZOF4TQK4Ug",
        "cjla_Slid98",
        "lC0gdGvu5ug",
        "p_ZKCgJibro",
        "2XgJ1MQpAHU",
        "rosko1DktW0",
        "HW554qecUU0",
        "rVUFef-zaCE",
        "B8h154w9qbo",  # atc
        "alOI2zxIPgc",
        "Zxahu5y79SA",
        "GkTOSDLfCaI",
        "MMBn3I-Rvi0",
        "SouId59N9jE",
        "VZUqWSzi2WA",
        "CGC4wqLUEbQ",
        "fJLCgEo27QM",
        "BPF9_0LGBlM",
        "FnZUdwYg8yY",
        "K7mswfTwjfk",
        "8aV44LTsw3k",
        "Gfg3wVVecYI",
        "https://traffic.libsyn.com/secure/financialsamurai/FS_212_-_Kathy_Fang-2.mp3?dest-id=1377836",
        "DnZPgopXQGM",
        "RcJ1YXHLv5o",
        "D4Xaqgd9-Ro", #all-in live in 2024-11-06
        "ULcwHlxfSkQ", # latent space missing, remove from data/latent_space_tv_ids_done.txt and retranscribe
    ]
    
    if id in private_videos:
        return
        
    # Generate individual transcript pages
    if force_all or should_regenerate_html(id):
        try:
            generate_html(id)
            # Generate individual transcript-only pages
            generate_transcript_page(id)
            
            # Update the modification cache
            transcript_file = transcripts_dir / f"{id}.txt"
            if transcript_file.exists():
                mod_time = os.path.getmtime(transcript_file)
                # Use a lock to safely update the shared cache
                modification_times_cache[id] = mod_time
                
            return id  # Return the ID to indicate it was processed
        except Exception as e:
            logging.error(f"Error processing video ID {id}: {e}")
            return None
    
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate HTML from YouTube transcript"
    )
    
    # Add command line arguments
    parser.add_argument(
        "--force-all", 
        action="store_true", 
        help="Force regeneration of all HTML files regardless of modification times"
    )
    parser.add_argument(
        "--force-indexes", 
        action="store_true", 
        help="Force regeneration of all index files regardless of modification times"
    )
    parser.add_argument(
        "--video-id", 
        type=str, 
        help="Generate HTML only for the specified video ID"
    )
    parser.add_argument(
        "--channel", 
        type=str, 
        help="Generate HTML only for the specified channel"
    )
    parser.add_argument(
        "--rebuild-file", 
        type=str, 
        help="Path to a file containing video IDs to force rebuild"
    )
    parser.add_argument(
        "--parallel", 
        action="store_true", 
        help="Use parallel processing to speed up HTML generation"
    )
    
    parser.add_argument(
        "--workers", 
        type=int, 
        default=4,
        help="Number of worker processes for parallel processing (default: 4)"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Preview what would be regenerated without actually doing it"
    )
    
    args = parser.parse_args()
    
    # open channels.json in configs_dir
    with open(configs_dir / "channels.json", "r") as f:
        config_channels = json.load(f)

    # If a specific video ID is provided, only generate HTML for that video
    if args.video_id:
        logging.info(f"Generating HTML for video ID {args.video_id}")
        if args.dry_run:
            logging.info(f"DRY RUN: Would generate HTML for video ID {args.video_id}")
        else:
            generate_html(args.video_id)
            generate_transcript_page(args.video_id)
            # Save the modification times cache
            save_modification_cache()
        logging.info("Task completed")
        exit(0)

    # If a rebuild file is provided, force rebuild those videos
    if args.rebuild_file:
        rebuild_file = Path(args.rebuild_file)
        if args.dry_run:
            video_ids = read_ids_from_file(rebuild_file)
            logging.info(f"DRY RUN: Would rebuild {len(video_ids)} videos from {args.rebuild_file}")
            for video_id in video_ids:
                if video_id is None or video_id == "" or video_id[0] == "-":
                    continue
                logging.info(f"DRY RUN: Would rebuild HTML for video ID {video_id}")
        else:
            force_rebuild_from_file(rebuild_file)
        logging.info("Rebuild completed")
        exit(0)

    list_all_videos = []
    processed_ids = []
    
    for channel in config_channels:
        # Skip channels that don't match the specified channel
        if args.channel and channel["name"].lower() != args.channel.lower():
            continue
            
        video_ids = read_ids_from_file(data_dir / channel["file"])
        logging.info(f"Found {len(video_ids)} video IDs")

        # Filter out invalid IDs and private videos
        valid_ids = [id for id in video_ids if id and id != "" and id[0] != "-"]
        
        # Process videos in parallel if requested
        if args.parallel and not args.dry_run:
            logging.info(f"Processing {len(valid_ids)} videos in parallel with {args.workers} workers")
            with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
                # Submit all tasks
                future_to_id = {executor.submit(process_video_id, id, args.force_all): id for id in valid_ids}
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_id):
                    id = future_to_id[future]
                    try:
                        result = future.result()
                        if result:
                            processed_ids.append(result)
                    except Exception as e:
                        logging.error(f"Error processing video ID {id}: {e}")
        else:
            # Process videos sequentially
            for id in valid_ids:
                if args.dry_run:
                    if should_regenerate_html(id):
                        logging.info(f"DRY RUN: Would regenerate HTML for video ID {id}")
                else:
                    result = process_video_id(id, args.force_all)
                    if result:
                        processed_ids.append(result)

        # Filter out private videos for the index
        all_ids = video_ids
        private_videos = [
            "LvGJeivoJ_U",
            "_YgOjzrZook",
            "4vI4iKLSP5c",
            "9dz2t3CbkzI",
            "hstHUxkkBSQ",
            "BM33MCMfBd4",
            "Qv0YGAAJkmI",
            "LE10gdGnFS4",
            "uWediDOjcSA",
            "RSw12R-UARk",
            "gSEJOE1pCEA",
            "rViJJ_XQQlM",
            "whcUYpv3cz0",
            "Knk90Kw0Ypc",
            "2NG8L57eTBg",
            "CbugxdPscyg",
            "-rBtM6F9Hgs",
            "yeFc3wn5S3g",
            "Hj8_6SRNd7M",
            "I0rH86ForOc",
            "3RQkbByS3VU",
            "0vXdMhwAfTk",
            "JaMVzW9yiBc",
            "qZOF4TQK4Ug",
            "cjla_Slid98",
            "lC0gdGvu5ug",
            "p_ZKCgJibro",
            "2XgJ1MQpAHU",
            "rosko1DktW0",
            "HW554qecUU0",
            "rVUFef-zaCE",
            "B8h154w9qbo",  # atc
            "alOI2zxIPgc",
            "Zxahu5y79SA",
            "GkTOSDLfCaI",
            "MMBn3I-Rvi0",
            "SouId59N9jE",
            "VZUqWSzi2WA",
            "CGC4wqLUEbQ",
            "fJLCgEo27QM",
            "BPF9_0LGBlM",
            "FnZUdwYg8yY",
            "K7mswfTwjfk",
            "8aV44LTsw3k",
            "Gfg3wVVecYI",
            "https://traffic.libsyn.com/secure/financialsamurai/FS_212_-_Kathy_Fang-2.mp3?dest-id=1377836",
            "DnZPgopXQGM",
            "RcJ1YXHLv5o",
            "D4Xaqgd9-Ro", #all-in live in 2024-11-06
            "ULcwHlxfSkQ", # latent space missing, remove from data/latent_space_tv_ids_done.txt and retranscribe
        ]
        exclude_list = private_videos
        filtered_ids = [id for id in all_ids if id not in exclude_list]
        
        # append to list_all_videos
        list_all_videos += filtered_ids

        logging.info("Generate index page")
        if args.dry_run:
            if args.force_all or args.force_indexes or should_regenerate_index(channel, filtered_ids):
                logging.info(f"DRY RUN: Would regenerate index page for {channel['name']}")
        elif args.force_all or args.force_indexes or should_regenerate_index(channel, filtered_ids):
            generate_index_page(filtered_ids, channel["name"])
        logging.info(f"Total videos: {len(filtered_ids)}")

    # Skip generating all videos and master indexes if a specific channel is specified
    if not args.channel:
        if args.dry_run:
            if args.force_all or args.force_indexes or should_regenerate_all_videos_index(list_all_videos):
                logging.info("DRY RUN: Would regenerate all videos index")
            
            if args.force_all or args.force_indexes or should_regenerate_master_index(config_channels):
                logging.info("DRY RUN: Would regenerate master index")
        else:
            if args.force_all or args.force_indexes or should_regenerate_all_videos_index(list_all_videos):
                generate_all_video_index(list_all_videos)
            
            if args.force_all or args.force_indexes or should_regenerate_master_index(config_channels):
                generate_master_index(config_channels)

    logging.info("All tasks completed")

    # Save the modification times cache if not a dry run
    if not args.dry_run:
        save_modification_cache()
