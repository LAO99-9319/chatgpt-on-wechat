# encoding:utf-8
import os
import json
import requests
from flask import Flask, request
from wechatpy.enterprise import WeChatClient
from common.log import logger  # 日志管理

# Flask 服务器
app = Flask(__name__)

# 企业微信 API 配置（从 Railway 环境变量获取）
CORP_ID = os.getenv("WECHAT_WORK_CORP_ID")
AGENT_ID = os.getenv("WECHAT_WORK_AGENT_ID")
SECRET = os.getenv("WECHAT_WORK_SECRET")
WEBHOOK = os.getenv("WECHAT_WORK_WEBHOOK")  # 企业微信群 Webhook

# 确保环境变量已正确配置
if not CORP_ID or not AGENT_ID or not SECRET:
    logger.error("❌ 企业微信 API 配置错误！请检查环境变量 WECHAT_WORK_CORP_ID, WECHAT_WORK_AGENT_ID, WECHAT_WORK_SECRET 是否正确配置。")
    exit(1)

# 获取 Access Token（防止失效）
def get_access_token():
    """ 获取企业微信 Access Token """
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORP_ID}&corpsecret={SECRET}"
    response = requests.get(url).json()
    return response.get("access_token")

# 发送消息到企业微信用户
def send_wechat_message(user, message):
    """ 发送企业微信消息 """
    token = get_access_token()  # 获取最新的 access_token
    data = {
        "touser": user,
        "msgtype": "text",
        "agentid": AGENT_ID,
        "text": {"content": message},
        "safe": 0
    }
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    response = requests.post(url, json=data).json()
    return response

# 监听并处理企业微信消息
@app.route("/wechat", methods=["POST"])
def wechat_callback():
    """ 处理企业微信消息，并调用 ChatGPT 回复 """
    try:
        data = request.json  # 获取请求数据
        logger.info(f"📩 收到企业微信消息: {data}")  # 记录日志

        user = data.get("from")  # 获取消息发送者
        message = data.get("text")  # 获取消息内容

        if not user or not message:
            return json.dumps({"status": "error", "message": "Invalid request"}), 400

        # 让 ChatGPT 处理消息
        response = chat_with_gpt(message)

        # 发送回复到企业微信
        send_wechat_message(user, response)

        return json.dumps({"status": "success"}), 200

    except Exception as e:
        logger.error(f"❌ 企业微信消息处理失败: {str(e)}")
        return json.dumps({"status": "error", "message": str(e)}), 500

# ChatGPT 处理消息（可替换为 OpenAI API）
def chat_with_gpt(message):
    """ 调用 ChatGPT API 处理消息 """
    try:
        # 这里可以调用 OpenAI API
        # response = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": message}])
        return f"🤖 ChatGPT 回复：{message}"  # 这里可以改成真正的 API 调用
    except Exception as e:
        logger.error(f"❌ ChatGPT 处理消息失败: {str(e)}")
        return "抱歉，我无法处理您的请求。"

# 发送消息到企业微信群（如果使用 Webhook）
def send_wechat_group_message(message):
    """ 发送消息到企业微信群 """
    if not WEBHOOK:
        logger.warning("⚠️ 企业微信群 Webhook 未配置，无法发送消息！")
        return {"error": "WEBHOOK 未配置"}

    data = {"msgtype": "text", "text": {"content": message}}
    response = requests.post(WEBHOOK, json=data).json()
    return response

# 确保 Flask 服务器运行
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 80))  # Railway 需要监听 80 端口
    app.run(host="0.0.0.0", port=port, debug=True)
