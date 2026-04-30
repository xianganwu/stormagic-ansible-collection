from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import re

import yaml
import pytest


MODULES_DIR = os.path.join(
    os.path.dirname(__file__),
    os.pardir, os.pardir, os.pardir, os.pardir,
    "plugins", "modules",
)

PS1_MODULES = sorted(
    f[:-4] for f in os.listdir(MODULES_DIR) if f.endswith(".ps1")
)


def _load_py_doc(module_name):
    py_path = os.path.join(MODULES_DIR, module_name + ".py")
    with open(py_path) as fh:
        content = fh.read()
    match = re.search(r'DOCUMENTATION\s*=\s*r"""(.*?)"""', content, re.DOTALL)
    assert match, "No DOCUMENTATION in {0}.py".format(module_name)
    return yaml.safe_load(match.group(1))


def _load_ps1_options(module_name):
    ps1_path = os.path.join(MODULES_DIR, module_name + ".ps1")
    with open(ps1_path) as fh:
        content = fh.read()
    options = set(re.findall(r'(\w+)\s*=\s*@\{\s*type\s*=', content))
    return options


class TestSvSANArgspecConsistency:
    @pytest.mark.parametrize("module_name", PS1_MODULES, ids=PS1_MODULES)
    def test_ps1_options_match_py_documentation(self, module_name):
        """Every option in the PS1 $spec must appear in the Python DOCUMENTATION."""
        doc = _load_py_doc(module_name)
        py_options = set(doc.get("options", {}).keys())
        ps1_options = _load_ps1_options(module_name)
        missing_in_py = ps1_options - py_options
        assert not missing_in_py, (
            "{0}: PS1 options {1} not documented in Python".format(module_name, missing_in_py)
        )

    @pytest.mark.parametrize("module_name", PS1_MODULES, ids=PS1_MODULES)
    def test_py_options_exist_in_ps1(self, module_name):
        """Every option in the Python DOCUMENTATION must exist in the PS1 $spec."""
        doc = _load_py_doc(module_name)
        py_options = set(doc.get("options", {}).keys())
        ps1_options = _load_ps1_options(module_name)
        extra_in_py = py_options - ps1_options
        assert not extra_in_py, (
            "{0}: Python documents {1} not in PS1 $spec".format(module_name, extra_in_py)
        )

    @pytest.mark.parametrize("module_name", PS1_MODULES, ids=PS1_MODULES)
    def test_ps1_password_fields_have_no_log(self, module_name):
        """Password fields in PS1 must have no_log = $true."""
        ps1_path = os.path.join(MODULES_DIR, module_name + ".ps1")
        with open(ps1_path) as fh:
            content = fh.read()
        for match in re.finditer(r'(\w*password\w*)\s*=\s*@\{([^}]+)\}', content, re.IGNORECASE):
            param_name = match.group(1)
            param_body = match.group(2)
            assert "no_log" in param_body, (
                "{0}: {1} missing no_log".format(module_name, param_name)
            )

    @pytest.mark.parametrize("module_name", PS1_MODULES, ids=PS1_MODULES)
    def test_ps1_supports_check_mode(self, module_name):
        """All SvSAN PS1 modules must support check mode."""
        ps1_path = os.path.join(MODULES_DIR, module_name + ".ps1")
        with open(ps1_path) as fh:
            content = fh.read()
        assert "supports_check_mode" in content, (
            "{0}: missing supports_check_mode in $spec".format(module_name)
        )
