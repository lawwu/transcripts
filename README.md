# Transcripts

Whisper transcripts for Youtube videos.

- 2025-03-07 to present, switched to `ggml-large-v3-turbo`
- Prior to 2025-03-07, used to `ggml-large-v2` model

Available models are [here](https://github.com/ggerganov/whisper.cpp/blob/master/models/README.md).


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
yt-dlp --flat-playlist --print id https://www.youtube.com/@lexfridman >> data/video_ids_done.txt

# Radical Personal Finance - Google Podcasts
yt-dlp -v --flat-playlist --print url https://podcasts.google.com/feed/aHR0cDovL3JhZGljYWxwZXJzb25hbGZpbmFuY2UubGlic3luLmNvbS9yc3M >> data/rpf_ids.txt

yt-dlp -v --flat-playlist --print id https://www.youtube.com/watch?v=G3QoF4dqdE0&list=PLFF7F6AE365DA3564 >> data/apj_ids.txt

yt-dlp -v --flat-playlist --print id https://www.youtube.com/@AndrejKarpathy >> data/andrej_karpathy_ids_done.txt

yt-dlp -v --flat-playlist --print id https://www.youtube.com/@CalNewportMedia >> data/calnewport_ids_done.txt

yt-dlp -v --flat-playlist --print id https://www.youtube.com/watch?v=G3QoF4dqdE0&list=PLFF7F6AE365DA3564 >> data/apj_ids_done.txt
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

To remove large files:

Can you use: https://github.com/newren/git-filter-repo

```
# brew install git-filter-repo
git filter-repo --strip-blobs-bigger-than 100M
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
- [x] schedule a crontab every 2 hours
- [x] add Stanford XCS224U: Natural Language Understanding course: https://www.youtube.com/playlist?list=PLoROMvodv4rOwvldxftJTmoR3kRcWkJBp
- [x] add Stanford CS224N: Natural Language Processing with Deep Learning: https://www.youtube.com/playlist?list=PLoROMvodv4rMFqRtEuo6SGjY4XbRIVRd4
- [x] create all transcript page
- [x] create other transcript page
- [ ] order by date
- [ ] add more metadata like views, likes, ratio
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

- [ ] add financial samurai - https://podcasts.google.com/feed/aHR0cDovL2ZpbmFuY2lhbHNhbXVyYWkubGlic3luLmNvbS9yc3M
- [ ] add MLJ
```
    {
        "name": "martyn_lloyd_jones_trust",
        "url": "https://www.youtube.com/@MLJTrust",
        "in_file": "mljt_ids.txt",
        "file": "mljt_ids_done.txt"
    },
```
- [ ] figure out how to handle playlists where some channels are hidden
```
    {
        "name": "ask_pastor_john",
        "url": "https://www.youtube.com/playlist?list=PLFF7F6AE365DA3564",
        "in_file": "apj_ids.txt",
        "file": "apj_ids_done.txt"
    },    
    {
        "name": "ask_the_compound",
        "url": "https://www.youtube.com/playlist?list=PLZgCX3KJ3XGDSgkgav-pPd5Uq01F82jGa",
        "in_file": "ask_the_compound_ids.txt",
        "file": "ask_the_compound_ids_done.txt"
    },
```
- [] add acquired podcast, 575 episodes and they are long
```
    {
        "name": "acquired",
        "url": "https://www.youtube.com/@AcquiredFM",
        "in_file": "acquired_ids.txt",
        "file": "acquired_ids_done.txt"
    },
```

- [] add huberman full episodes