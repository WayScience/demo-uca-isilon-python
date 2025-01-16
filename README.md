# University of Colorado Anschutz Isilon with Python Demonstration

This repository demonstrates using the [University of Colorado Anschutz Isilon](https://www.cuanschutz.edu/offices/office-of-information-technology/tools-services/storage-servers-and-backups) storage solution with Python.
We seek to understand how this works and how it performs more generally.

Our approach here focuses on mounting the Isilon path to a local directory on a machine, then performing work using that mounted directory.

## Development

1. [Install `uv`](https://docs.astral.sh/uv/getting-started/installation/).
1. [Install `just`](https://github.com/casey/just?tab=readme-ov-file#installation).
1. Install package locally (e.g. `uv pip install -e "."`).
1. Run various other tasks using [just](https://github.com/casey/just) (e.g. `just tiff_to_omezarr`)

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
