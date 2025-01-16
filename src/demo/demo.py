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

# + [markdown] papermill={"duration": 0.001344, "end_time": "2025-01-16T17:49:48.873038", "exception": false, "start_time": "2025-01-16T17:49:48.871694", "status": "completed"}
# # University of Colorado Anschutz Isilon with Python Demonstration Notebook
#
# This notebook demonstrates various work with files to better
# understand how the University of Colorado Anschutz Isilon
# storage solution performs.

# + papermill={"duration": 0.325393, "end_time": "2025-01-16T17:49:49.201157", "exception": false, "start_time": "2025-01-16T17:49:48.875764", "status": "completed"}
import pathlib
import shutil

import matplotlib.pyplot as plt
from skimage import io

# setup a data directory reference
source_data_dir = str(pathlib.Path("src/demo/data/input").resolve())
target_data_dir = str(pathlib.Path("src/demo/data/output").resolve())
isilon_dir = pathlib.Path("~/mnt/isilon").expanduser()

# + papermill={"duration": 0.006053, "end_time": "2025-01-16T17:49:49.208266", "exception": false, "start_time": "2025-01-16T17:49:49.202213", "status": "completed"}
# show the files
print("List of files:\n", list(pathlib.Path(source_data_dir).rglob("*.tif")))

# + papermill={"duration": 0.292352, "end_time": "2025-01-16T17:49:49.947420", "exception": false, "start_time": "2025-01-16T17:49:49.655068", "status": "completed"}
# %%time

# upload the files to isilon one by one
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    shutil.copy(src=image_file, dst=isilon_dir)

# + papermill={"duration": 0.1294, "end_time": "2025-01-16T17:49:50.079102", "exception": false, "start_time": "2025-01-16T17:49:49.949702", "status": "completed"}
# %%time

# download the files to isilon one by one
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    shutil.copy(src=image_file, dst=target_data_dir)

# + papermill={"duration": 0.169881, "end_time": "2025-01-16T17:49:50.252137", "exception": false, "start_time": "2025-01-16T17:49:50.082256", "status": "completed"}
# %%time

# display images by reading them locally
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    plt.clf()
    plt.imshow(io.imread(image_file), cmap="gray")
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.176502, "end_time": "2025-01-16T17:49:50.430753", "exception": false, "start_time": "2025-01-16T17:49:50.254251", "status": "completed"}
# %%time

# display images by reading them from isilon
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    plt.clf()
    plt.imshow(io.imread(image_file), cmap="gray")
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.054803, "end_time": "2025-01-16T17:49:50.488530", "exception": false, "start_time": "2025-01-16T17:49:50.433727", "status": "completed"}
# %%time

# remove files from isilon
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    image_file.unlink()
