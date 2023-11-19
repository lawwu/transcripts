import time
from pathlib import Path
from functools import wraps
import json
import pandas as pd
from datetime import datetime

project_dir = Path(__file__).resolve().parents[2]
data_dir = project_dir / "data"
raw_dir = data_dir / "raw"
interim_dir = data_dir / "interim"
processed_dir = data_dir / "processed"
external_dir = data_dir / "external"
model_dir = project_dir / "models"
transcripts_dir = data_dir / "transcripts"
videos_dir = data_dir / "videos"
html_dir = project_dir / "docs"
whispercpp_dir = project_dir / "whisper.cpp"
configs_dir = project_dir / "configs"


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(
            f"{func.__name__} completed. Time elapsed: {elapsed_time:.2f} seconds."
        )
        return result

    return wrapper


def dump_json_to_file(json_object, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_object, f, ensure_ascii=False, indent=4)


def convert_cache_to_dataframe(cache):
    # Initialize list to store flattened dictionaries
    flattened_data = []

    # Flatten dictionary structure
    for _, attributes in cache.items():
        # print(video)
        id_ = attributes["id"]
        title = attributes["title"]
        upload_date = attributes["upload_date"]
        upload_date_formatted = datetime.strptime(
            upload_date, "%Y%m%d"
        ).strftime("%Y-%m-%d")
        flattened_dict = {
            "id": id_,
            "title": title,
            "upload_date": upload_date_formatted,
        }
        flattened_data.append(flattened_dict)

    df = pd.DataFrame(flattened_data)
    df = df.sort_values(["upload_date"], ascending=False)
    return df
