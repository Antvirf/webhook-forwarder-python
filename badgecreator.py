"""
Python script to get ratings and downloads from Garmin Marketplace, and create repo badges for both.
"""
import subprocess

import requests


def create_badge(text, value):
    """Given a text and a number, generate an .svg badge"""
    url = f"https://img.shields.io/badge/{text}-{value}-brightgreen"
    svg_text = requests.get(url).text

    with open(text+".svg", "w") as writer:
        writer.write(svg_text)


if __name__ == "__main__":
    # compute coverage value
    coverage_value = subprocess.check_output(
        "pytest --cov tests | grep 'TOTAL' | grep  -E -i -o '([0-9]+)%'", shell=True)

    coverage_value = str(coverage_value.decode("utf-8")).strip()
    create_badge("coverage", coverage_value)
