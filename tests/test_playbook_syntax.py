"""Validate that all example playbooks pass ansible-playbook --syntax-check."""

import glob
import os
import subprocess

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAYBOOKS = sorted(glob.glob(os.path.join(PROJECT_ROOT, "playbooks", "*.yml")))


def _collections_path():
    """Return the directory containing ansible_collections/stormagic/stormagic.

    In CI the checkout is into ansible_collections/stormagic/stormagic under
    $GITHUB_WORKSPACE, so ANSIBLE_COLLECTIONS_PATH is set to $GITHUB_WORKSPACE.
    Locally the repo root contains a symlink at
    ansible_collections/stormagic/stormagic -> <repo>.
    """
    return os.environ.get("ANSIBLE_COLLECTIONS_PATH", PROJECT_ROOT)


@pytest.mark.parametrize(
    "playbook",
    PLAYBOOKS,
    ids=lambda p: os.path.basename(p),
)
def test_playbook_syntax(playbook):
    env = os.environ.copy()
    env["ANSIBLE_COLLECTIONS_PATH"] = _collections_path()
    result = subprocess.run(
        ["ansible-playbook", "--syntax-check", playbook],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    assert result.returncode == 0, (
        f"Syntax check failed for {os.path.basename(playbook)}:\n{result.stderr}"
    )
