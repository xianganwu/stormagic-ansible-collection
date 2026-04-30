==========================================
StorMagic Ansible Collection Release Notes
==========================================

.. contents:: Topics

v1.3.1
======

Minor Changes
-------------

- svkms_key - add ansible-test integration target with full lifecycle tests against mock server (https://github.com/xianganwu/stormagic-ansible-collection/pull/1).

v1.3.0
======

Release Summary
---------------

Breaking parameter rename, documentation accuracy overhaul, and security hardening for role secrets.

Minor Changes
-------------

- Added 30-second connection timeout to ``SvKMSClient`` API requests to prevent indefinite hangs on network issues.
- Added URL encoding to all path parameters and filter query values in ``SvKMSClient`` to handle special characters safely.
- Added ``block/rescue/always`` error handling to all 5 roles — ``svkms_setup``, ``svkms_key_rotation``, ``svsan_deploy``, ``svsan_patching_preflight``, and ``svsan_patching_postflight``. Roles now report which task failed and propagate the error with remediation guidance instead of abrupt failure.
- Added ``no_log: true`` to ``svkms_key_rotation_api_key`` and ``svkms_setup_api_key`` in role ``argument_specs.yml`` to prevent credential leakage in verbose output.
- Added ``seealso`` cross-references to all 19 module DOCUMENTATION strings, linking related modules within the collection for improved discoverability via ``ansible-doc``.
- Added ``svsan_esxi_preflight`` to module table in ``README.md``.
- Added tags to ``svkms_setup`` (``svkms_setup``), ``svkms_key_rotation`` (``svkms_key_rotation``), and ``svsan_deploy`` (``svsan_deploy``, ``svsan_deploy_provision``, ``svsan_deploy_configure``) roles for selective task execution.
- Removed empty-string default values for password parameters in ``svsan_deploy`` (``svsan_deploy_vcenter_password``, ``svsan_deploy_admin_password``) and ``svsan_patching_preflight`` (``svsan_patching_preflight_vcenter_password``) role defaults — these are required parameters and empty defaults are misleading.
- Verified ``no_log: true`` is present on all sensitive parameters in argument_specs — ``api_key`` and ``password`` in SvKMS ``svkms_argument_spec()``, ``vsa_password`` in all SvSAN PowerShell modules, and ``vcenter_password`` in ``svsan_esxi_preflight``.

Breaking Changes / Porting Guide
--------------------------------

- Renamed ``svkms_user`` module parameter ``username`` to ``name`` to eliminate collision with the authentication ``username`` from ``svkms_argument_spec()``. The previous parameter made both API key and username/password authentication unusable. Update all playbooks and roles that use ``svkms_user`` to use ``name`` instead of ``username``.

Bugfixes
--------

- Fixed ``.ansible/`` directory (stale nested collection copies) leaking into collection tarball, inflating it from ~650 files to ~120 files. Added ``.ansible`` to ``build_ignore`` and ``.gitignore``.
- Fixed ``docs/svsan_quickstart.md`` referencing non-existent ``pool_capacity_critical_pct`` parameter on ``svsan_health_check`` module.
- Fixed ``docs/svsan_quickstart.md`` using non-existent ``sync_status`` and ``out_of_sync_mb`` mirror fields — corrected to ``sync_pct`` matching ``svsan_mirror_info`` RETURN documentation.
- Fixed ``svsan_license`` RETURN documentation claiming ``license_applied: bool`` when the module actually returns ``license: dict`` with ``Key`` and ``IsValid`` fields.
- Fixed role READMEs documenting phantom variables and omitting required parameters — rewrote ``svkms_setup``, ``svkms_key_rotation``, and ``svsan_deploy`` READMEs from ``argument_specs.yml`` source of truth.

v1.2.6
======

Release Summary
---------------

Comprehensive audit fixes for Red Hat certification readiness. Fixes critical authentication bug, diff-mode consistency, documentation accuracy, and role configuration correctness.

Minor Changes
-------------

- Added ``.DS_Store`` and ``.pytest_cache`` to ``galaxy.yml`` build_ignore to prevent build artifacts from entering the collection tarball.
- Added copyright header to ``svsan.py`` doc fragment for Red Hat certification compliance.

Bugfixes
--------

- Fixed ``README.md`` role example using wrong variable names (``svsan_vsa_hostname`` instead of ``svsan_patching_preflight_vsa_hostname``).
- Fixed ``docs/svkms_quickstart.md`` using invalid algorithm value ``AES256`` — corrected to ``algorithm: AES`` with ``length: 256``.
- Fixed ``svkms_backup`` check mode results missing ``status`` field documented in RETURN section.
- Fixed ``svkms_certificate`` silent exception swallowing during cert_id lookup — now only catches 404 (not found) and re-raises other API errors (auth failures, server errors).
- Fixed ``svkms_setup`` role default policies using invalid ``rotation_days``/``key_algorithm`` fields — replaced with correct ``rules`` format accepted by ``svkms_policy`` module.
- Fixed ``svkms_user`` missing ``username`` parameter in SvKMSClient initialization — username/password authentication was completely broken for this module.
- Fixed ``svsan_pool`` incorrect ``Diff.before`` when deleting — was set to empty hash instead of the existing pool state.
- Fixed diff-mode output in ``svsan_target``, ``svsan_mirror``, ``svsan_pool``, and ``svsan_config`` — now set ``Diff.before`` and ``Diff.after`` in all idempotent (no-change) paths for consistent ``--diff`` output.

v1.2.5
======

Release Summary
---------------

Certification and best-practices audit fixes. Removes dead httpapi plugin, adds direct API key authentication, fixes session leaks, improves idempotency, and cleans up unused parameters.

Minor Changes
-------------

- Added ``Disconnect-SmSession`` function to ``SvSAN.psm1`` module utility and ``Remove-SmSession`` mock for Pester testing.
- Added ``Get-SmVcVSA`` function to SvSAN mock for VSA existence checks in Pester tests.
- Added ``api_key``, ``username``, and ``password`` authentication parameters to all SvKMS modules for direct REST API connection.
- Added ``client.login()``/``client.logout()`` session lifecycle to all SvKMS modules, enabling username/password authentication and proper session cleanup via ``try/finally`` blocks.
- Added ``host`` and ``api_key`` test values to ``svkms_key_rotation`` molecule converge for proper CI validation.
- Added ``update_user`` and ``update_policy`` methods to ``SvKMSClient`` for proper idempotent updates.
- Added tags to patching roles and workflow playbook for selective task execution (``svsan_preflight``, ``svsan_postflight``, ``svsan_maintenance``, ``svsan_patch``, ``svsan_reboot``).
- Cleaned unused variables from ``svkms_setup`` role defaults and argument_specs (``svkms_setup_admin_password``, ``svkms_setup_admin_email``, ``svkms_setup_ca_organization``, ``svkms_setup_ca_validity_days``).
- Removed empty-string defaults for required ``host`` and ``api_key`` parameters from ``svkms_key_rotation`` and ``svkms_setup`` role defaults — these are validated via ``argument_specs`` as required.

Breaking Changes / Porting Guide
--------------------------------

- Removed the ``svkms`` httpapi connection plugin. All SvKMS modules now connect directly to the REST API using ``host`` and ``api_key`` (or ``username``/``password``) parameters. Playbooks using ``connection: ansible.netcommon.httpapi`` must be updated.

Bugfixes
--------

- Fixed ``svkms_certificate`` substring matching — ``find_certificate_by_name`` now uses exact match on ``name`` field with CN extraction fallback instead of substring search on ``subject``.
- Fixed ``svkms_key`` not passing ``metadata`` parameter to ``create_key`` API call.
- Fixed ``svkms_policy`` idempotency — module now compares ``rules`` against existing policy and calls ``update_policy`` when different.
- Fixed ``svkms_user`` idempotency — module now compares ``role`` and ``auth_type`` against existing user and calls ``update_user`` when different instead of silently skipping.
- Fixed ``svsan_health_check`` check mode — no longer calls ``FailJson`` when health status is ``fail`` during check mode.
- Fixed ``svsan_license`` idempotency — module now compares license state before and after applying, correctly reporting ``changed`` only when the license actually changed. Check mode runs before any mutation.
- Fixed ``svsan_vsa`` idempotency — module now checks for existing VSA by name via ``Get-SmVcVSA`` before deploying, returning ``changed: false`` if already deployed.
- Fixed credential leak — ``SvKMSClient`` now clears the password from memory after successful login.
- Fixed session leak in ``svsan_esxi_preflight`` — ``Disconnect-VIServer`` moved from ``try`` to ``finally`` block.
- Fixed session leak in all 11 SvSAN PowerShell modules — sessions are now properly disconnected via ``try/finally`` blocks.
- Removed non-functional ``state: absent`` from ``svsan_vsa`` and ``svkms_certificate`` modules (API does not support deletion).
- Removed unused ``cert_type`` parameter from ``svkms_certificate`` module and roles.
- Removed unused ``mirror`` parameter from ``svsan_target`` module (mirroring is managed via ``svsan_mirror``).

v1.2.0
======

Release Summary
---------------

Sheetz-informed patching workflow improvements. New ESXi preflight module, mirror resync wait, health baseline comparison, and production-ready patching playbook.

Minor Changes
-------------

- Added Molecule test scaffolding for ``svsan_patching_preflight`` and ``svsan_patching_postflight`` roles.
- Added ``pyvmomi>=8.0.0`` to EE requirements for ``vmware.vmware`` dependency compatibility.
- Added ``set_fact`` output variables to both patching roles: ``svsan_patching_preflight_status``, ``svsan_patching_preflight_baseline``, and ``svsan_patching_postflight_status`` for workflow conditional logic.
- Added ``svsan_esxi_preflight`` module for pre-patching ESXi checks via vCenter — retrieves active alerts, build number, version, and maintenance mode status using PowerCLI.
- Added mirror resync polling to ``svsan_patching_postflight`` role — waits for mirrors to resynchronize after ESXi reboot before running health checks (configurable retries/delay).
- Added pre/post health comparison to ``svsan_patching_postflight`` role — detects health degradation by comparing against preflight baseline.
- Integrated optional ESXi preflight checks into ``svsan_patching_preflight`` role via ``svsan_patching_preflight_check_esxi`` toggle (default false).
- Rewrote ``docs/patching_workflow.md`` with correct variable names, per-vCenter scale guidance, and WinRM concurrency tuning.
- Rewrote ``svsan_patching_workflow.yml`` playbook with complete ESXi patching workflow including ``serial`` batching, maintenance mode via ``vmware.vmware.esxi_maintenance_mode``, and pre/post health gates.

New Modules
-----------

- svsan_esxi_preflight - Pre-patching checks for ESXi hosts via vCenter

v1.1.3
======

Release Summary
---------------

Make SvKMS host parameter optional for httpapi connection compatibility.

Bugfixes
--------

- Changed ``host`` from required to optional in all SvKMS module argument_specs. When using httpapi connection, host is provided by inventory; modules now fail with a clear message if host is missing outside httpapi context. Fixes ansible-lint args[module] warnings in roles and playbooks.

v1.1.2
======

Release Summary
---------------

Fix sanity test and ansible-lint failures across all ansible-core versions.

Minor Changes
-------------

- Added EXAMPLES block to SvKMS httpapi plugin.
- Added copyright header to ``module_utils/svkms_api.py``.

Bugfixes
--------

- Added ``host`` and ``port`` to argument_spec in all SvKMS modules to match the doc fragment DOCUMENTATION, fixing ``nonexistent-parameter-documented`` sanity errors.
- Added missing ``datacenter`` parameter to ``vmware.vmware.vm_powerstate`` task in ``svsan_deploy`` role, fixing ansible-lint ``args[module]`` warning.
- Removed ``no_log: true`` from ``vsa_password`` in the SvSAN doc fragment DOCUMENTATION block — ``no_log`` is only valid in argument_spec (already present in the PowerShell modules), not in YAML documentation.

v1.1.1
======

Release Summary
---------------

Bug fixes, security hardening, and CI/testing improvements.

Minor Changes
-------------

- Added Molecule test scaffolding for ``svkms_key_rotation`` and ``svsan_deploy`` roles.
- Added ``no_log: true`` to ``vsa_password`` in SvSAN doc fragment to prevent credential leakage in verbose output.
- Added sanity ignore files for ansible-core 2.18, 2.19, and 2.20.
- Expanded CI sanity test matrix to include ansible-core 2.18 through 2.20.
- Removed unused ``module_utils/common.py`` dead code.

Bugfixes
--------

- Added missing v1.0.1 entry to changelog.
- Fixed ``svkms_health_check`` module not failing when API returns unhealthy status (only failed on connection errors).
- Fixed ``svsan_deploy`` role passing invalid ``node_id`` parameter to ``svsan_vsa`` module and invalid ``size_gb`` parameter to ``svsan_pool`` module.
- Fixed ``svsan_ha_setup`` playbook using non-existent ``mirror_enabled`` and ``mirror_node`` parameters on ``svsan_target`` module.
- Fixed copyright year inconsistency in SvKMS doc fragment.

v1.1.0
======

Release Summary
---------------

Certification readiness improvements and new end-user features.

Minor Changes
-------------

- Added 2-3 examples per module covering check mode and register+assert patterns.
- Added ``action_groups`` to ``meta/runtime.yml`` for ``module_defaults`` grouping.
- Added ``argument_specs.yml`` for all roles enabling ``ansible-doc --type role`` rendering.
- Added ``meta/execution-environment.yml`` for Ansible Automation Platform EE builds.
- Added partner-certification-checker job to CI workflow.
- Expanded RETURN documentation with ``contains:`` nesting for all SvKMS modules.
- Improved README with dependency table, Red Hat certified support language, and full URLs.

New Roles
---------

- svkms_key_rotation - Rotate encryption keys on SvKMS

v1.0.3
======

Release Summary
---------------

Migrated VMware dependency from community collection to Red Hat certified collection.

Breaking Changes / Porting Guide
--------------------------------

- ESXi maintenance mode in patching workflow now uses ``vmware.vmware.esxi_maintenance_mode`` which connects through vCenter.
- New role variables required for guest customization - ``svsan_deploy_domain``, ``svsan_deploy_netmask``, ``svsan_deploy_gateway``, ``svsan_deploy_dns_servers``.
- Replaced ``community.vmware`` dependency with ``vmware.vmware`` (>= 2.0.0), the Red Hat certified VMware collection.
- The ``svsan_deploy`` role now uses a multi-step workflow with ``vmware.vmware.deploy_folder_template``, ``vmware.vmware.vm``, ``vmware.vmware.vm_apply_customization``, and ``vmware.vmware.vm_powerstate`` instead of a single ``community.vmware.vmware_guest`` call.

v1.0.2
======

Release Summary
---------------

Bug fixes and quality-of-life improvements for SvKMS and SvSAN modules.

Minor Changes
-------------

- Added ``validate_certs`` and ``ca_path`` parameters to all SvKMS modules for TLS certificate validation control.
- Added automatic retry with exponential backoff to SvKMS API client (retries on 5xx, 429, and connection errors; no retry on 4xx client errors).
- Added diff mode support (``--diff``) to all state-changing SvKMS and SvSAN modules for before/after change visibility.
- Added retry with exponential backoff to SvSAN ``Connect-SmVsa`` helper.
- Improved error messages in all modules.

Bugfixes
--------

- Fixed broken ``#AnsibleRequires`` namespace in all SvSAN PowerShell modules (``stormagic.stormagic`` to ``xianganwu.stormagic``).
- Fixed namespace references in README, quickstart guides, and patching workflow docs.

v1.0.1
======

Release Summary
---------------

Namespace correction for Ansible Galaxy publishing.

Bugfixes
--------

- Changed collection namespace from ``stormagic`` to ``xianganwu`` for Ansible Galaxy compatibility.

v1.0.0
======

Release Summary
---------------

Initial release of the StorMagic Ansible collection for managing SvKMS encryption key management and SvSAN virtual storage appliances.

Major Changes
-------------

- Eleven SvSAN PowerShell modules for target, pool, mirror, config, license, health check, and VSA deployment management.
- Four roles for SvKMS setup, SvSAN deployment, and patching workflows.
- Seven SvKMS modules for key, user, policy, certificate, health check, and backup/restore management.
- SvKMS httpapi plugin for REST API connectivity.

New Plugins
-----------

Httpapi
~~~~~~~

- svkms - HttpApi plugin for SvKMS REST API

New Modules
-----------

- svkms_backup - Backup and restore SvKMS
- svkms_certificate - Manage certificates on SvKMS
- svkms_health_check - Check SvKMS server health
- svkms_key - Manage encryption keys on SvKMS
- svkms_key_info - Gather key information from SvKMS
- svkms_policy - Manage key access policies on SvKMS
- svkms_user - Manage users on SvKMS
- svsan_config - Manage VSA configuration
- svsan_config_info - Gather VSA configuration
- svsan_health_check - Run health checks on SvSAN VSA
- svsan_license - Manage SvSAN licenses
- svsan_mirror - Manage mirrored storage on SvSAN
- svsan_mirror_info - Gather mirror status from SvSAN
- svsan_pool - Manage storage pools on SvSAN
- svsan_pool_info - Gather pool info from SvSAN
- svsan_target - Manage iSCSI targets on SvSAN
- svsan_target_info - Gather target info from SvSAN
- svsan_vsa - Deploy VSA instances
