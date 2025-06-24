# justfile for common project commands
# see here for more information: https://github.com/casey/just

# find system default shell
hashbang := if os() == 'macos' {
	'/usr/bin/env zsh'
} else {
	'/usr/bin/env bash'
}

# cifs / samba command based on operating system
# note for linux / non-mac:
# reads in the username so it may be used with the mount command
# note: cifs-utils is required for this (but may not explicitly be stated by mount command).
# You may install it with, for example: `sudo apt-get install cifs-utils`
cifs_or_samba_mount_command := if os() == 'macos' {
	'mount_smbfs //data.ucdenver.pvt/dept/SOM/DBMI/Bandicoot ~/mnt/isilon'
} else {
	'read -p "Isilon/CIFS username: " cifs_username && sudo mount -t cifs //data.ucdenver.pvt/dept/SOM/DBMI/Bandicoot ~/mnt/bandicoot -o username=$cifs_username,domainauto'
}

# show a list of just commands for this project
default:
  @just --list

# install the project for development purposes
@setup:
    #!{{hashbang}}
    uv pip install '.'

# mount a uca cifs / samba
@mount-isilon:
    #!{{hashbang}}
    if mount | grep "/mnt/isilon"; then
        echo "The isilon fileshare is already mounted."
    else
        # create a mount destination
        mkdir -p ~/mnt/isilon
        # run the mount command
        {{cifs_or_samba_mount_command}}
    fi

# run isilon demo
@run-isilon-demo:
    #!{{hashbang}}

    # mount isilon
    just mount-isilon

    # prepare the data
    uv run python src/demo/prepare_files.py

    # run the demo for mounted storage, storing the results in a notebook
    uv run papermill src/demo/demo_mounted.ipynb src/demo/demo_mounted.ipynb

    # run the demo for s3 storage, storing the results in a notebook
    uv run papermill src/demo/demo_s3.ipynb src/demo/demo_s3.ipynb

    # share a friendly message
    echo "Demo completed. The results are stored in src/demo/demo.ipynb."
