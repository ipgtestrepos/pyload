import csv
import subprocess
import shlex
import sys
import argparse
import json
import tempfile
import os
import tarfile
from typing import Any

from contextlib import contextmanager

@contextmanager
def pushd(new_dir):
    prev_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(prev_dir)

# returns either "dir", "tar", "tgz", "unknown"
def archive_path_type(path: str) -> str:
    if os.path.isdir(path):
        return "dir"

    if os.path.isfile(path):
        try:
            # Try opening as a tar archive
            with tarfile.open(path, "r") as tar:
                if tarfile.is_tarfile(path):
                    if path.endswith(".tar"):
                        return "tar"
                    else:
                        return "tgz"
        except tarfile.ReadError:
            pass  # Not a tar file

    return "unknown"
    
def process_json(json_str):
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON output: {e}")
        print("Raw output:")
        print(json_str)
        return None
      
def run_command(cmd, working_dir=None):
    try:
        if working_dir and not os.path.isdir(working_dir):
            return -1, "", f"Working directory does not exist: {working_dir}"       
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=working_dir
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -1, "", f"Unhandled error: {e}"

def exec_command(cmd, global_args) -> tuple[dict[str,Any] | None, bool]:
    if cmd == None:
        print(f"❌ error building command.")
        return None, False

    retcode, stdout, stderr = run_command(cmd, working_dir=".")
    if retcode != 0:
        print(f"❌ command failed. Stopping.  return code: {retcode}")
        quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
        print(f"➡️   {quoted_cmd}")
        return None, False
    if stderr:
        print(f"⚠️ Error output:\n{stderr}")
        quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
        print(f"➡️   {quoted_cmd}")
        return None, False
    if stdout:
        data = process_json(stdout)
        return data, True 

def build_chip_init_command(chip_name, intrnl_name, ips, global_args, no_exec):
    cmd = ["ipg", "chip", "init"]

    cmd.extend(["--chip", chip_name])
    cmd.extend(["--internal-name", intrnl_name])

    for ip in ips:
        cmd.extend(["--ip", ip])

    cmd.extend(["--quiet"])
    cmd.extend(["--format", "json"])

    quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
    print(f"➡️ label find command: {quoted_cmd}")
    if no_exec:
        return

    data, ok = exec_command(cmd, global_args)
    if not ok:
        print(f"could not create chip: {chip_name}")
    
    return
    
# this is what the json payload looks like:
#{
#  "status": "OK",
#  "message": "Found 1 label",
#  "data": [
#    {
#      "id": "ab533260-6c6e-41da-9e94-26a94649e750",
#      "name": "12345",
#      "description": "",
#      "payload": {
#        "URI": "mystic/dmx",
#        "category": "memory",
#        "company": "mystic",
#        "eccn": "4G909",
#        "product": "dmx",
#        "product_id": "12345"
#      },
#      "updated_by": "77cc0c5d-a66b-4b97-b936-dca0f334706c",
#      "updated_at": "2025-08-07T22:25:27.231429-04:00",
#      "created_by": "77cc0c5d-a66b-4b97-b936-dca0f334706c",
#      "created_at": "2025-08-07T22:25:27.231429-04:00",
#      "used_in": [
#        {
#          "resource_type": "product",
#          "resource_uri": "mystic/dmx"
#        }
#      ]
#    }
#  ]
#}

def find_ip_label(row, global_args, no_exec) -> str:
    cmd = ["ipg", "label", "find"]

    ipid = row.get("ipid", "").strip() or None
    if ipid == None:
        return None

    cmd.extend([ipid])

    cmd.extend(["--quiet"])
    cmd.extend(["--format", "json"])

    quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
    print(f"➡️ label find command: {quoted_cmd}")
    if no_exec:
        return "<dummylabel>"

    data, ok = exec_command(cmd, global_args)
    if not ok:
        print(f"could not locate label for {ipid}")
        return ""
    
    uri_value = data.get("data", [{}])[0].get("payload", {}).get("URI")

    return uri_value


def main(chip_name, intrnl_name, ip_file, global_args, no_exec):
    ips = []
    with open(ip_file, newline='') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            #
            # extract the data from the IPID label
            ip = find_ip_label(row, global_args, no_exec)
            ips.append(ip)

    build_chip_init_command(chip_name, intrnl_name, ips, global_args, no_exec)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch runner for chip init with CSV IP product input")
    parser.add_argument("chip_name", help="Chip name")
    parser.add_argument("intrnl_name", help="Chip internal name")
    parser.add_argument("ip_file", help="Path to IP list CSV input file")
    parser.add_argument("--global-args", help="Extra args to pass to every ipgrid command", default="")
    parser.add_argument("--no-exec", action="store_true", help="Only show commands, do not execute them")
    args = parser.parse_args()

    main(args.chip_name, args.intrnl_name, args.ip_file, args.global_args, args.no_exec)


