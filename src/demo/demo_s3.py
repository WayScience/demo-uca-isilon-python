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

# + [markdown] papermill={"duration": 0.009082, "end_time": "2025-04-24T22:42:17.665763", "exception": false, "start_time": "2025-04-24T22:42:17.656681", "status": "completed"}
# # University of Colorado Anschutz Isilon with Python Demonstration Notebook
#
# This notebook demonstrates various work with files to better
# understand how the University of Colorado Anschutz Isilon
# storage solution performs when using the
# [S3-API](https://infohub.delltechnologies.com/fr-fr/l/dell-powerscale-onefs-s3-api-guide/overview-5983/).

# + papermill={"duration": 0.77896, "end_time": "2025-04-24T22:42:18.459890", "exception": false, "start_time": "2025-04-24T22:42:17.680930", "status": "completed"}
import io
import os
import pathlib
import warnings

import duckdb
import matplotlib.pyplot as plt
import minio
import pandas as pd
from dotenv import load_dotenv
from skimage import io as skio
from urllib3.exceptions import InsecureRequestWarning

# Load environment variables from a .env file.
# We use this to avoid plaintext secrets within
# repositories.
load_dotenv()

# We filter warnings to avoid cert check warnings about the host.
# In this case we assume trust for data.ucdenver.pvt instead of
# checking it from the certificate.
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# setup common references for this notebook
source_data_dir = str(pathlib.Path("src/demo/data/input").resolve())
target_data_dir = str(pathlib.Path("src/demo/data/output").resolve())
target_bucket_object_path = "example/"
target_bucket = "bandicoot"

# + papermill={"duration": 0.012853, "end_time": "2025-04-24T22:42:18.474228", "exception": false, "start_time": "2025-04-24T22:42:18.461375", "status": "completed"}
# Create MinIO client with your Isilon S3-compatible endpoint
client = minio.Minio(
    endpoint="data.ucdenver.pvt:9021",
    access_key=os.getenv("ISILON_S3_KEY"),
    secret_key=os.getenv("ISILON_S3_SECRET"),
    secure=True,
    cert_check=False,
)

# + papermill={"duration": 0.665245, "end_time": "2025-04-24T22:42:19.146700", "exception": false, "start_time": "2025-04-24T22:42:18.481455", "status": "completed"}
# check if a bucket exists
if not client.bucket_exists(bucket_name=target_bucket):
    raise LookupError(f"Bucket with name {target_bucket} does not exist on system.")
else:
    print(f"Found the bucket: {target_bucket}")

# + papermill={"duration": 0.047243, "end_time": "2025-04-24T22:42:19.197816", "exception": false, "start_time": "2025-04-24T22:42:19.150573", "status": "completed"}
# %%time

# create a "directory" within the bucket by uploading an empty object
# note: there are no true directories within buckets,
# only objects which represent them. Because of this we
# upload an object with directory-like properties.
result = client.put_object(
    bucket_name=target_bucket,
    object_name=target_bucket_object_path,
    data=io.BytesIO(b""),
    length=0,
    content_type="application/x-directory",
)
result.object_name

# + papermill={"duration": 0.01984, "end_time": "2025-04-24T22:42:19.219770", "exception": false, "start_time": "2025-04-24T22:42:19.199930", "status": "completed"}
# List objects within the bucket


def print_objects_in_bucket(client: minio.api.Minio, bucket: str) -> None:
    """
    Prints objects found within the bucket.

    Args:
        client: minio.api.Minio
            A Minio Python API client for
            interacting with S3-like hosts.
        bucket: str
            A string which represents a bucket
            to target for listing objects.

    Returns:
        None
    """

    for obj in client.list_objects(bucket_name=target_bucket, recursive=True):
        print(obj.object_name, "(dir)" if obj.is_dir else "")


print_objects_in_bucket(client=client, bucket=target_bucket)

# + papermill={"duration": 0.175846, "end_time": "2025-04-24T22:42:19.407405", "exception": false, "start_time": "2025-04-24T22:42:19.231559", "status": "completed"}
# %%time

# upload the files to isilon one by one
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    result = client.fput_object(
        bucket_name=target_bucket,
        object_name=f"{target_bucket_object_path}{image_file.name}",
        file_path=image_file,
    )

# + papermill={"duration": 0.031544, "end_time": "2025-04-24T22:42:19.446507", "exception": false, "start_time": "2025-04-24T22:42:19.414963", "status": "completed"}
# show the remote objects
print_objects_in_bucket(client=client, bucket=target_bucket)

# + papermill={"duration": 0.12276, "end_time": "2025-04-24T22:42:19.580815", "exception": false, "start_time": "2025-04-24T22:42:19.458055", "status": "completed"}
# %%time

# download the files
for obj in client.list_objects(
    bucket_name=target_bucket,
    recursive=True,
    # we prefix this loop to search under
    # an object storage "directory"
    prefix=target_bucket_object_path,
):
    client.fget_object(
        bucket_name=target_bucket,
        object_name=obj.object_name,
        # we build a path based on a target directory and object name
        # (otherwise we may get a full object path for a name)
        file_path=f"{target_data_dir}/{pathlib.Path(obj.object_name).name}",
    )

# + papermill={"duration": 0.014355, "end_time": "2025-04-24T22:42:19.605857", "exception": false, "start_time": "2025-04-24T22:42:19.591502", "status": "completed"}
# show the files
print("List of files:\n", list(pathlib.Path(source_data_dir).rglob("*.tif")))

# + papermill={"duration": 0.1723, "end_time": "2025-04-24T22:42:19.788132", "exception": false, "start_time": "2025-04-24T22:42:19.615832", "status": "completed"}
# %%time

# display images by reading them locally
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    plt.clf()
    plt.imshow(skio.imread(image_file), cmap="gray")
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.354483, "end_time": "2025-04-24T22:42:20.155797", "exception": false, "start_time": "2025-04-24T22:42:19.801314", "status": "completed"}
# %%time

# display images by reading them from isilon s3
for obj in client.list_objects(
    bucket_name=target_bucket,
    recursive=True,
    prefix=target_bucket_object_path,
):
    plt.clf()
    plt.imshow(
        skio.imread(
            # use bytesio to simulate a file
            io.BytesIO(
                # read an object's bytes into skimage
                client.get_object(
                    bucket_name=target_bucket, object_name=obj.object_name
                ).read()
            )
        ),
        cmap="gray",
    )
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.035105, "end_time": "2025-04-24T22:42:20.194442", "exception": false, "start_time": "2025-04-24T22:42:20.159337", "status": "completed"}
# %%time

# remove files from isilon
for obj in client.list_objects(
    bucket_name=target_bucket,
    recursive=True,
    prefix=target_bucket_object_path,
):
    client.remove_object(bucket_name=target_bucket, object_name=obj.object_name)

# + papermill={"duration": 0.022626, "end_time": "2025-04-24T22:42:20.231743", "exception": false, "start_time": "2025-04-24T22:42:20.209117", "status": "completed"}
# show the remote objects
print_objects_in_bucket(client=client, bucket=target_bucket)

# + papermill={"duration": 0.04769, "end_time": "2025-04-24T22:42:20.290585", "exception": false, "start_time": "2025-04-24T22:42:20.242895", "status": "completed"}
# create a dataframe and export to Parquet
df = pd.DataFrame(
    {
        "image_id": ["img1", "img2", "img3"],
        "label": ["cat", "dog", "bird"],
        "score": [0.95, 0.89, 0.78],
    }
).to_parquet((example_parquet := f"{source_data_dir}/example.parquet"), index=False)

# put the Parquet file in the bucket
client.fput_object(
    bucket_name=target_bucket,
    object_name=f"{target_bucket_object_path}/example.parquet",
    file_path=example_parquet,
)

# show the remote objects
print_objects_in_bucket(client=client, bucket=target_bucket)

# + papermill={"duration": 0.44722, "end_time": "2025-04-24T22:42:20.744181", "exception": false, "start_time": "2025-04-24T22:42:20.296961", "status": "completed"}
# %%time

# read the Parquet from S3
pd.read_parquet(
    f"s3://{target_bucket}/example/example.parquet",
    storage_options={
        "key": os.getenv("ISILON_S3_KEY"),
        "secret": os.getenv("ISILON_S3_SECRET"),
        "client_kwargs": {
            "endpoint_url": "https://data.ucdenver.pvt:9021",
            "verify": False,
        },
    },
)

# + papermill={"duration": 0.990053, "end_time": "2025-04-24T22:42:21.738553", "exception": false, "start_time": "2025-04-24T22:42:20.748500", "status": "completed"}
# %%time

with duckdb.connect() as ddb:
    df = ddb.execute(
        f"""
        /* install httpfs for duckdb */
        INSTALL httpfs;
        LOAD httpfs;

        /* add a custom secret for access to isilon */
        CREATE SECRET (
            TYPE s3,
            KEY_ID '{os.getenv("ISILON_S3_KEY")}',
            SECRET '{os.getenv("ISILON_S3_SECRET")}',
            ENDPOINT 'data.ucdenver.pvt:9021'
        );

        /* perform selection on the file */
        SELECT * FROM read_parquet('s3://{target_bucket}/example/example.parquet');
        """
    ).df()

df

# + papermill={"duration": 0.035391, "end_time": "2025-04-24T22:42:21.783523", "exception": false, "start_time": "2025-04-24T22:42:21.748132", "status": "completed"}
# remove the Parquet file from the bucket
client.remove_object(
    bucket_name=target_bucket,
    object_name=f"{target_bucket_object_path}/example.parquet",
)

# show the remote objects
print_objects_in_bucket(client=client, bucket=target_bucket)
