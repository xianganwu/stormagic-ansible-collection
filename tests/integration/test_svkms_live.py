from __future__ import absolute_import, division, print_function

import pytest

from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


class TestHealth:
    def test_health_check(self, svkms_client):
        result = svkms_client.health_check()
        assert result["status"] == "healthy"
        assert result["version"] == "4.2.0"


class TestAuth:
    def test_login_returns_token(self, svkms_client):
        client = SvKMSClient(
            host="localhost", port=1443,
            username="admin", password="admin",
            validate_certs=False,
        )
        token = client.login()
        assert token is not None
        assert len(token) > 0

    def test_authenticated_request_after_login(self, svkms_client):
        client = SvKMSClient(
            host="localhost", port=1443,
            username="admin", password="admin",
            validate_certs=False,
        )
        client.login()
        result = client.list_keys()
        assert isinstance(result, list)

    def test_logout_clears_token(self, svkms_client):
        client = SvKMSClient(
            host="localhost", port=1443,
            username="admin", password="admin",
            validate_certs=False,
        )
        client.login()
        client.logout()
        assert client._session_token is None

    def test_api_key_auth(self, svkms_client):
        client = SvKMSClient(
            host="localhost", port=1443,
            api_key="test-api-key",
            validate_certs=False,
        )
        result = client.health_check()
        assert result["status"] == "healthy"

    def test_invalid_login_raises(self, svkms_client):
        client = SvKMSClient(
            host="localhost", port=1443,
            username="admin", password="wrong",
            validate_certs=False,
        )
        with pytest.raises(SvKMSAPIError) as exc_info:
            client.login()
        assert exc_info.value.status_code == 401

    def test_unauthenticated_request_returns_401(self, svkms_client):
        client = SvKMSClient(
            host="localhost", port=1443,
            validate_certs=False,
        )
        with pytest.raises(SvKMSAPIError) as exc_info:
            client.list_keys()
        assert exc_info.value.status_code == 401


class TestKeyLifecycle:
    def test_create_key(self, svkms_client):
        result = svkms_client.create_key(name="lifecycle-key", algorithm="AES", length=256)
        assert result["name"] == "lifecycle-key"
        assert result["algorithm"] == "AES"
        assert result["length"] == 256
        assert result["version"] == 1
        assert result["state"] == "active"
        assert "id" in result

    def test_list_keys_contains_created(self, svkms_client):
        keys = svkms_client.list_keys()
        names = [k["name"] for k in keys]
        assert "lifecycle-key" in names

    def test_get_key_by_id(self, svkms_client):
        keys = svkms_client.list_keys()
        key = next(k for k in keys if k["name"] == "lifecycle-key")
        fetched = svkms_client.get_key(key["id"])
        assert fetched["name"] == "lifecycle-key"
        assert fetched["id"] == key["id"]

    def test_duplicate_create_returns_409(self, svkms_client):
        with pytest.raises(SvKMSAPIError) as exc_info:
            svkms_client.create_key(name="lifecycle-key", algorithm="AES", length=256)
        assert exc_info.value.status_code == 409

    def test_rotate_key(self, svkms_client):
        keys = svkms_client.list_keys()
        key = next(k for k in keys if k["name"] == "lifecycle-key")
        rotated = svkms_client.rotate_key(key["id"])
        assert rotated["version"] == 2

    def test_rotate_again(self, svkms_client):
        keys = svkms_client.list_keys()
        key = next(k for k in keys if k["name"] == "lifecycle-key")
        rotated = svkms_client.rotate_key(key["id"])
        assert rotated["version"] == 3

    def test_retire_key(self, svkms_client):
        keys = svkms_client.list_keys()
        key = next(k for k in keys if k["name"] == "lifecycle-key")
        retired = svkms_client.retire_key(key["id"])
        assert retired["state"] == "retired"

    def test_destroy_key(self, svkms_client):
        keys = svkms_client.list_keys()
        key = next(k for k in keys if k["name"] == "lifecycle-key")
        svkms_client.destroy_key(key["id"])
        with pytest.raises(SvKMSAPIError) as exc_info:
            svkms_client.get_key(key["id"])
        assert exc_info.value.status_code == 404

    def test_get_nonexistent_key(self, svkms_client):
        with pytest.raises(SvKMSAPIError) as exc_info:
            svkms_client.get_key("nonexistent-id")
        assert exc_info.value.status_code == 404

    def test_destroy_nonexistent_key(self, svkms_client):
        with pytest.raises(SvKMSAPIError) as exc_info:
            svkms_client.destroy_key("nonexistent-id")
        assert exc_info.value.status_code == 404


class TestKeyFiltering:
    def test_filter_by_name(self, svkms_client):
        svkms_client.create_key(name="filter-aaa", algorithm="AES", length=128)
        svkms_client.create_key(name="filter-bbb", algorithm="RSA", length=2048)

        filtered = svkms_client.list_keys(filters={"name": "filter-aaa"})
        assert len(filtered) == 1
        assert filtered[0]["name"] == "filter-aaa"

        # Cleanup
        for k in svkms_client.list_keys():
            if k["name"].startswith("filter-"):
                svkms_client.destroy_key(k["id"])

    def test_create_key_with_metadata(self, svkms_client):
        result = svkms_client.create_key(
            name="meta-key", algorithm="EC", length=384,
            metadata={"env": "prod", "owner": "team-a"},
        )
        assert result["metadata"]["env"] == "prod"
        svkms_client.destroy_key(result["id"])


class TestUserLifecycle:
    def test_create_user(self, svkms_client):
        result = svkms_client.create_user(
            username="test-operator", role="operator", auth_type="password",
        )
        assert result["username"] == "test-operator"
        assert result["role"] == "operator"
        assert "id" in result

    def test_list_users(self, svkms_client):
        users = svkms_client.list_users()
        usernames = [u["username"] for u in users]
        assert "test-operator" in usernames

    def test_get_user(self, svkms_client):
        users = svkms_client.list_users()
        user = next(u for u in users if u["username"] == "test-operator")
        fetched = svkms_client.get_user(user["id"])
        assert fetched["username"] == "test-operator"

    def test_duplicate_user_returns_409(self, svkms_client):
        with pytest.raises(SvKMSAPIError) as exc_info:
            svkms_client.create_user(username="test-operator", role="admin")
        assert exc_info.value.status_code == 409

    def test_delete_user(self, svkms_client):
        users = svkms_client.list_users()
        user = next(u for u in users if u["username"] == "test-operator")
        svkms_client.delete_user(user["id"])
        with pytest.raises(SvKMSAPIError) as exc_info:
            svkms_client.get_user(user["id"])
        assert exc_info.value.status_code == 404

    def test_delete_nonexistent_user(self, svkms_client):
        with pytest.raises(SvKMSAPIError) as exc_info:
            svkms_client.delete_user("nonexistent-id")
        assert exc_info.value.status_code == 404


class TestPolicyLifecycle:
    def test_create_policy(self, svkms_client):
        rules = [{"principal": "app-user", "actions": ["encrypt"], "resources": ["*"]}]
        result = svkms_client.create_policy(name="test-policy", rules=rules)
        assert result["name"] == "test-policy"
        assert len(result["rules"]) == 1
        assert "id" in result

    def test_list_policies(self, svkms_client):
        policies = svkms_client.list_policies()
        names = [p["name"] for p in policies]
        assert "test-policy" in names

    def test_get_policy(self, svkms_client):
        policies = svkms_client.list_policies()
        policy = next(p for p in policies if p["name"] == "test-policy")
        fetched = svkms_client.get_policy(policy["id"])
        assert fetched["name"] == "test-policy"

    def test_duplicate_policy_returns_409(self, svkms_client):
        with pytest.raises(SvKMSAPIError) as exc_info:
            svkms_client.create_policy(name="test-policy", rules=[])
        assert exc_info.value.status_code == 409

    def test_delete_policy(self, svkms_client):
        policies = svkms_client.list_policies()
        policy = next(p for p in policies if p["name"] == "test-policy")
        svkms_client.delete_policy(policy["id"])
        with pytest.raises(SvKMSAPIError) as exc_info:
            svkms_client.get_policy(policy["id"])
        assert exc_info.value.status_code == 404


class TestCertificates:
    def test_list_certificates(self, svkms_client):
        certs = svkms_client.list_certificates()
        assert isinstance(certs, list)
        assert len(certs) >= 1

    def test_get_certificate(self, svkms_client):
        certs = svkms_client.list_certificates()
        cert = certs[0]
        fetched = svkms_client.get_certificate(cert["id"])
        assert fetched["id"] == cert["id"]
        assert fetched["type"] == "ca"
        assert "subject" in fetched

    def test_get_nonexistent_cert(self, svkms_client):
        with pytest.raises(SvKMSAPIError) as exc_info:
            svkms_client.get_certificate("nonexistent")
        assert exc_info.value.status_code == 404


class TestBackupRestore:
    def test_backup(self, svkms_client):
        result = svkms_client.backup(destination="/tmp/backup.tar.gz")
        assert result["status"] == "success"
        assert "backup_id" in result

    def test_restore(self, svkms_client):
        result = svkms_client.restore(source="/tmp/backup.tar.gz")
        assert result["status"] == "success"
        assert "restore_id" in result


class TestIdempotencyPatterns:
    def test_key_create_idempotency(self, svkms_client):
        svkms_client.create_key(name="idemp-key", algorithm="AES", length=256)
        keys = svkms_client.list_keys()
        existing = next((k for k in keys if k["name"] == "idemp-key"), None)
        assert existing is not None
        svkms_client.destroy_key(existing["id"])

    def test_key_delete_idempotency(self, svkms_client):
        keys = svkms_client.list_keys()
        existing = next((k for k in keys if k["name"] == "ghost-key"), None)
        assert existing is None

    def test_user_full_cycle(self, svkms_client):
        user = svkms_client.create_user(username="cycle-user", role="auditor")
        users = svkms_client.list_users()
        found = next((u for u in users if u["username"] == "cycle-user"), None)
        assert found is not None
        svkms_client.delete_user(found["id"])
        users = svkms_client.list_users()
        found = next((u for u in users if u["username"] == "cycle-user"), None)
        assert found is None

    def test_policy_full_cycle(self, svkms_client):
        policy = svkms_client.create_policy(name="cycle-policy", rules=[])
        policies = svkms_client.list_policies()
        found = next((p for p in policies if p["name"] == "cycle-policy"), None)
        assert found is not None
        svkms_client.delete_policy(found["id"])
        policies = svkms_client.list_policies()
        found = next((p for p in policies if p["name"] == "cycle-policy"), None)
        assert found is None
