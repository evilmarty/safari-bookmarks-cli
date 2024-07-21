#!/usr/bin/env bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
PROJECT_DIR=$(realpath -- "$(dirname -- "${SCRIPT_DIR}")")
VIRTUAL_ENV_DIR="${PROJECT_DIR}/.venv"
ACTIVATE_PATH="${VIRTUAL_ENV_DIR}/bin/activate"

if [[ "${PROJECT_DIR}" != "${PWD}" ]]; then
	echo "Cannot bootstrap outside of project directory. Aborting..."
	return 1 # Use return instead of exit otherwise if script is sourced will cause session to end
fi

if [[ ! -d .venv ]]; then
	echo "Virtual environment not detected. Creating..."
	python3 -m venv "${VIRTUAL_ENV_DIR}"
fi

if [[ "${VIRTUAL_ENV}" != "${VIRTUAL_ENV_DIR}" ]]; then
	if [[ -z "${VIRTUAL_ENV:-}" ]]; then
		echo "Activating virtual environment"
	else
		echo "Detected another activated virtual environment. Switching..."
		[[ $(type -t deactivate) == function ]] && deactivate
	fi
	source "${ACTIVATE_PATH}"

	echo "Installing dependencies..."
	pip3 install .[tests]
fi
