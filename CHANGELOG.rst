============================
StorMagic Collection Release Notes
============================

.. contents:: Topics

v1.0.0
======

Release Summary
---------------
Initial release of the StorMagic Ansible collection.

New Modules
-----------
- stormagic.stormagic.svkms_key - Manage encryption keys on SvKMS
- stormagic.stormagic.svkms_key_info - Gather key information from SvKMS
- stormagic.stormagic.svkms_health_check - Check SvKMS server health
- stormagic.stormagic.svkms_certificate - Manage certificates on SvKMS
- stormagic.stormagic.svkms_user - Manage users on SvKMS
- stormagic.stormagic.svkms_policy - Manage key access policies on SvKMS
- stormagic.stormagic.svkms_backup - Backup and restore SvKMS
- stormagic.stormagic.svsan_health_check - Run health checks on SvSAN VSA
- stormagic.stormagic.svsan_target - Manage iSCSI targets on SvSAN
- stormagic.stormagic.svsan_target_info - Gather target info from SvSAN
- stormagic.stormagic.svsan_mirror - Manage mirrored storage on SvSAN
- stormagic.stormagic.svsan_mirror_info - Gather mirror status from SvSAN
- stormagic.stormagic.svsan_pool - Manage storage pools on SvSAN
- stormagic.stormagic.svsan_pool_info - Gather pool info from SvSAN
- stormagic.stormagic.svsan_license - Manage SvSAN licenses
- stormagic.stormagic.svsan_config - Manage VSA configuration
- stormagic.stormagic.svsan_config_info - Gather VSA configuration
- stormagic.stormagic.svsan_vsa - Deploy VSA instances

New Roles
---------
- stormagic.stormagic.svsan_patching_preflight - Pre-patching health gate
- stormagic.stormagic.svsan_patching_postflight - Post-patching verification
- stormagic.stormagic.svsan_deploy - Deploy SvSAN VSA pair
- stormagic.stormagic.svkms_setup - Initial SvKMS configuration

New Plugins
-----------
- httpapi: stormagic.stormagic.svkms - HttpApi plugin for SvKMS REST API
