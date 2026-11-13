#!/bin/bash
set -ex

ruff format */*.py
ruff check */*.py

python -m pip install .[dev]

nc2 tests/NeuroML2/c302_D_Pharyngeal.net.nml -nogui
nc2 tests/NeuroML2/Example2.net.nml -nogui

