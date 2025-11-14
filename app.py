import os, json
from pathlib import Path
from flask import Flask, request, jsonify, render_template
import requests
from dotenv import load_dotenv

env_path = Path(__file__).with_name(".env")
load_dotenv(env_path)

app = Flask(__name__)

JENKINS_URL   = (os.getenv("JENKINS_URL") or "").rstrip("/")
JENKINS_JOB   = os.getenv("JENKINS_JOB") or ""
JENKINS_USER  = os.getenv("JENKINS_USER") or ""
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN") or ""
VALID_TARGETS = {"all", "backend", "frontend"}

# ----------- 管理界面 -----------
@app.route("/")
def index():
    return render_template("index.html")

# ----------- API 接口（保持兼容） -----------
@app.route("/deploy", methods=["POST"])
def deploy():
    body = request.get_json(silent=True) or {}
    target = body.get("deploy_target", "all").strip().lower()
    if target not in VALID_TARGETS:
        return jsonify(error=f"deploy_target must be one of {VALID_TARGETS}"), 400

    missing = []
    if not JENKINS_URL:
        missing.append("JENKINS_URL")
    if not JENKINS_JOB:
        missing.append("JENKINS_JOB")
    if not JENKINS_USER:
        missing.append("JENKINS_USER")
    if not JENKINS_TOKEN:
        missing.append("JENKINS_TOKEN")
    if missing:
        return jsonify(error="Missing required env", fields=missing), 500

    build_url = f"{JENKINS_URL}/job/{JENKINS_JOB}/buildWithParameters"
    try:
        resp = requests.post(
            build_url,
            params={"DEPLOY_TARGET": target},
            auth=(JENKINS_USER, JENKINS_TOKEN),
            timeout=10,
        )
        if resp.status_code in (200, 201, 302):
            return jsonify(message="Jenkins job triggered", target=target), 200
        return jsonify(error="Jenkins error", detail=resp.text[:300]), resp.status_code
    except Exception as e:
        return jsonify(error="Failed to call Jenkins", detail=str(e)), 500

# ----------- 健康检查 -----------
@app.route("/ping")
def ping():
    return "pong", 200

if __name__ == "__main__":
    # 生产用 gunicorn，开发可直接 python app.py
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 3000)))
