# University of Colorado Anschutz Isilon with Python Demonstration

This repository demonstrates using the [University of Colorado Anschutz Isilon](https://www.cuanschutz.edu/offices/office-of-information-technology/tools-services/storage-servers-and-backups) storage solution with Python.
We seek to understand how this works and how it performs more generally.

Our approach here focuses on mounting the Isilon path to a local directory on a machine, then performing work using that mounted directory.

## Development

1. [Install `uv`](https://docs.astral.sh/uv/getting-started/installation/).
1. [Install `just`](https://github.com/casey/just?tab=readme-ov-file#installation).
1. Install package locally (e.g. `uv pip install -e "."`).
1. Run various other tasks using [just](https://github.com/casey/just) (e.g. `just run-isilon-demo`)

## Tasks

[Just](https://github.com/casey/just) tasks may be run to help generate results without needing to run individual files or perform additional discovery within this project.
You can show all available tasks with `just` (which lists all tasks).

Examples:

```bash
just run-isilon-demo
```

## Isilon notes

- Isilon requires you to have access through the UCA VPN or local campus network.
- Isilon may be mounted on MacOS using `mount_smbfs`.
  - Using a mount path without a username or password specified will attempt to mount the directory using your MacOS user which is currently logged in (which may differ from your UCA account credentials).
- Isilon may be mounted on Linux using `mount -t cifs`.

## CIFS benchmarks

With the Bandicoot share already mounted, time listing its top-level directory:

```bash
just benchmark-isilon-dir ~/mnt/bandicoot .
# Or choose another directory relative to the mountpoint:
uv run --no-sync python src/demo/benchmark_mounted.py --mount ~/mnt/bandicoot \
  --directory temp_imgs/G9-2 --repeats 3
```

This enumerates immediate directory entries only (no recursive walk, file
contents, or per-entry metadata lookups). It reports entry count and elapsed
time per pass plus the median. Short lists and repeated runs are especially
sensitive to caches, so the first pass and exact directory size matter more
than the warm-cache median.

To benchmark reading an existing file on the share instead:

```bash
just benchmark-isilon ~/mnt/bandicoot temp_imgs/G9-2/placeholder_cell-masks.tiff
# Or, without just (and with a custom repeat count):
uv run --no-sync python src/demo/benchmark_mounted.py --mount ~/mnt/bandicoot \
  --file temp_imgs/G9-2/placeholder_cell-masks.tiff --repeats 3
```

Replace the mountpoint and relative file/directory path if your share or data is
elsewhere (e.g. `~/mnt/isilon` when mounted with the provided macOS recipe).
The read and listing modes require an active CIFS/SMB mount and never create,
modify, or delete files on Isilon. File mode reads a nonempty file in 1 MiB
chunks and reports elapsed time and throughput per pass plus a median. Repeated
reads can be served from caches, so these figures are not cold-cache network
speeds. The two small TIFFs cited by the demo are downloaded locally by
`prepare_files.py`; they are not assumed to be present on the mounted share.
Do not use `just run-isilon-demo` for read-only testing: that older demo writes
and removes files on Isilon.

### Observed results (October 2026)

From a Mac with Bandicoot mounted over SMB 3.1.1, one full read of the existing
`phenotypic_profiling_data/JUMP Raw Data/merged/BR00118042_merged_sc.parquet`
(6,727,972,763 bytes, or 6.27 GiB) took 64.870 s: **98.91 MiB/s**. The
read-only command was:

```bash
uv run --no-sync python src/demo/benchmark_mounted.py --mount ~/mnt/bandicoot \
  --file 'phenotypic_profiling_data/JUMP Raw Data/merged/BR00118042_merged_sc.parquet' \
  --repeats 1
```

The route to the SMB server used an Ethernet interface negotiated at 1 Gb/s.
The observed rate is about 830 Mb/s, or 83% of the link's theoretical
119.21 MiB/s maximum before network and SMB overhead. This is **client-to-share
throughput**, not the maximum capability of the storage cluster. The file's
size was unchanged afterward; no Isilon data was created or removed.

In a separate listing test, enumerating Bandicoot's 39 top-level entries took
29.801 ms on the first observed pass and 0.204/0.179 ms on subsequent passes.
The share had already been inspected, so none of these is guaranteed to be a
cold-cache measurement. Directory enumeration does not measure file transfer
speed or the server's per-operation SMB latency.

[Dell's read-test guidance](https://www.dell.com/support/kbdoc/en-us/000015384/emc14001790-troubleshooting-performance-issues)
recommends an existing file larger than 1 GB that was not just created for the
test. This read meets the size and existing-file criteria, but we cannot prove
the server cache was cold. Dell's [up to 35 GB/s per-node claim](https://www.dell.com/en-us/blog/powerscale-onefs-9-15-strengthens-dell-ai-data-platform-foundations/)
applies to a specific newer PowerScale platform based on PowerEdge R7725xd
with OneFS 9.15 or later. Bandicoot's node model and OneFS version are unknown,
and a single 1 Gb/s SMB client cannot test that cluster-side claim. Dell also
[distinguishes client throughput from available storage bandwidth](https://infohub.delltechnologies.com/l/dell-powerscale-network-design-considerations/bandwidth-and-throughput-3/).
A direct vendor comparison would require the actual hardware/software
configuration, a faster client path and server-side statistics during the run.

### Bounded write benchmark (October 2026)

Write mode creates a unique directory directly under the mounted share and a
new file inside it; it refuses to overwrite existing paths. The size is capped
at 1,024 MiB per run. The files are **left in place**, even on failure, rather
than deleting any data. To reproduce the two tests:

```bash
just benchmark-isilon-write ~/mnt/bandicoot zeros
just benchmark-isilon-write ~/mnt/bandicoot random
```

Each test wrote 1 GiB in 1 MiB chunks and then called `fsync`. The write phase
includes generating random data where applicable; the total includes the
`fsync` call but not directory creation or the final file-size check.

| New file | Write phase | `fsync` | Write + `fsync` |
| --- | --- | --- | --- |
| Zeros | 8.615 s (118.87 MiB/s) | 1.979 s | 10.593 s (96.67 MiB/s) |
| Random | 8.322 s (123.05 MiB/s) | 1.725 s | 10.047 s (101.92 MiB/s) |

Both files were verified to be 1,073,741,824 bytes, with the first and last
MiB checked. They remain under these newly created directories:

- `~/mnt/bandicoot/benchmark-write-8489dd9d004d4d2a982d0c796bb8fa62/`
- `~/mnt/bandicoot/benchmark-write-53ddbf7512034d74a39acfc559ed0204/`

Dell's [single-stream write example](https://www.dell.com/support/kbdoc/en-us/000015384/emc14001790-troubleshooting-performance-issues)
creates a 1 GiB file of zeros with `dd` on the cluster or a UNIX/Linux client.
Our zero-data SMB test is similar in size and pattern, but runs from a Mac and
also reports `fsync`; it is **not** a matched test of Dell's node-side example.
Dell's 35 GB/s per-node headline cited above is a **read** claim, not a write
target. The random-data run reduces the chance of server-side compression making
the result look unusually fast. In fact, its write-only rate exceeds the
1 Gb/s link's theoretical 119.21 MiB/s, indicating buffering; use the
write-plus-`fsync` figures for a more conservative client-side comparison.
Even `fsync` acknowledgment does not establish the cluster's physical-disk
throughput. The approximately 97–102 MiB/s total rates, like the earlier
99 MiB/s read, are consistent with this client's 1 Gb/s network path; they
cannot establish Bandicoot's maximum write performance.
