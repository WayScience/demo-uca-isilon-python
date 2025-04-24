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

# + [markdown] papermill={"duration": 0.002203, "end_time": "2025-04-24T22:42:14.689897", "exception": false, "start_time": "2025-04-24T22:42:14.687694", "status": "completed"}
# # University of Colorado Anschutz Isilon with Python Demonstration Notebook
#
# This notebook demonstrates various work with files to better
# understand how the University of Colorado Anschutz Isilon
# storage solution performs with a locally mounted directory.

# + papermill={"duration": 0.441802, "end_time": "2025-04-24T22:42:15.139535", "exception": false, "start_time": "2025-04-24T22:42:14.697733", "status": "completed"}
import pathlib
import shutil

import matplotlib.pyplot as plt
from skimage import io

# setup a data directory reference
source_data_dir = str(pathlib.Path("src/demo/data/input").resolve())
target_data_dir = str(pathlib.Path("src/demo/data/output").resolve())
isilon_dir = pathlib.Path("~/mnt/isilon/example").expanduser()

# + papermill={"duration": 0.010481, "end_time": "2025-04-24T22:42:15.151824", "exception": false, "start_time": "2025-04-24T22:42:15.141343", "status": "completed"}
# show the files
print("List of files:\n", list(pathlib.Path(source_data_dir).rglob("*.tif")))

# + papermill={"duration": 0.014535, "end_time": "2025-04-24T22:42:15.172355", "exception": false, "start_time": "2025-04-24T22:42:15.157820", "status": "completed"}
# %%time

# create a directory within isilon storage to add files
isilon_dir.mkdir(exist_ok=True)

# + papermill={"duration": 0.338747, "end_time": "2025-04-24T22:42:15.515695", "exception": false, "start_time": "2025-04-24T22:42:15.176948", "status": "completed"}
# %%time

# upload the files to isilon one by one
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    shutil.copy(src=image_file, dst=isilon_dir)

# + papermill={"duration": 0.181238, "end_time": "2025-04-24T22:42:15.711103", "exception": false, "start_time": "2025-04-24T22:42:15.529865", "status": "completed"}
# %%time

# download the files to isilon one by one
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    shutil.copy(src=image_file, dst=target_data_dir)

# + papermill={"duration": 0.187643, "end_time": "2025-04-24T22:42:15.906189", "exception": false, "start_time": "2025-04-24T22:42:15.718546", "status": "completed"}
# %%time

# display images by reading them locally
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    plt.clf()
    plt.imshow(io.imread(image_file), cmap="gray")
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.187112, "end_time": "2025-04-24T22:42:16.103346", "exception": false, "start_time": "2025-04-24T22:42:15.916234", "status": "completed"}
# %%time

# display images by reading them from isilon
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    plt.clf()
    plt.imshow(io.imread(image_file), cmap="gray")
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.062512, "end_time": "2025-04-24T22:42:16.169077", "exception": false, "start_time": "2025-04-24T22:42:16.106565", "status": "completed"}
# %%time

# remove files from isilon
for image_file in pathlib.Path(isilon_dir).rglob("*.tif"):
    image_file.unlink()
