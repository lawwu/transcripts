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

To download all IDs of a channel into a `txt` file:
```bash
yt-dlp --flat-playlist --print id https://www.youtube.com/@lexfridman >> data/lex_fridman_ids.txt

# Radical Personal Finance - Google Podcasts
yt-dlp -v --flat-playlist --print url https://podcasts.google.com/feed/aHR0cDovL3JhZGljYWxwZXJzb25hbGZpbmFuY2UubGlic3luLmNvbS9yc3M >> data/rpf_ids.txt
```

To transcribe all of the video ids in a text file:
```bash
./bash_transcribe.sh data/rpf_ids.txt
```

The code uses a config file `configs/channels.json`:
```python
[
    {
        "name": "ai_explained",
        "url": "https://www.youtube.com/@aiexplained-official",
        "in_file": "aiexplained_video_ids.txt",
        "file": "aiexplained_video_ids_done.txt"
    },
    {
        "name": "all_in",
        "url": "https://www.youtube.com/@allin",
        "in_file": "allin_video_ids.txt",
        "file": "allin_video_ids_done.txt"
    },
    {
        "name": "lex_fridman",
        "url": "https://www.youtube.com/@lexfridman",
        "in_file": "video_ids.txt",
        "file": "video_ids_done.txt"
    },
    {
        "name": "radical_personal_finance",
        "url": "https://podcasts.google.com/feed/aHR0cDovL3JhZGljYWxwZXJzb25hbGZpbmFuY2UubGlic3luLmNvbS9yc3M",
        "in_file": "rpf_ids.txt",
        "file": "rpf_ids_done.txt"
    }
]
```

To transcribe new videos:
```bash
make transcribe_new
```

To generate the HTML pages:
```bash
make html
```

To setup a crontab:
```bash
crontab -e
0 */2 * * 1-6 /Users/lwu-macstudio/github/transcripts/src/transcripts/transcribe_new_videos.py
```

# TODO

Download history of videos
- [x] https://www.youtube.com/@allin
- [x] https://www.youtube.com/@lexfridman
- [x] https://www.youtube.com/@aiexplained-official
- [x] https://radicalpersonalfinance.libsyn.com/

Others
- [x] Organize the transcripts and html pages by channel
- [x] don't use JSON cache, use a slimmer CSV with id, title, upload_date, url, and other necessary fields
- [x] clean up the rpf transcripts, use ids
- [x] lex fridman: reverse order of transcripts, transcribe rest of them in `video_ids.txt`
- [x] modify `bash_transcribe_new_videos.sh` to get new videos for each channel, add url to the config
- [ ] create all transcript page ordered by date
- [ ] create other transcript page
- [ ] check transcript is good, sometimes whisper generates transcripts that have invalid utf-8

```python
Traceback (most recent call last):
  File "/Users/lwu-macstudio/github/transcripts/src/transcripts/generate_html.py", line 440, in <module>
    generate_html(id)
  File "/Users/lwu-macstudio/github/transcripts/src/transcripts/generate_html.py", line 300, in generate_html
    lines = f.readlines()
            ^^^^^^^^^^^^^
  File "<frozen codecs>", line 322, in decode
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xeb in position 1264: invalid continuation byte
```

- [ ] Use python bindings instead of calling whisper.cpp directly, can use https://github.com/aarnphm/whispercpp