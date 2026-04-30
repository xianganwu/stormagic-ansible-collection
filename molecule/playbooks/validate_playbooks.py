"""Validate playbooks against Red Hat validated content standards."""

import os
import re
import sys

import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLAYBOOK_DIR = os.path.join(PROJECT_ROOT, "playbooks")
EXAMPLES_DIR = os.path.join(PROJECT_ROOT, "examples")

BUILTIN_KEYS = {
    "name", "hosts", "gather_facts", "vars", "tasks", "module_defaults",
    "serial", "max_fail_percentage", "tags", "block", "rescue", "always",
    "when", "register", "loop", "loop_control", "delegate_to",
    "changed_when", "failed_when", "check_mode", "notify", "become",
    "become_user", "environment", "no_log", "retries", "delay", "until",
    "ignore_errors", "connection", "collections",
}

DESTRUCTIVE_PLAYBOOKS = [
    "svsan_patching_workflow.yml",
    "svsan_ha_setup.yml",
    "svsan_add_storage.yml",
    "svkms_key_rotation.yml",
]

EXPECTED_PLAYBOOKS = [
    "svkms_backup.yml",
    "svkms_full_setup.yml",
    "svkms_key_rotation.yml",
    "svsan_add_storage.yml",
    "svsan_capacity_report.yml",
    "svsan_ha_setup.yml",
    "svsan_patching_workflow.yml",
]

errors = []


def error(msg):
    errors.append(msg)
    print(f"  FAIL: {msg}")


def check_fqcn(tasks, filename):
    for task in tasks:
        if "block" in task:
            check_fqcn(task["block"], filename)
            check_fqcn(task.get("rescue", []), filename)
            continue
        for key in task:
            if key not in BUILTIN_KEYS and "." not in key:
                error(f'{filename}: task "{task.get("name", "?")}" uses short module name "{key}"')


print("=" * 60)
print("Playbook Validation — Red Hat Validated Content Standards")
print("=" * 60)

# 1. All expected playbooks exist
print("\n1. Playbook existence")
for pb in EXPECTED_PLAYBOOKS:
    path = os.path.join(PLAYBOOK_DIR, pb)
    if os.path.isfile(path):
        print(f"  OK: {pb}")
    else:
        error(f"{pb} not found")

# 2. Structural validation
print("\n2. Play structure (name, hosts, gather_facts, tasks, module_defaults)")
for pb in EXPECTED_PLAYBOOKS:
    path = os.path.join(PLAYBOOK_DIR, pb)
    if not os.path.isfile(path):
        continue
    with open(path) as f:
        plays = yaml.safe_load(f)
    if not isinstance(plays, list):
        error(f"{pb}: not a list of plays")
        continue
    for play in plays:
        for field in ("name", "hosts", "gather_facts", "tasks", "module_defaults"):
            if field not in play:
                error(f'{pb}: play "{play.get("name", "?")}" missing {field}')
    print(f"  OK: {pb}")

# 3. Tags on all top-level tasks
print("\n3. Tags on all tasks")
for pb in EXPECTED_PLAYBOOKS:
    path = os.path.join(PLAYBOOK_DIR, pb)
    if not os.path.isfile(path):
        continue
    with open(path) as f:
        plays = yaml.safe_load(f)
    for play in plays:
        for task in play.get("tasks", []):
            if "block" in task:
                continue
            if "tags" not in task:
                error(f'{pb}: task "{task.get("name", "?")}" missing tags')
    print(f"  OK: {pb}")

# 4. FQCN on all module calls
print("\n4. FQCN validation")
for pb in EXPECTED_PLAYBOOKS:
    path = os.path.join(PLAYBOOK_DIR, pb)
    if not os.path.isfile(path):
        continue
    with open(path) as f:
        plays = yaml.safe_load(f)
    for play in plays:
        check_fqcn(play.get("tasks", []), pb)
    print(f"  OK: {pb}")

# 5. Destructive playbooks have block/rescue
print("\n5. Block/rescue on destructive playbooks")
for pb in DESTRUCTIVE_PLAYBOOKS:
    path = os.path.join(PLAYBOOK_DIR, pb)
    if not os.path.isfile(path):
        continue
    with open(path) as f:
        plays = yaml.safe_load(f)
    found = any(
        "block" in t and "rescue" in t
        for p in plays
        for t in p.get("tasks", [])
    )
    if not found:
        error(f"{pb}: destructive but no block/rescue")
    else:
        print(f"  OK: {pb}")

# 6. Vault variable chain consistency
print("\n6. Vault variable chain")
vault_path = os.path.join(EXAMPLES_DIR, "inventory", "group_vars", "all", "vault.yml")
if os.path.isfile(vault_path):
    with open(vault_path) as f:
        vault_vars = set(re.findall(r"^(vault_\w+):", f.read(), re.MULTILINE))
    for pb in EXPECTED_PLAYBOOKS:
        path = os.path.join(PLAYBOOK_DIR, pb)
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            refs = set(re.findall(r"\{\{\s*(vault_\w+)", f.read()))
        missing = refs - vault_vars
        if missing:
            error(f"{pb}: references undefined vault vars: {missing}")
        else:
            print(f"  OK: {pb} ({len(refs)} vault refs)")
    print(f"  Vault template defines {len(vault_vars)} variables")

# 7. No plaintext credentials
print("\n7. No plaintext credentials")
cred_patterns = [
    r"password:\s*[\"']?(?!\{\{)[A-Za-z0-9]",
    r"api_key:\s*[\"']?(?!\{\{)[A-Za-z0-9]",
]
for pb in EXPECTED_PLAYBOOKS:
    path = os.path.join(PLAYBOOK_DIR, pb)
    if not os.path.isfile(path):
        continue
    with open(path) as f:
        for i, line in enumerate(f, 1):
            if line.strip().startswith("#"):
                continue
            for pat in cred_patterns:
                if re.search(pat, line):
                    error(f"{pb}:{i}: possible plaintext credential")
    print(f"  OK: {pb}")

# 8. Inventory template completeness
print("\n8. Inventory template groups")
inv_path = os.path.join(EXAMPLES_DIR, "inventory", "hosts.yml")
if os.path.isfile(inv_path):
    with open(inv_path) as f:
        inv = yaml.safe_load(f)
    children = inv.get("all", {}).get("children", {})
    for group in ("svkms_servers", "windows_mgmt", "svsan_vsas", "esxi_hosts"):
        if group in children:
            print(f"  OK: {group}")
        else:
            error(f"Missing inventory group: {group}")

# Summary
print("\n" + "=" * 60)
if errors:
    print(f"FAILED: {len(errors)} error(s)")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("PASSED: All 8 validation checks passed")
    sys.exit(0)
