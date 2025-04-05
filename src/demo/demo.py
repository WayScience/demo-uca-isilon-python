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

# + [markdown] papermill={"duration": 0.004578, "end_time": "2025-01-16T17:54:07.495347", "exception": false, "start_time": "2025-01-16T17:54:07.490769", "status": "completed"}
# # University of Colorado Anschutz Isilon with Python Demonstration Notebook
#
# This notebook demonstrates various work with files to better
# understand how the University of Colorado Anschutz Isilon
# storage solution performs.

# + papermill={"duration": 0.342874, "end_time": "2025-01-16T17:54:07.842190", "exception": false, "start_time": "2025-01-16T17:54:07.499316", "status": "completed"}
import pathlib
import shutil

import matplotlib.pyplot as plt
from skimage import io

# setup a data directory reference
source_data_dir = str(pathlib.Path("src/demo/data/input").resolve())
target_data_dir = str(pathlib.Path("src/demo/data/output").resolve())
isilon_dir = pathlib.Path("~/mnt/isilon/example").expanduser()

# + papermill={"duration": 0.005683, "end_time": "2025-01-16T17:54:07.848952", "exception": false, "start_time": "2025-01-16T17:54:07.843269", "status": "completed"}
# show the files
print("List of files:\n", list(pathlib.Path(source_data_dir).rglob("*.tif")))

# +
# %%time

# create a directory within isilon storage to add files
isilon_dir.mkdir(exist_ok=True)

# + papermill={"duration": 0.27517, "end_time": "2025-01-16T17:54:08.126964", "exception": false, "start_time": "2025-01-16T17:54:07.851794", "status": "completed"}
# %%time

# upload the files to isilon one by one
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    shutil.copy(src=image_file, dst=isilon_dir)

# + papermill={"duration": 0.125019, "end_time": "2025-01-16T17:54:08.255048", "exception": false, "start_time": "2025-01-16T17:54:08.130029", "status": "completed"}
# %%time

# download the files to isilon one by one
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    shutil.copy(src=image_file, dst=target_data_dir)

# + papermill={"duration": 0.166833, "end_time": "2025-01-16T17:54:08.424427", "exception": false, "start_time": "2025-01-16T17:54:08.257594", "status": "completed"}
# %%time

# display images by reading them locally
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    plt.clf()
    plt.imshow(io.imread(image_file), cmap="gray")
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.173802, "end_time": "2025-01-16T17:54:08.600285", "exception": false, "start_time": "2025-01-16T17:54:08.426483", "status": "completed"}
# %%time

# display images by reading them from isilon
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    plt.clf()
    plt.imshow(io.imread(image_file), cmap="gray")
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.054132, "end_time": "2025-01-16T17:54:08.657459", "exception": false, "start_time": "2025-01-16T17:54:08.603327", "status": "completed"}
# %%time

# remove files from isilon
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    image_file.unlink()
