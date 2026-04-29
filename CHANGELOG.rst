============================
StorMagic Collection Release Notes
============================

.. contents:: Topics

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
