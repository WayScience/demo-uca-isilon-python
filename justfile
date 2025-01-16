# justfile for common project commands
# see here for more information: https://github.com/casey/just

# find system default shell
hashbang := if os() == 'macos' {
	'/usr/bin/env zsh'
} else {
	'/usr/bin/env bash'
}

# cifs / samba command based on operating system
cifs_or_samba_mount_command := if os() == 'macos' {
	'mount_smbfs //data.ucdenver.pvt/dept/SOM/SOMDean/Testing/DBMITest ~/mnt/isilon'
} else {
	'sudo mount -t cifs //data.ucdenver.pvt/dept/SOM/SOMDean/Testing/DBMITest -o username='
}

# show a list of just commands for this project
default:
  @just --list

# install the project for development purposes
@setup:
    #!{{hashbang}}
    uv pip install '.'

# run testing on development source
@test:
    #!{{hashbang}}
    uv run pre-commit run -a
    uv run pytest

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

    # run the test, storing the results in a notebook
    uv run papermill src/demo/demo.ipynb src/demo/demo.ipynb
