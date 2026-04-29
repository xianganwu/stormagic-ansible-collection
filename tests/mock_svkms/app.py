from __future__ import absolute_import, division, print_function

import os
import ssl
import subprocess
import uuid
from functools import wraps

from flask import Flask, request, jsonify

app = Flask(__name__)

KEYS = {}
USERS = {}
POLICIES = {}
CERTIFICATES = {}
TOKENS = {}
VALID_API_KEYS = {"test-api-key"}


def seed_data():
    cert_id = str(uuid.uuid4())
    CERTIFICATES[cert_id] = {
        "id": cert_id,
        "type": "ca",
        "subject": "CN=SvKMS Root CA",
        "issuer": "CN=SvKMS Root CA",
        "not_before": "2025-01-01T00:00:00Z",
        "not_after": "2030-01-01T00:00:00Z",
    }


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key in VALID_API_KEYS:
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if token in TOKENS:
                return f(*args, **kwargs)

        return jsonify({"error": "Unauthorized"}), 401
    return decorated


@app.route("/v0/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "version": "4.2.0"})


@app.route("/v0/auth/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")
    if username == "admin" and password == "admin":
        token = str(uuid.uuid4())
        TOKENS[token] = username
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/v0/auth/logout", methods=["POST"])
@require_auth
def logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        TOKENS.pop(token, None)
    return jsonify({})


# --- Keys ---

@app.route("/v0/keys", methods=["POST"])
@require_auth
def create_key():
    data = request.get_json(force=True)
    name = data.get("name")
    for key in KEYS.values():
        if key["name"] == name:
            return jsonify({"error": "Key '{0}' already exists".format(name)}), 409

    key_id = str(uuid.uuid4())
    key = {
        "id": key_id,
        "name": name,
        "algorithm": data.get("algorithm", "AES"),
        "length": data.get("length", 256),
        "version": 1,
        "state": "active",
    }
    if data.get("metadata"):
        key["metadata"] = data["metadata"]
    KEYS[key_id] = key
    return jsonify(key), 201


@app.route("/v0/keys", methods=["GET"])
@require_auth
def list_keys():
    keys = list(KEYS.values())
    for param, value in request.args.items():
        keys = [k for k in keys if str(k.get(param)) == value]
    return jsonify(keys)


@app.route("/v0/keys/<key_id>", methods=["GET"])
@require_auth
def get_key(key_id):
    key = KEYS.get(key_id)
    if not key:
        return jsonify({"error": "Key not found"}), 404
    return jsonify(key)


@app.route("/v0/keys/<key_id>/rotate", methods=["POST"])
@require_auth
def rotate_key(key_id):
    key = KEYS.get(key_id)
    if not key:
        return jsonify({"error": "Key not found"}), 404
    key["version"] += 1
    return jsonify(key)


@app.route("/v0/keys/<key_id>/retire", methods=["POST"])
@require_auth
def retire_key(key_id):
    key = KEYS.get(key_id)
    if not key:
        return jsonify({"error": "Key not found"}), 404
    key["state"] = "retired"
    return jsonify(key)


@app.route("/v0/keys/<key_id>", methods=["DELETE"])
@require_auth
def destroy_key(key_id):
    if key_id not in KEYS:
        return jsonify({"error": "Key not found"}), 404
    del KEYS[key_id]
    return jsonify({})


# --- Users ---

@app.route("/v0/users", methods=["POST"])
@require_auth
def create_user():
    data = request.get_json(force=True)
    username = data.get("username")
    for user in USERS.values():
        if user["username"] == username:
            return jsonify({"error": "User '{0}' already exists".format(username)}), 409

    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "username": username,
        "role": data.get("role", "operator"),
        "auth_type": data.get("auth_type", "password"),
    }
    USERS[user_id] = user
    return jsonify(user), 201


@app.route("/v0/users", methods=["GET"])
@require_auth
def list_users():
    return jsonify(list(USERS.values()))


@app.route("/v0/users/<user_id>", methods=["GET"])
@require_auth
def get_user(user_id):
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@app.route("/v0/users/<user_id>", methods=["DELETE"])
@require_auth
def delete_user(user_id):
    if user_id not in USERS:
        return jsonify({"error": "User not found"}), 404
    del USERS[user_id]
    return jsonify({})


# --- Policies ---

@app.route("/v0/policies", methods=["POST"])
@require_auth
def create_policy():
    data = request.get_json(force=True)
    name = data.get("name")
    for policy in POLICIES.values():
        if policy["name"] == name:
            return jsonify({"error": "Policy '{0}' already exists".format(name)}), 409

    policy_id = str(uuid.uuid4())
    policy = {
        "id": policy_id,
        "name": name,
        "rules": data.get("rules", []),
    }
    POLICIES[policy_id] = policy
    return jsonify(policy), 201


@app.route("/v0/policies", methods=["GET"])
@require_auth
def list_policies():
    return jsonify(list(POLICIES.values()))


@app.route("/v0/policies/<policy_id>", methods=["GET"])
@require_auth
def get_policy(policy_id):
    policy = POLICIES.get(policy_id)
    if not policy:
        return jsonify({"error": "Policy not found"}), 404
    return jsonify(policy)


@app.route("/v0/policies/<policy_id>", methods=["DELETE"])
@require_auth
def delete_policy(policy_id):
    if policy_id not in POLICIES:
        return jsonify({"error": "Policy not found"}), 404
    del POLICIES[policy_id]
    return jsonify({})


# --- Certificates ---

@app.route("/v0/certificates", methods=["GET"])
@require_auth
def list_certificates():
    return jsonify(list(CERTIFICATES.values()))


@app.route("/v0/certificates/<cert_id>", methods=["GET"])
@require_auth
def get_certificate(cert_id):
    cert = CERTIFICATES.get(cert_id)
    if not cert:
        return jsonify({"error": "Certificate not found"}), 404
    return jsonify(cert)


# --- Backup / Restore ---

@app.route("/v0/backup", methods=["POST"])
@require_auth
def backup():
    data = request.get_json(force=True) if request.data else {}
    return jsonify({
        "status": "success",
        "backup_id": str(uuid.uuid4()),
        "destination": data.get("destination", "/default/backup.tar.gz"),
    })


@app.route("/v0/restore", methods=["POST"])
@require_auth
def restore():
    data = request.get_json(force=True)
    return jsonify({
        "status": "success",
        "restore_id": str(uuid.uuid4()),
        "source": data.get("source"),
    })


if __name__ == "__main__":
    seed_data()

    cert_path = "/certs/server.crt"
    key_path = "/certs/server.key"
    if not os.path.exists(cert_path):
        os.makedirs("/certs", exist_ok=True)
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", key_path, "-out", cert_path,
            "-days", "365", "-nodes",
            "-subj", "/CN=localhost",
        ], check=True)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)
    app.run(host="0.0.0.0", port=1443, ssl_context=context)
