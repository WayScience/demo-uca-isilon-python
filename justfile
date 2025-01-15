# justfile for common project commands
# see here for more information: https://github.com/casey/just

# find system default shell
hashbang := if os() == 'macos' {
	'/usr/bin/env zsh'
} else {
	'/usr/bin/env bash'
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
