# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# + [markdown] papermill={"duration": 0.005255, "end_time": "2025-04-23T23:12:13.300071", "exception": false, "start_time": "2025-04-23T23:12:13.294816", "status": "completed"}
# # University of Colorado Anschutz Isilon with Python Demonstration Notebook
#
# This notebook demonstrates various work with files to better
# understand how the University of Colorado Anschutz Isilon
# storage solution performs with a locally mounted directory.

# + papermill={"duration": 0.344351, "end_time": "2025-04-23T23:12:13.662449", "exception": false, "start_time": "2025-04-23T23:12:13.318098", "status": "completed"}
import pathlib
import shutil

import matplotlib.pyplot as plt
from skimage import io

# setup a data directory reference
source_data_dir = str(pathlib.Path("src/demo/data/input").resolve())
target_data_dir = str(pathlib.Path("src/demo/data/output").resolve())
isilon_dir = pathlib.Path("~/mnt/isilon/example").expanduser()

# + papermill={"duration": 0.006186, "end_time": "2025-04-23T23:12:13.669724", "exception": false, "start_time": "2025-04-23T23:12:13.663538", "status": "completed"}
# show the files
print("List of files:\n", list(pathlib.Path(source_data_dir).rglob("*.tif")))

# + papermill={"duration": 0.005539, "end_time": "2025-04-23T23:12:13.677947", "exception": false, "start_time": "2025-04-23T23:12:13.672408", "status": "completed"}
# %%time

# create a directory within isilon storage to add files
isilon_dir.mkdir(exist_ok=True)

# + papermill={"duration": 0.421523, "end_time": "2025-04-23T23:12:14.101899", "exception": false, "start_time": "2025-04-23T23:12:13.680376", "status": "completed"}
# %%time

# upload the files to isilon one by one
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    shutil.copy(src=image_file, dst=isilon_dir)

# + papermill={"duration": 0.154178, "end_time": "2025-04-23T23:12:14.258582", "exception": false, "start_time": "2025-04-23T23:12:14.104404", "status": "completed"}
# %%time

# download the files to isilon one by one
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    shutil.copy(src=image_file, dst=target_data_dir)

# + papermill={"duration": 0.170106, "end_time": "2025-04-23T23:12:14.429928", "exception": false, "start_time": "2025-04-23T23:12:14.259822", "status": "completed"}
# %%time

# display images by reading them locally
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    plt.clf()
    plt.imshow(io.imread(image_file), cmap="gray")
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.179508, "end_time": "2025-04-23T23:12:14.613150", "exception": false, "start_time": "2025-04-23T23:12:14.433642", "status": "completed"}
# %%time

# display images by reading them from isilon
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    plt.clf()
    plt.imshow(io.imread(image_file), cmap="gray")
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.055651, "end_time": "2025-04-23T23:12:14.673795", "exception": false, "start_time": "2025-04-23T23:12:14.618144", "status": "completed"}
# %%time

# remove files from isilon
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    image_file.unlink()
