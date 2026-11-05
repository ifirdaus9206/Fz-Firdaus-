#!/usr/bin/env python3
"""ketua_weekly.py — pembalut cron untuk tools/weekly_check.py di ~/hermes-console.

Cron Hermes memerlukan skrip di ~/.hermes20/scripts/, jadi fail ini hanya
menjalankan skrip sebenar dengan argv yang sama.
"""
import runpy
import sys

TARGET = "/data/data/com.termux/files/home/hermes-console/tools/weekly_check.py"

if __name__ == "__main__":
    sys.argv[0] = TARGET
    runpy.run_path(TARGET, run_name="__main__")
