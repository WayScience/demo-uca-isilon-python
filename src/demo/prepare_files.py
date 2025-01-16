"""
Prepares files for the demonstration work.
"""

import pathlib

import requests

# references to dirs we'll work with
download_dir = "src/demo/data/input"
output_dir = "src/demo/data/output"

# create dirs if they don't already exist
pathlib.Path(download_dir).mkdir(parents=True, exist_ok=True)
pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

# setup filenames and figshare urls for demonstration work
images = {
    "B1_01_2_1_GFP_001.tif": "https://figshare.com/ndownloader/files/39518140",
    "B1_01_2_2_GFP_001.tif": "https://figshare.com/ndownloader/files/39518143",
}

# download the files for work with the demonstration
for filename, url in images.items():
    try:
        # Send GET request to the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Check for HTTP request errors

        # Write the content to a file
        with open((output_file := f"{download_dir}/{filename}"), "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"File downloaded successfully as {output_file}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
