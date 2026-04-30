============================
StorMagic Collection Release Notes
============================

.. contents:: Topics

v1.1.2
======

Release Summary
---------------
Fix sanity test and ansible-lint failures across all ansible-core versions.

Bugfixes
--------
- Added ``host`` and ``port`` to argument_spec in all SvKMS modules to match the
  doc fragment DOCUMENTATION, fixing ``nonexistent-parameter-documented`` sanity errors.
- Removed ``no_log: true`` from ``vsa_password`` in the SvSAN doc fragment DOCUMENTATION
  block — ``no_log`` is only valid in argument_spec (already present in the PowerShell
  modules), not in YAML documentation.
- Added missing ``datacenter`` parameter to ``vmware.vmware.vm_powerstate`` task in
  ``svsan_deploy`` role, fixing ansible-lint ``args[module]`` warning.

Minor Changes
-------------
- Added EXAMPLES block to SvKMS httpapi plugin.
- Added copyright header to ``module_utils/svkms_api.py``.

v1.1.0
======

Release Summary
---------------
Certification readiness improvements and new end-user features.

Minor Changes
-------------
- Added ``action_groups`` to ``meta/runtime.yml`` for ``module_defaults`` grouping.
- Expanded RETURN documentation with ``contains:`` nesting for all SvKMS modules.
- Added 2-3 examples per module covering check mode and register+assert patterns.
- Added ``argument_specs.yml`` for all roles enabling ``ansible-doc --type role`` rendering.
- Added ``meta/execution-environment.yml`` for Ansible Automation Platform EE builds.
- Added partner-certification-checker job to CI workflow.
- Improved README with dependency table, Red Hat certified support language, and full URLs.

New Roles
---------
- xianganwu.stormagic.svkms_key_rotation - Rotate encryption keys on SvKMS

v1.0.3
======

Release Summary
---------------
Migrated VMware dependency from community collection to Red Hat certified collection.

Breaking Changes
----------------
- Replaced ``community.vmware`` dependency with ``vmware.vmware`` (>= 2.0.0), the
  Red Hat certified VMware collection.
- The ``svsan_deploy`` role now uses a multi-step workflow with
  ``vmware.vmware.deploy_folder_template``, ``vmware.vmware.vm``,
  ``vmware.vmware.vm_apply_customization``, and ``vmware.vmware.vm_powerstate``
  instead of a single ``community.vmware.vmware_guest`` call.
- New role variables required for guest customization: ``svsan_deploy_domain``,
  ``svsan_deploy_netmask``, ``svsan_deploy_gateway``, ``svsan_deploy_dns_servers``.
- New optional variables: ``svsan_deploy_template_folder``,
  ``svsan_deploy_adapter_type``.
- ESXi maintenance mode in patching workflow now uses
  ``vmware.vmware.esxi_maintenance_mode`` which connects through vCenter
  (requires ``vcenter_hostname``, ``vcenter_username``, ``vcenter_password``
  inventory variables) instead of directly to ESXi hosts.

v1.0.2
======

Release Summary
---------------
Bug fixes and quality-of-life improvements for SvKMS and SvSAN modules.

Bugfixes
--------
- Fixed broken ``#AnsibleRequires`` namespace in all SvSAN PowerShell modules
  (``stormagic.stormagic`` → ``xianganwu.stormagic``).
- Fixed namespace references in README, quickstart guides, and patching workflow docs.

Minor Changes
-------------
- Added ``validate_certs`` and ``ca_path`` parameters to all SvKMS modules for
  TLS certificate validation control.
- Added automatic retry with exponential backoff to SvKMS API client (retries
  on 5xx, 429, and connection errors; no retry on 4xx client errors).
- Added retry with exponential backoff to SvSAN ``Connect-SmVsa`` helper.
- Improved error messages in all modules — SvKMS modules now include API
  response detail and status code; SvSAN modules include the VSA hostname.
- Added diff mode support (``--diff``) to all state-changing SvKMS and SvSAN
  modules for before/after change visibility.

v1.0.0
======

Release Summary
---------------
Initial release of the StorMagic Ansible collection.

New Modules
-----------
- xianganwu.stormagic.svkms_key - Manage encryption keys on SvKMS
- xianganwu.stormagic.svkms_key_info - Gather key information from SvKMS
- xianganwu.stormagic.svkms_health_check - Check SvKMS server health
- xianganwu.stormagic.svkms_certificate - Manage certificates on SvKMS
- xianganwu.stormagic.svkms_user - Manage users on SvKMS
- xianganwu.stormagic.svkms_policy - Manage key access policies on SvKMS
- xianganwu.stormagic.svkms_backup - Backup and restore SvKMS
- xianganwu.stormagic.svsan_health_check - Run health checks on SvSAN VSA
- xianganwu.stormagic.svsan_target - Manage iSCSI targets on SvSAN
- xianganwu.stormagic.svsan_target_info - Gather target info from SvSAN
- xianganwu.stormagic.svsan_mirror - Manage mirrored storage on SvSAN
- xianganwu.stormagic.svsan_mirror_info - Gather mirror status from SvSAN
- xianganwu.stormagic.svsan_pool - Manage storage pools on SvSAN
- xianganwu.stormagic.svsan_pool_info - Gather pool info from SvSAN
- xianganwu.stormagic.svsan_license - Manage SvSAN licenses
- xianganwu.stormagic.svsan_config - Manage VSA configuration
- xianganwu.stormagic.svsan_config_info - Gather VSA configuration
- xianganwu.stormagic.svsan_vsa - Deploy VSA instances

New Roles
---------
- xianganwu.stormagic.svsan_patching_preflight - Pre-patching health gate
- xianganwu.stormagic.svsan_patching_postflight - Post-patching verification
- xianganwu.stormagic.svsan_deploy - Deploy SvSAN VSA pair
- xianganwu.stormagic.svkms_setup - Initial SvKMS configuration

New Plugins
-----------
- httpapi: xianganwu.stormagic.svkms - HttpApi plugin for SvKMS REST API
