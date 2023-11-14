#!/bin/bash

# Check if the path to the text file is provided as an argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <path_to_youtube_ids_file>"
  exit 1
fi

# Store the path to the YouTube IDs text file in a variable
youtube_ids_file="$1"

# Check if the file exists
if [ ! -f "$youtube_ids_file" ]; then
  echo "Error: File '$youtube_ids_file' does not exist."
  exit 1
fi

# Read YouTube IDs from the text file and store them in a variable
youtube_ids=$(cat "$youtube_ids_file")

# Loop through each YouTube ID
for id in $youtube_ids; do
  # Create the full YouTube URL
  youtube_url="https://www.youtube.com/watch?v=$id"
  
  # Call your Python script
  python src/transcripts/transcribe_youtube.py "$youtube_url"
  
  # Optionally, sleep for a few seconds to avoid hitting rate limits
  sleep 2
done