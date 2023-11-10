import os
from typing import List

from setuptools import find_packages, setup

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


def read_requirements(name: str) -> List[str]:
    """
    To read the requirements
    """
    file = f"./{name}.txt"
    fpath = os.path.join(ROOT_DIR, file)
    with open(fpath) as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


requirements = read_requirements("requirements")

setup(
    url="https://github.com/lawwu/transcripts",
    author="Lawrence Wu",
    name="transcripts",
    version="0.1.1",
    packages=find_packages("src"),
    package_dir={"transcripts": "src/transcripts"},
    install_requires=requirements,
)
