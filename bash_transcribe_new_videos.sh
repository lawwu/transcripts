#!/bin/bash

# get new video ideas
python src/transcripts/get_new_video_ids.py

# Check if video_ids.txt is empty
if [ -s "./data/video_ids.txt" ]; then
    # transcribe new videos
    ./bash_transcribe.sh ./data/video_ids.txt
    
    # generate html and output to docs/
    python src/transcripts/generate_html.py --file ./data/video_ids_done.txt
    
    # commit files
    # git add "./data/*.txt"
    # git add "./docs/*.html"
    # # git add data/video_details_cache.json
    # git commit -m "AUTO: adding latest messages from $(date +'%Y-%m-%d')"
    # git push
else
    echo "No new videos found. Exiting script."
fi