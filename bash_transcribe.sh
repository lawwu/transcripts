#!/bin/bash

# Check if the path to the text file is provided as an argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <path_to_ids_file>"
  exit 1
fi

# Store the path to the YouTube IDs text file in a variable
ids_file="$1"

# Check if the file exists
if [ ! -f "$ids_file" ]; then
  echo "Error: File '$ids_file' does not exist."
  exit 1
fi

# Read YouTube IDs from the text file and store them in a variable
ids=$(cat "$ids_file")

# Loop through each YouTube ID
for id in $ids; do
  
  # Call your Python script
  python src/transcripts/transcribe_youtube.py "$id"
  
  # Optionally, sleep for a few seconds to avoid hitting rate limits
  sleep 2
done