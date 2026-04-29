from __future__ import absolute_import, division, print_function

import json
import os
import ssl
import subprocess
import sys
import time
import urllib.request

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

CONTAINER_NAME = "svkms-mock-test"
IMAGE_NAME = "svkms-mock:test"
MOCK_DIR = os.path.join(PROJECT_ROOT, "tests", "mock_svkms")
HOST = "localhost"
PORT = 1443


def _docker(*args):
    return subprocess.run(
        ["docker"] + list(args),
        capture_output=True, text=True, timeout=120,
    )


def _wait_for_health(host, port, timeout=30):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    deadline = time.time() + timeout
    url = "https://{0}:{1}/v0/health".format(host, port)
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, context=ctx, timeout=5)
            data = json.loads(resp.read())
            if data.get("status") == "healthy":
                return True
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError("Mock SvKMS not healthy after {0}s".format(timeout))


@pytest.fixture(scope="session")
def svkms_client():
    from ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api import (
        SvKMSClient,
    )

    _docker("rm", "-f", CONTAINER_NAME)

    result = _docker("build", "-t", IMAGE_NAME, MOCK_DIR)
    if result.returncode != 0:
        pytest.fail("Docker build failed:\n{0}".format(result.stderr))

    result = _docker(
        "run", "-d",
        "--name", CONTAINER_NAME,
        "-p", "{0}:1443".format(PORT),
        IMAGE_NAME,
    )
    if result.returncode != 0:
        pytest.fail("Docker run failed:\n{0}".format(result.stderr))

    try:
        _wait_for_health(HOST, PORT)
    except TimeoutError as e:
        logs = _docker("logs", CONTAINER_NAME)
        _docker("rm", "-f", CONTAINER_NAME)
        pytest.fail("{0}\nContainer logs:\n{1}\n{2}".format(e, logs.stdout, logs.stderr))

    client = SvKMSClient(
        host=HOST,
        port=PORT,
        api_key="test-api-key",
        validate_certs=False,
    )

    yield client

    _docker("rm", "-f", CONTAINER_NAME)
