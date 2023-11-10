#!/bin/bash

# Read YouTube IDs from the text file and store them in a variable
youtube_ids=$(cat ./data/video_ids.txt)

# Loop through each YouTube ID
for id in $youtube_ids; do
  # Create the full YouTube URL
  youtube_url="https://www.youtube.com/watch?v=$id"
  
  # Call your Python script
  python src/transcripts/transcribe_youtube.py "$youtube_url"
  
  # Optionally, sleep for a few seconds to avoid hitting rate limits
  sleep 2
done
