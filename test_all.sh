#!/bin/bash
set -ex

ruff format */*.py
ruff check */*.py

pip install .

