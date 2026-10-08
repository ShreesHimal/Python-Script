#!/usr/bin/env python3
import os
import sys
import subprocess
import re
import argparse
import json
from pathlib import Path

# Target configurations
OUTPUT_DIR = Path("ffuf_outputs")
REQUEST_RATE = 50 

def locate_wordlists():
    """Dynamically looks for the required wordlists in common installation variants."""
    search_paths = [
        Path("/usr/share/seclists/Discovery/Web-Content"),
        Path("/usr/share/seclists/SecLists/Discovery/Web-Content"),
        Path("/opt/seclists/Discovery/Web-Content")
    ]
    
    standard_list = None
    api_list = None
    
    for base_path in search_paths:
        s_check = base_path / "common.txt"
        a_check = base_path / "api/api-endpoints.txt"
        
        if s_check.exists() and a_check.exists():
            standard_list = s_check
            api_list = a_check
            break

    if not standard_list:
        for root, dirs, files in os.walk("/usr/share/seclists"):
            if "directory-list-2.3-medium.txt" in files:
                standard_list = Path(root) / "directory-list-2.3-medium.txt"
            if "api-endpoints.txt" in files:
                api_list = Path(root) / "api-endpoints.txt"
                
    if not standard_list or not api_list:
        print("[-] Critical Error: Could not locate your SecLists files.")
        sys.exit(1)
        
    return standard_list, api_list

def clean_filename(url):
    """Converts a target URL into a safe, clean string for text filenames."""
    name = re.sub(r'^[^/]*//', '', url)
    name = re.sub(r'[/:]', '_', name)
    return f"ffuf_{name}.txt"

def process_target(host, standard_list, api_list):
    """Executes the native ffuf command and formats output strictly as text."""
    host = host.strip()
    if not host or host.startswith('#'):
        return

    if not host.startswith(('http://', 'https://')):
        url = f"https://{host}"
    else:
        url = host

    # Temporary JSON file to parse exact results accurately
    out_file_txt = OUTPUT_DIR / clean_filename(url)
    tmp_json = OUTPUT_DIR / f"tmp_{clean_filename(url)}.json"

    if "api" in url.lower():
        print(f"\n[+] API target structure detected: {url}")
        target_list = api_list
        status_codes = "200,204,301,302,401,403"
    else:
        print(f"\n[*] Standard property detected: {url}")
        target_list = standard_list
        status_codes = "200,204,301,302,307,403"

    # Command using JSON output internally for reliable data extraction
    cmd = [
        "ffuf",
        "-w", str(target_list),
        "-u", f"{url}/FUZZ",
        "-mc", status_codes,
        "-rate", str(REQUEST_RATE),
        "-of", "json",
        "-o", str(tmp_json)
    ]

    # Reconstruct exact string for the file header
    executed_command = " ".join(cmd)

    try:
        # Run silently so terminal output stays clean
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Read the temporary JSON results and write your custom clean layout
        results = []
        if tmp_json.exists() and tmp_json.stat().st_size > 0:
            with open(tmp_json, 'r') as jf:
                data = json.load(jf)
                # FFUF structure stores valid hits in the 'results' list
                for match in data.get("results", []):
                    path = match.get("input", {}).get("FUZZ", "")
                    status = match.get("status", "")
                    results.append(f"/{path} [{status}]")

        # Write clean custom output file
        with open(out_file_txt, 'w') as tf:
            tf.write(f"{url}\n")
            tf.write(f"{executed_command}\n")
            for result in results:
                tf.write(f"{result}\n")

        print(f"[✓] Clean output written to: {out_file_txt}")

    except FileNotFoundError:
        print("[-] Error: 'ffuf' binary is missing from your system $PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[-] Execution bypassed or faulted on target {url}: {e}")
    finally:
        # Cleanup temporary JSON files
        if tmp_json.exists():
            tmp_json.unlink()

def main():
    parser = argparse.ArgumentParser(
        description="Automate targeted ffuf scanning with clean line-by-line output templates.",
        usage="./ffuf_script.py [target_url or -l list.txt]"
    )
    
    parser.add_argument("positional_target", nargs="?", help="A single target URL or domain")
    parser.add_argument("-l", "--list", dest="list_file", help="File containing a list of target hosts")

    args = parser.parse_args()

    standard_list, api_list = locate_wordlists()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.list_file:
        if not os.path.exists(args.list_file):
            print(f"[-] Error: Target file '{args.list_file}' not found.")
            sys.exit(1)
            
        print(f"[*] Processing hosts from list file: {args.list_file}")
        with open(args.list_file, 'r') as f:
            for line in f:
                process_target(line, standard_list, api_list)

    elif args.positional_target:
        if os.path.exists(args.positional_target) and not args.positional_target.startswith(('http://', 'https://')):
            print(f"[-] Warning: '{args.positional_target}' looks like a local file.")
            
        process_target(args.positional_target, standard_list, api_list)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
