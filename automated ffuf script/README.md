# Automated FFUF Script

This directory contains the Python command-line utility used to automate ffuf scans for one or more web targets.

## Script

- `automated_ffuf_script.py` — Reads a target or target list, selects the appropriate SecLists wordlist, runs ffuf, and writes clean text reports.

## Run

```bash
python3 automated_ffuf_script.py example.com
python3 automated_ffuf_script.py -l targets.txt
```

## Requirements

- Python 3
- [ffuf](https://github.com/ffuf/ffuf) available on `PATH`
- SecLists installed under one of the Linux paths checked by the script

The script looks for `common.txt` and `api/api-endpoints.txt` in standard SecLists installation locations.

## Output

Reports are written to `ffuf_outputs/` in the current working directory. Temporary JSON output is removed after each scan.

## Target input

- A hostname such as `example.com`
- A full URL such as `https://example.com`
- A plain-text file containing one target per line

Only scan systems you own or are authorized to test.
