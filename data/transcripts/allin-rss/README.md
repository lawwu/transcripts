# All-In transcripts from the podcast feed

Transcripts of All-In episodes made from the podcast feed's MP3s
(`https://rss.libsyn.com/shows/254861/destinations/1928300.xml`) rather than
YouTube, which now refuses yt-dlp caption and audio downloads. Each file is
`<YYYY-MM-DD>-<title slug>.txt`, named by the feed's publish date and the
first eight words of the title, in the same `[start --> end]   text` line
format as the YouTube transcripts.

Two sets:

- **New episodes** — the weekly shows and predictions specials from
  January 2025 on that had no transcript here.
- **Redos** — 2020–2022 episodes whose large-v2 transcripts in
  `data/transcripts/<youtube id>.txt` are hallucination loops (the same line
  repeated hundreds of times; in some, most of the file). The old files are
  left in place.

Models:

- 156 files begin with `# mlx-community/parakeet-tdt-0.6b-v2`: NVIDIA
  Parakeet TDT 0.6B v2 run through parakeet-mlx (about 65× real time on an
  M1 Max), one punctuated sentence per line. It misspells names more than
  Whisper ("Sachs", "Jamath").
- The other 13 are whisper.cpp with `ggml-large-v3-turbo`.

Timestamps follow the MP3, which carries ads, so they run ahead of the
YouTube upload's clock.

Made for the All-In predictions tracker at
<https://apps.lawrencewu.net/all-in-predictions/> (source:
`apps/web/all-in-predictions/scripts/transcribe.py` in
<https://github.com/lawwu/lawrencewu-net>).
