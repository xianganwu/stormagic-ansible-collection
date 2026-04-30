from __future__ import absolute_import, division, print_function
__metaclass__ = type

import yaml
import pytest

from ansible_collections.xianganwu.stormagic.plugins.modules import (
    svsan_pool,
    svsan_pool_info,
    svsan_target,
    svsan_target_info,
    svsan_mirror,
    svsan_mirror_info,
    svsan_config,
    svsan_config_info,
    svsan_health_check,
    svsan_license,
    svsan_vsa,
    svsan_esxi_preflight,
)

SVSAN_MODULES = [
    svsan_pool,
    svsan_pool_info,
    svsan_target,
    svsan_target_info,
    svsan_mirror,
    svsan_mirror_info,
    svsan_config,
    svsan_config_info,
    svsan_health_check,
    svsan_license,
    svsan_vsa,
    svsan_esxi_preflight,
]

SVSAN_MODULE_IDS = [m.__name__.rsplit(".", maxsplit=1)[-1] for m in SVSAN_MODULES]

SVSAN_STATE_MODULES = [
    svsan_pool,
    svsan_target,
    svsan_mirror,
    svsan_config,
    svsan_license,
    svsan_vsa,
]

SVSAN_INFO_MODULES = [
    svsan_pool_info,
    svsan_target_info,
    svsan_mirror_info,
    svsan_config_info,
]

SVSAN_STATE_MODULE_IDS = [m.__name__.rsplit(".", maxsplit=1)[-1] for m in SVSAN_STATE_MODULES]
SVSAN_INFO_MODULE_IDS = [m.__name__.rsplit(".", maxsplit=1)[-1] for m in SVSAN_INFO_MODULES]


class TestSvSANDocumentationStructure:
    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_documentation_is_valid_yaml(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        assert isinstance(doc, dict)

    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_documentation_has_required_fields(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        assert "module" in doc, "missing 'module' field"
        assert "short_description" in doc, "missing 'short_description'"
        assert "description" in doc, "missing 'description'"
        assert isinstance(doc["description"], list), "'description' must be a list"
        assert "author" in doc, "missing 'author'"

    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_documentation_has_version_added(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        assert "version_added" in doc

    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_documentation_has_options(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        assert "options" in doc

    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_documentation_has_seealso(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        assert "seealso" in doc, "missing 'seealso' cross-references"
        assert isinstance(doc["seealso"], list)
        assert len(doc["seealso"]) > 0

    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_documentation_has_doc_fragment(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        if doc["module"] == "svsan_esxi_preflight":
            return
        fragments = doc.get("extends_documentation_fragment", [])
        assert "xianganwu.stormagic.svsan" in fragments, "missing svsan doc fragment"


class TestSvSANDocumentationOptions:
    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_vsa_hostname_documented(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        options = doc.get("options", {})
        mod_name = doc["module"]
        if mod_name == "svsan_esxi_preflight":
            assert "vcenter_hostname" in options
        else:
            assert "vsa_hostname" in options

    @pytest.mark.parametrize("module", SVSAN_STATE_MODULES, ids=SVSAN_STATE_MODULE_IDS)
    def test_state_modules_have_state_option(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        options = doc.get("options", {})
        mod_name = doc["module"]
        if mod_name in ("svsan_license", "svsan_health_check", "svsan_config"):
            return
        assert "state" in options, "{0} should document 'state' option".format(mod_name)
        state_opt = options["state"]
        assert "choices" in state_opt

    @pytest.mark.parametrize("module", SVSAN_INFO_MODULES, ids=SVSAN_INFO_MODULE_IDS)
    def test_info_modules_have_no_state(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        options = doc.get("options", {})
        assert "state" not in options, "info modules should not have 'state'"


class TestSvSANExamples:
    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_examples_is_valid_yaml(self, module):
        examples = yaml.safe_load(module.EXAMPLES)
        assert isinstance(examples, list), "EXAMPLES must be a YAML list of tasks"
        assert len(examples) >= 2, "should have at least 2 examples"

    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_examples_use_fqcn(self, module):
        examples = yaml.safe_load(module.EXAMPLES)
        for task in examples:
            task_keys = [k for k in task.keys() if k not in (
                "name", "register", "when", "delegate_to", "check_mode",
                "loop", "tags", "block", "rescue", "always",
            )]
            for key in task_keys:
                if key.startswith("xianganwu.stormagic."):
                    break
                if key.startswith("ansible.builtin."):
                    continue
            else:
                if task_keys:
                    assert any(
                        k.startswith("xianganwu.stormagic.") or k.startswith("ansible.builtin.")
                        for k in task_keys
                    ), "examples should use FQCN: {0}".format(task_keys)


class TestSvSANReturn:
    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_return_is_valid_yaml(self, module):
        ret = yaml.safe_load(module.RETURN)
        assert isinstance(ret, dict), "RETURN must be a YAML dict"
        assert len(ret) > 0, "RETURN should document at least one return value"

    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_return_values_have_description(self, module):
        ret = yaml.safe_load(module.RETURN)
        for key, value in ret.items():
            assert "description" in value, "return value '{0}' missing description".format(key)
            assert "type" in value, "return value '{0}' missing type".format(key)

    @pytest.mark.parametrize("module", SVSAN_INFO_MODULES, ids=SVSAN_INFO_MODULE_IDS)
    def test_info_modules_return_list_or_dict(self, module):
        ret = yaml.safe_load(module.RETURN)
        has_collection = any(
            v.get("type") in ("list", "dict") for v in ret.values()
        )
        assert has_collection, "info modules should return a list or dict"

    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_return_values_have_returned_field(self, module):
        ret = yaml.safe_load(module.RETURN)
        for key, value in ret.items():
            assert "returned" in value, "return value '{0}' missing 'returned' field".format(key)


class TestSvSANModuleNaming:
    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_module_name_matches_filename(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        expected = module.__name__.rsplit(".", maxsplit=1)[-1]
        assert doc["module"] == expected

    @pytest.mark.parametrize("module", SVSAN_INFO_MODULES, ids=SVSAN_INFO_MODULE_IDS)
    def test_info_module_name_ends_with_info(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        assert doc["module"].endswith("_info")

    @pytest.mark.parametrize("module", SVSAN_MODULES, ids=SVSAN_MODULE_IDS)
    def test_short_description_not_empty(self, module):
        doc = yaml.safe_load(module.DOCUMENTATION)
        assert len(doc["short_description"]) > 10
