============================
StorMagic Collection Release Notes
============================

.. contents:: Topics

v1.3.0
======

Release Summary
---------------
Breaking parameter rename, documentation accuracy overhaul, and security
hardening for role secrets.

Breaking Changes
----------------
- Renamed ``svkms_user`` module parameter ``username`` to ``name`` to eliminate
  collision with the authentication ``username`` from ``svkms_argument_spec()``.
  The previous parameter made both API key and username/password authentication
  unusable. Update all playbooks and roles that use ``svkms_user`` to use
  ``name`` instead of ``username``.

Bugfixes
--------
- Fixed ``.ansible/`` directory (stale nested collection copies) leaking into
  collection tarball, inflating it from ~650 files to ~120 files. Added
  ``.ansible`` to ``build_ignore`` and ``.gitignore``.
- Fixed ``svsan_license`` RETURN documentation claiming ``license_applied: bool``
  when the module actually returns ``license: dict`` with ``Key`` and ``IsValid``
  fields.
- Fixed ``docs/svsan_quickstart.md`` using non-existent ``sync_status`` and
  ``out_of_sync_mb`` mirror fields — corrected to ``sync_pct`` matching
  ``svsan_mirror_info`` RETURN documentation.
- Fixed ``docs/svsan_quickstart.md`` referencing non-existent
  ``pool_capacity_critical_pct`` parameter on ``svsan_health_check`` module.
- Fixed role READMEs documenting phantom variables and omitting required
  parameters — rewrote ``svkms_setup``, ``svkms_key_rotation``, and
  ``svsan_deploy`` READMEs from ``argument_specs.yml`` source of truth.

Minor Changes
-------------
- Added ``svsan_esxi_preflight`` to module table in ``README.md``.
- Added ``no_log: true`` to ``svkms_key_rotation_api_key`` and
  ``svkms_setup_api_key`` in role ``argument_specs.yml`` to prevent credential
  leakage in verbose output.
- Added ``block/rescue/always`` error handling to all 5 roles for graceful
  failure reporting with remediation guidance.
- Added tags to ``svkms_setup``, ``svkms_key_rotation``, and ``svsan_deploy``
  roles for selective task execution.
- Added ``seealso`` cross-references to all 19 module DOCUMENTATION strings.
- Verified ``no_log: true`` is present on all sensitive parameters in
  argument_specs across SvKMS and SvSAN modules.
- Added 30-second connection timeout to ``SvKMSClient`` API requests.
- Added URL encoding to all path parameters and filter query values in
  ``SvKMSClient``.
- Removed empty-string default values for password parameters in
  ``svsan_deploy`` and ``svsan_patching_preflight`` role defaults.

v1.2.6
======

Release Summary
---------------
Comprehensive audit fixes for Red Hat certification readiness.

Bugfixes
--------
- Fixed ``svkms_user`` missing ``username`` parameter in SvKMSClient
  initialization — username/password authentication was completely broken.
- Fixed ``svkms_certificate`` silent exception swallowing during cert_id lookup.
- Fixed ``svkms_backup`` check mode results missing ``status`` field.
- Fixed ``svsan_pool`` incorrect ``Diff.before`` when deleting.
- Fixed diff-mode output in ``svsan_target``, ``svsan_mirror``, ``svsan_pool``,
  and ``svsan_config`` for consistent ``--diff`` output.
- Fixed ``svkms_setup`` role default policies using invalid fields.
- Fixed ``README.md`` role example using wrong variable names.
- Fixed ``docs/svkms_quickstart.md`` using invalid algorithm value.

Minor Changes
-------------
- Added copyright header to ``svsan.py`` doc fragment.
- Added ``.DS_Store`` and ``.pytest_cache`` to ``galaxy.yml`` build_ignore.

v1.2.5
======

Release Summary
---------------
Certification and best-practices audit fixes. Removes dead httpapi plugin,
adds direct API key authentication, fixes session leaks, and improves
idempotency.

Breaking Changes
----------------
- Removed the ``svkms`` httpapi connection plugin. All SvKMS modules now
  connect directly to the REST API using ``host`` and ``api_key`` (or
  ``username``/``password``) parameters.

Bugfixes
--------
- Fixed session leak in all 11 SvSAN PowerShell modules.
- Fixed session leak in ``svsan_esxi_preflight``.
- Fixed ``svkms_user`` idempotency — now compares role and auth_type.
- Fixed ``svkms_policy`` idempotency — now compares rules.
- Fixed ``svkms_certificate`` substring matching — now uses exact match.
- Fixed ``svsan_license`` idempotency — compares before/after license state.
- Fixed ``svsan_vsa`` idempotency — checks for existing VSA before deploying.
- Fixed ``svkms_key`` not passing ``metadata`` to ``create_key``.
- Fixed credential leak — ``SvKMSClient`` now clears password after login.
- Removed non-functional ``state: absent`` from ``svsan_vsa`` and
  ``svkms_certificate``.
- Removed unused ``mirror`` parameter from ``svsan_target``.
- Removed unused ``cert_type`` parameter from ``svkms_certificate``.
- Fixed ``svsan_health_check`` check mode calling ``FailJson`` on fail status.

Minor Changes
-------------
- Added ``api_key``, ``username``, and ``password`` authentication parameters.
- Added ``client.login()``/``client.logout()`` session lifecycle.
- Added ``Disconnect-SmSession`` function to ``SvSAN.psm1``.
- Added ``update_user`` and ``update_policy`` methods to ``SvKMSClient``.
- Added tags to patching roles and workflow playbook.
- Cleaned unused variables from ``svkms_setup`` role defaults.

v1.2.0
======

Release Summary
---------------
Sheetz-informed patching workflow improvements. New ESXi preflight module,
mirror resync wait, health baseline comparison, and production-ready
patching playbook.

Minor Changes
-------------
- Added ``svsan_esxi_preflight`` module for pre-patching ESXi checks via
  vCenter.
- Added mirror resync polling to ``svsan_patching_postflight`` role.
- Added ``set_fact`` output variables to both patching roles.
- Added pre/post health comparison to ``svsan_patching_postflight`` role.
- Integrated optional ESXi preflight checks into ``svsan_patching_preflight``
  role.
- Rewrote ``svsan_patching_workflow.yml`` playbook with complete ESXi
  patching workflow.
- Rewrote ``docs/patching_workflow.md`` with correct variable names.
- Added ``pyvmomi>=8.0.0`` to EE requirements.

New Modules
-----------
- xianganwu.stormagic.svsan_esxi_preflight - Pre-patching checks for ESXi
  hosts via vCenter

v1.1.3
======

Release Summary
---------------
Make SvKMS host parameter optional for httpapi connection compatibility.

Bugfixes
--------
- Changed ``host`` from required to optional in all SvKMS module argument_specs.
  When using httpapi connection, host is provided by inventory; modules now fail
  with a clear message if host is missing outside httpapi context.

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
