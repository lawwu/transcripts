# Transcripts

Whisper transcripts for Youtube videos

# Setup

```bash
pyenv local 3.11
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# install in editable mode
pip install -e .

# initialize git-lfs
git lfs install

# build whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make clean
make -j

# download large-v3 model and put it in models
# https://huggingface.co/ggerganov/whisper.cpp/blob/main/ggml-large.bin

# setup pre-commit
pre-commit install
```

To download all IDs of a channel:
```bash
yt-dlp --flat-playlist --print id https://www.youtube.com/@aiexplained-official
```

# TODO

Download history of videos
- [x] https://www.youtube.com/@allin
- [ ] https://www.youtube.com/@lexfridman
- [x] https://www.youtube.com/@aiexplained-official
- [ ] https://www.youtube.com/@gracetoyou
- [ ] https://www.youtube.com/@ligonier/videos
- [ ] https://radicalpersonalfinance.libsyn.com/
- [ ] https://www.latent.space/podcast

Organize the transcripts and html pages by channel
  [ ] don't use JSON cache, use a slimmer CSV with id, title, upload_date, url, and other necessary fields
- [ ] Use python bindings instead of calling whisper.cpp directly, can use https://github.com/aarnphm/whispercpp