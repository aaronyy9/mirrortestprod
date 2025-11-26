import os, json
from pathlib import Path
from flask import Flask, request, jsonify, render_template
import requests
from dotenv import load_dotenv

env_path = Path(__file__).with_name(".env")
load_dotenv(env_path, override=True)

app = Flask(__name__)

JENKINS_URL   = (os.getenv("JENKINS_URL") or "").rstrip("/")
JENKINS_JOB   = os.getenv("JENKINS_JOB") or ""
JENKINS_USER  = os.getenv("JENKINS_USER") or ""
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN") or ""
PROJECTS = {
    "bms": {"targets": {"all", "backend", "frontend"}, "jobs_env": True, "jobs": []},
    "standard_demo": {"targets": {
        "all",
        "standard-account-demo-backend",
        "standard-aiquery-demo-backend",
        "standard-aiaccount-demo-web-Docker-quick",
    }, "jobs_env": False, "jobs": [
        "standard-account-demo-backend",
        "standard-aiquery-demo-backend",
        "standard-aiaccount-demo-web-Docker-quick",
    ]},
}

# ----------- 管理界面 -----------
@app.route("/")
def index():
    return render_template("index.html")

# ----------- API 接口（保持兼容） -----------
@app.route("/deploy", methods=["POST"])
def deploy():
    body = request.get_json(silent=True) or {}
    project = (body.get("project") or "bms").strip().lower()
    target = (body.get("deploy_target") or "all").strip()
    if project not in PROJECTS:
        return jsonify(error="invalid project", projects=list(PROJECTS.keys())), 400
    if target not in PROJECTS[project]["targets"]:
        return jsonify(error=f"invalid target", targets=list(PROJECTS[project]["targets"])), 400

    missing = []
    if not JENKINS_URL:
        missing.append("JENKINS_URL")
    if not JENKINS_USER:
        missing.append("JENKINS_USER")
    if not JENKINS_TOKEN:
        missing.append("JENKINS_TOKEN")
    if PROJECTS[project]["jobs_env"] and not JENKINS_JOB:
        missing.append("JENKINS_JOB")
    if missing:
        return jsonify(error="Missing required env", fields=missing), 500

    jobs = []
    if PROJECTS[project]["jobs_env"]:
        jobs = [JENKINS_JOB]
    else:
        if target == "all":
            jobs = PROJECTS[project]["jobs"]
        else:
            jobs = [target]
    if not jobs:
        return jsonify(error="no jobs configured"), 500

    results = []
    ok = True
    for job in jobs:
        build_url = f"{JENKINS_URL}/job/{job}/buildWithParameters"
        try:
            params = {"DEPLOY_TARGET": target} if project == "bms" else {}
            resp = requests.post(
                build_url,
                params=params,
                auth=(JENKINS_USER, JENKINS_TOKEN),
                timeout=10,
            )
            r = {"job": job, "status": resp.status_code, "ok": resp.status_code in (200, 201, 302)}
            results.append(r)
            if not r["ok"]:
                ok = False
        except Exception as e:
            results.append({"job": job, "error": str(e), "ok": False})
            ok = False
    if ok:
        return jsonify(message="jobs triggered", project=project, target=target, results=results), 200
    return jsonify(error="some jobs failed", project=project, target=target, results=results), 500

# ----------- 健康检查 -----------
@app.route("/ping")
def ping():
    return "pong", 200

if __name__ == "__main__":
    # 生产用 gunicorn，开发可直接 python app.py
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 3000)))
