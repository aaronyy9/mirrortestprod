import os, json
from pathlib import Path
from flask import Flask, request, jsonify, render_template
import requests
from dotenv import load_dotenv

env_path = Path(__file__).with_name(".env")
load_dotenv(env_path)

app = Flask(__name__)

VALID_TARGETS = {"all", "backend", "frontend"}

def _get_jenkins_config():
    url = (os.getenv("JENKINS_URL") or "").strip().rstrip("/")
    job = (os.getenv("JENKINS_JOB") or "").strip()
    user = (os.getenv("JENKINS_USER") or "").strip()
    token = (os.getenv("JENKINS_TOKEN") or "").strip()
    missing = [k for k, v in {"JENKINS_URL": url, "JENKINS_JOB": job, "JENKINS_USER": user, "JENKINS_TOKEN": token}.items() if not v]
    return {"url": url, "job": job, "user": user, "token": token}, missing

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

    cfg, missing = _get_jenkins_config()
    if missing:
        return jsonify(error="Missing Jenkins configuration", missing=missing), 500
    if not (cfg["url"].startswith("http://") or cfg["url"].startswith("https://")):
        return jsonify(error="Invalid JENKINS_URL", value=cfg["url"]), 400

    build_url = f"{cfg['url']}/job/{cfg['job']}/buildWithParameters"
    try:
        resp = requests.post(
            build_url,
            params={"DEPLOY_TARGET": target},
            auth=(cfg["user"], cfg["token"]),
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
