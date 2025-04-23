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

# + [markdown] papermill={"duration": 0.009573, "end_time": "2025-04-23T23:12:16.160401", "exception": false, "start_time": "2025-04-23T23:12:16.150828", "status": "completed"}
# # University of Colorado Anschutz Isilon with Python Demonstration Notebook
#
# This notebook demonstrates various work with files to better
# understand how the University of Colorado Anschutz Isilon
# storage solution performs when using the
# [S3-API](https://infohub.delltechnologies.com/fr-fr/l/dell-powerscale-onefs-s3-api-guide/overview-5983/).

# + papermill={"duration": 0.59795, "end_time": "2025-04-23T23:12:16.763027", "exception": false, "start_time": "2025-04-23T23:12:16.165077", "status": "completed"}
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
# checking it with from the certificate.
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# setup common references for this notebook
source_data_dir = str(pathlib.Path("src/demo/data/input").resolve())
target_data_dir = str(pathlib.Path("src/demo/data/output").resolve())
target_bucket_object_path = "example/"
target_bucket = "bandicoot"

# + papermill={"duration": 0.007917, "end_time": "2025-04-23T23:12:16.772302", "exception": false, "start_time": "2025-04-23T23:12:16.764385", "status": "completed"}
# Create MinIO client with your Isilon S3-compatible endpoint
client = minio.Minio(
    endpoint="data.ucdenver.pvt:9021",
    access_key=os.getenv("ISILON_S3_KEY"),
    secret_key=os.getenv("ISILON_S3_SECRET"),
    secure=True,
    cert_check=False,
)

# + papermill={"duration": 0.085469, "end_time": "2025-04-23T23:12:16.860645", "exception": false, "start_time": "2025-04-23T23:12:16.775176", "status": "completed"}
# check if a bucket exists
client.bucket_exists(bucket_name=target_bucket)

# + papermill={"duration": 0.013032, "end_time": "2025-04-23T23:12:16.876687", "exception": false, "start_time": "2025-04-23T23:12:16.863655", "status": "completed"}
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

# + papermill={"duration": 0.012867, "end_time": "2025-04-23T23:12:16.892907", "exception": false, "start_time": "2025-04-23T23:12:16.880040", "status": "completed"}
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

# + papermill={"duration": 0.267299, "end_time": "2025-04-23T23:12:17.161669", "exception": false, "start_time": "2025-04-23T23:12:16.894370", "status": "completed"}
# %%time

# upload the files to isilon one by one
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    result = client.fput_object(
        bucket_name=target_bucket,
        object_name=f"{target_bucket_object_path}{image_file.name}",
        file_path=image_file,
    )

# + papermill={"duration": 0.012721, "end_time": "2025-04-23T23:12:17.179327", "exception": false, "start_time": "2025-04-23T23:12:17.166606", "status": "completed"}
# show the remote objects
print_objects_in_bucket(client=client, bucket=target_bucket)

# + papermill={"duration": 0.092667, "end_time": "2025-04-23T23:12:17.275431", "exception": false, "start_time": "2025-04-23T23:12:17.182764", "status": "completed"}
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

# + papermill={"duration": 0.006265, "end_time": "2025-04-23T23:12:17.285311", "exception": false, "start_time": "2025-04-23T23:12:17.279046", "status": "completed"}
# show the files
print("List of files:\n", list(pathlib.Path(source_data_dir).rglob("*.tif")))

# + papermill={"duration": 0.159671, "end_time": "2025-04-23T23:12:17.449096", "exception": false, "start_time": "2025-04-23T23:12:17.289425", "status": "completed"}
# %%time

# display images by reading them locally
for image_file in pathlib.Path(source_data_dir).rglob("*.tif"):
    plt.clf()
    plt.imshow(skio.imread(image_file), cmap="gray")
    plt.axis("off")
    plt.show()

# + papermill={"duration": 0.304935, "end_time": "2025-04-23T23:12:17.759226", "exception": false, "start_time": "2025-04-23T23:12:17.454291", "status": "completed"}
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

# + papermill={"duration": 0.026836, "end_time": "2025-04-23T23:12:17.791705", "exception": false, "start_time": "2025-04-23T23:12:17.764869", "status": "completed"}
# %%time

# remove files from isilon
for obj in client.list_objects(
    bucket_name=target_bucket,
    recursive=True,
    prefix=target_bucket_object_path,
):
    client.remove_object(bucket_name=target_bucket, object_name=obj.object_name)

# + papermill={"duration": 0.01341, "end_time": "2025-04-23T23:12:17.811103", "exception": false, "start_time": "2025-04-23T23:12:17.797693", "status": "completed"}
# show the remote objects
print_objects_in_bucket(client=client, bucket=target_bucket)

# + papermill={"duration": 0.036111, "end_time": "2025-04-23T23:12:17.853829", "exception": false, "start_time": "2025-04-23T23:12:17.817718", "status": "completed"}
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

# + papermill={"duration": 0.630102, "end_time": "2025-04-23T23:12:18.487205", "exception": false, "start_time": "2025-04-23T23:12:17.857103", "status": "completed"}
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

# + papermill={"duration": 0.608262, "end_time": "2025-04-23T23:12:19.099176", "exception": false, "start_time": "2025-04-23T23:12:18.490914", "status": "completed"}
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

# + papermill={"duration": 0.020188, "end_time": "2025-04-23T23:12:19.124357", "exception": false, "start_time": "2025-04-23T23:12:19.104169", "status": "completed"}
# remove the Parquet file from the bucket
client.remove_object(
    bucket_name=target_bucket,
    object_name=f"{target_bucket_object_path}/example.parquet",
)

# show the remote objects
print_objects_in_bucket(client=client, bucket=target_bucket)
