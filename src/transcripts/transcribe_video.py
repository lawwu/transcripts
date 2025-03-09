import argparse
import ffmpeg
import logging
import subprocess
from pathlib import Path

from transcripts.utils import (
    transcripts_dir,
    model_dir,
    whispercpp_dir,
    timeit,
)

# Setup logging
log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)

def extract_audio(video_file):
    """
    Extract audio from video file.

    Parameters:
    - video_file: Path to the video file
    """
    audio_file = video_file.parent / f"{video_file.stem}_audio.wav"
    logging.info(f"Extracting audio from {video_file} to {audio_file}")
    # try:
    #     # Run ffmpeg command
    #     (
    #         ffmpeg.input(video_file)
    #         .output(str(audio_file), acodec="mp3", ac=2, ar="48k", ab="192k")
    #         .run(overwrite_output=True)
    #     )
    try:
        command = ["ffmpeg", "-y", "-i", str(video_file), "-ar", "16000", str(audio_file)]
        print(command)
        subprocess.run(command)
    except Exception as e:
        logging.error(f"Error extracting audio: {e}")

def ensure_wav_16k(input_file):
    """
    Ensure the audio file is in WAV format with a 16kHz sample rate.

    Parameters:
    - input_file: Path to the input audio file
    """
    output_file_16k = input_file.parent / f"{input_file.stem}_16k.wav"
    command = ["ffmpeg", "-y", "-i", str(input_file), "-ar", "16000", str(output_file_16k)]
    subprocess.run(command)
    return output_file_16k

@timeit
def run_whisper(input_file, model_name, num_threads=7, num_processors=1):
    model_path = model_dir / model_name
    output_path = transcripts_dir / f"{input_file.stem}.txt"

    whisper_main = whispercpp_dir / "main"
    command = f"{whisper_main} -m {model_path} -t {num_threads} -p {num_processors} -f {input_file} > {output_path}"
    subprocess.run(command, shell=True)

def main():
    parser = argparse.ArgumentParser(description="Process local audio or video files.")
    parser.add_argument("file_path", type=str, help="Path to the audio or video file")
    parser.add_argument("--model_name", type=str, default="ggml-large-v3-turbo", help="Name of the whisper model to use")
    args = parser.parse_args()

    file_path = Path(args.file_path)
    if not file_path.exists():
        logger.error("File does not exist.")
        return

    if file_path.suffix.lower() in [".mp4", ".mov"]:  # Video file
        extract_audio(file_path)
        audio_file = file_path.parent / f"{file_path.stem}_audio.wav"
    elif file_path.suffix.lower() in [".wav", ".mp3"]:  # Audio file
        audio_file = file_path
    else:
        logger.error("Unsupported file type.")
        return

    processed_file = ensure_wav_16k(audio_file)
    run_whisper(processed_file, args.model_name)

if __name__ == "__main__":
    main()