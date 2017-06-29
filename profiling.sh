#!/usr/bin/env bash
python -m cProfile -s "cumtime" analysis/evolution.py > profiling_report.txt