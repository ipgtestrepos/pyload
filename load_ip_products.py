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

# csv file headers:
#   company,name,revision,ip_type,description,directory

ip_type_map = {
    "HARDIP" : "hard_ip",
    "SOFTIP" : "soft_ip"
}

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

def build_prod_find_command(row, global_args) -> list[str]:
    cmd = ["ipg", "prod", "find"]

    company = row.get("company_name", "").strip() or None
    product = row.get("product_name", "").strip() or None
    if company == None or product == None:
        print(f"prod_find:  {company}, {product}")
        return None

    cmd.extend(["--company", company])
    cmd.extend(["--product", product])

    cmd.extend(["--format", "json"])

    return cmd

def exec_command(cmd, global_args) -> tuple[dict[str,Any] | None, bool]:
    if cmd == None:
        print(f"❌ error building command.")
        return None, False

    retcode, stdout, stderr = run_command(cmd, working_dir=".")
    if retcode != 0:
        print(f"❌ command failed. Stopping.  return code: {retcode}")
        quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
        print(f"➡️   {quoted_cmd}")
        print(f"➡️   stdout: {stdout}")
        print(f"➡️   stderr: {stderr}")
        return None, False
    if stderr:
        print(f"⚠️ Error output:\n{stderr}")
        quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
        print(f"➡️   {quoted_cmd}")
        return None, False
    if stdout:
        data = process_json(stdout)
        return data, True 

def build_prod_import_command(row, global_args) -> list[str]:
    cmd = ["ipg", "prod", "import"]

    company = row.get("company_name", "").strip() or None
    product = row.get("product_name", "").strip() or None
    release = row.get("release", "").strip() or None
    directory = row.get("directory", "").strip() or None
    description = row.get("description", "").strip() or None
    ip_type = row.get("ip_type", "soft_ip").strip() or None
    ip_type = ip_type_map.get(ip_type, ip_type)  # convert from HARDIP, SOFTIP to ipgrid keywords
    if company == None or product == None or release == None or directory == None:
        return None

    cmd.extend(["--company", company])
    cmd.extend(["--product", product])
    cmd.extend(["--release", release])
    if description != "":
        cmd.extend(["--description", description])
    cmd.extend(["--package-sources"])
    cmd.extend(["--type", ip_type])
    cmd.extend(["--source-root", "."])    # the command pushes into the ip directory

    cmd.extend(["--quiet"])
    cmd.extend(["--format", "json"])

    return cmd

def build_policy_create_policy_command(row, global_args) -> list[str]:
    cmd = ["ipg", "auth", "policy", "create"]

    company = row.get("company_name", "").strip() or None
    product = row.get("product_name", "").strip() or None 
    if company == None or product == None:
        return None

    policy_name = company + "_" + product + "_auth"
    # statements are an array of policy objects
    statements = [{
        "Action": ["ipgrid:*"],
        "Effect": "allow",
        "Resource": "ipgrid:/product/" + company + "/" + product
    }]

    cmd.extend(["--policy", policy_name])
    cmd.extend(["--statement", json.dumps(statements)])

    cmd.extend(["--quiet"])
    cmd.extend(["--format", "json"])

    return cmd

def build_policy_account_command(row, global_args) -> list[str]:
    cmd = ["ipg", "auth", "account", "policy", "add"]

    company = row.get("company_name", "").strip() or None
    product = row.get("product_name", "").strip() or None 
    email = row.get("email", "").strip() or None
    if company == None or product == None or email == None:
        return None

    policy_name = company + "_" + product + "_auth"

    cmd.extend(["--policy", policy_name])
    cmd.extend(["--login", email])

    cmd.extend(["--quiet"])
    cmd.extend(["--format", "json"])

    return cmd


def build_label_create_command(row, global_args) -> list[str]:
    cmd = ["ipg", "label", "create"]

    company = row.get("company_name", "").strip() or None
    product = row.get("product_name", "").strip() or None 
    ipid = row.get("ipid", "").strip() or None

    if company == None or product == None or ipid == None:
        print("help")
        return None

    eccn = row.get("eccn", "")  # optional
    category = row.get("category", "")   # optional

    label_name = ipid
    payload = {
        "product_id": ipid,
        "company": company,
        "product": product,
        "URI": company + "/" + product,
        "eccn": eccn,
        "category":  category
    }

    cmd.extend(["--label", label_name])
    cmd.extend(["--payload", json.dumps(payload)])
    cmd.extend(["--public", "true"])

    cmd.extend(["--quiet"])
    cmd.extend(["--format", "json"])

    return cmd

def build_label_add_command(row, global_args) -> list[str]:
    cmd = ["ipg", "prod", "label", "add"]

    company = row.get("company_name", "").strip() or None
    product = row.get("product_name", "").strip() or None 
    ipid = row.get("ipid", "").strip() or None
    if company == None or product == None or ipid == None:
        return None

    label_name = ipid

    cmd.extend(["--company", company])
    cmd.extend(["--product", product])
    cmd.extend(["--label", label_name])

    cmd.extend(["--quiet"])
    cmd.extend(["--format", "json"])

    return cmd


def main(csv_file, global_args, no_exec):
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            #
            # 1. test for existing of product
            # 2. initialize product
            # 3. register release
            #
            ipdirectory = row.get("directory", "").strip() or None
            if ipdirectory == None:
                print(f"❌ Row {idx} directory for IP required")
                continue

            total_rel = 0
            cmd = build_prod_find_command(row, global_args)
            if no_exec:
                quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
                print(f"➡️ Row {idx} find command: {quoted_cmd}")
            else:
                data, ok = exec_command(cmd, global_args) 
                total_rel = len(data.get("data", []))
                company = row.get("company_name", "").strip() or None
                product = row.get("product_name", "").strip() or None 
                print(f"IP product {company}/{product}.  number of releases found: {total_rel}")


            if total_rel == 0:
                company = row.get("company_name", "").strip() or None
                product = row.get("product_name", "").strip() or None 
                print(f"  ...Loading IP product {company}/{product}. ")

                # Step 1.   Import product
                #--------------------------------
                cmd = build_prod_import_command(row, global_args)
                if no_exec:
                    quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
                    print(f"➡️ Row {idx} import command: {quoted_cmd}")
                else:
                    with pushd(ipdirectory):
                        data, ok = exec_command(cmd, global_args) 
                        if not ok:
                            print(data)
                            continue

                # Step 2.  Create and add label
                #--------------------------------
                cmd = build_label_create_command(row, global_args)
                if no_exec:
                    quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
                    print(f"➡️ Row {idx} create label command: {quoted_cmd}")
                else:
                    with pushd(ipdirectory):
                        data, ok = exec_command(cmd, global_args) 
                        if not ok:
                            print(data)
                            continue

                cmd = build_label_add_command(row, global_args)
                if no_exec:
                    quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
                    print(f"➡️ Row {idx} label add command: {quoted_cmd}")
                else:
                    with pushd(ipdirectory):
                        data, ok = exec_command(cmd, global_args) 
                        if not ok:
                            print(data)
                            continue

                # Step 3.  Create and add policy
                #--------------------------------
                cmd = build_policy_create_policy_command(row, global_args)
                if no_exec:
                    quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
                    print(f"➡️ Row {idx} policy create command: {quoted_cmd}")
                else:
                    with pushd(ipdirectory):
                        data, ok = exec_command(cmd, global_args) 
                        if not ok:
                            print(data)
                            continue

                cmd = build_policy_account_command(row, global_args)
                if no_exec:
                    quoted_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
                    print(f"➡️ Row {idx} policy add command: {quoted_cmd}")
                else:
                    with pushd(ipdirectory):
                        data, ok = exec_command(cmd, global_args) 
                        if not ok:
                            print(data)
                            continue
                        
        else:
            print("\n✅ All commands completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch runner for ipg with CSV input")
    parser.add_argument("csv_file", help="Path to CSV input file")
    parser.add_argument("--global-args", help="Extra args to pass to every ipgrid command", default="")
    parser.add_argument("--no-exec", action="store_true", help="Only show commands, do not execute them")
    args = parser.parse_args()

    main(args.csv_file, args.global_args, args.no_exec)


