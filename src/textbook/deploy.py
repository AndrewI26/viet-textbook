"""Build the Docker image and run it locally, to check the deployment before shipping it.

Usage: uv run docker-test   (serves the image at http://localhost:8080)
"""

import shutil
import subprocess
import sys

from .common import ROOT

IMAGE = "viet-textbook"


def docker_test() -> None:
    if shutil.which("docker") is None:
        sys.exit("Docker isn't installed.")
    subprocess.run(["docker", "build", "-t", IMAGE, str(ROOT)], check=True)
    print("Serving the image at http://localhost:8080  (Ctrl+C to stop)")
    try:
        subprocess.run(["docker", "run", "--rm", "-p", "8080:80", IMAGE], check=True)
    except KeyboardInterrupt:
        print()
