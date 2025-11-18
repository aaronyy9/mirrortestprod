from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
import subprocess
import logging

app = Flask(__name__)
auth = HTTPBasicAuth()

# 用户凭据
users = {
    "depz": "zenx2020"  # 替换为你的用户名和密码
}

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

@app.route('/zenxup', methods=['GET'])
@auth.login_required
def update():
    try:
        # 获取请求参数 type
        type = request.args.get('type', '4')  # 默认值为 '4' (all)
        logging.debug(f"Starting command execution with type: {type}")

        # 检查 type 是否合法
    if type not in ['1', '2', '3', '4', '5', '6', '7']:
        return jsonify({"status": "error", "output": "Invalid type parameter"}), 400

        # 定义要执行的 Shell 命令
        command = f"cd /data/zenx_soft/depzen/tools && bash up.sh {type}"

        # 使用 subprocess 执行命令
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        logging.debug("Command execution completed")
        # 检查命令是否成功执行
        if process.returncode == 0:
            return jsonify({"status": "success", "output": stdout.decode('utf-8')})
        else:
            logging.error(f"Command failed with error: {stderr.decode('utf-8')}")
            return jsonify({"status": "error", "output": stderr.decode('utf-8')}), 500
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return jsonify({"status": "error", "output": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=20001)
