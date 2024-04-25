#!/bin/bash

echo "Script started at $(date)"

# Set the absolute path to the Git repository directory
SCRIPT_DIR="/Users/lawrencewu/Github/transcripts"
SSH_KEY_PATH="/Users/lawrencewu/.ssh/id_rsa"

# Change to the Git repository directory
cd "$SCRIPT_DIR"

# Set the Git remote URL to use SSH
export PATH=$PATH:/opt/homebrew/bin
git remote set-url origin git@github.com:lawwu/transcripts.git

# Activate the virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Start the SSH agent and add the SSH key
eval "$(ssh-agent -s)"
ssh-add "$SSH_KEY_PATH"

python "$SCRIPT_DIR/src/transcripts/transcribe_new_videos.py"

# Commit files
git add "$SCRIPT_DIR/data/*.txt"
git add "$SCRIPT_DIR/docs/*.html"
git add "$SCRIPT_DIR/data/video_details_cache.json"
git commit -m "AUTO: adding transcripts from $(date +'%Y-%m-%d')"
git push 2>&1 | tee "$SCRIPT_DIR/git_push_output.log"

# Kill the SSH agent
eval "$(ssh-agent -k)"

echo "Script finished at $(date)"