# encoding:utf-8
import os
import json
import requests
from flask import Flask, request
from wechatpy.enterprise import WeChatClient  # 企业微信 API
app = Flask(__name__)

# 读取企业微信 API 相关信息（从 Railway 环境变量获取）
CORP_ID = os.getenv("WECHAT_WORK_CORP_ID")
AGENT_ID = os.getenv("WECHAT_WORK_AGENT_ID")
SECRET = os.getenv("WECHAT_WORK_SECRET")
WEBHOOK = os.getenv("WECHAT_WORK_WEBHOOK")  # 企业微信群 Webhook

# 连接企业微信 API
client = WeChatClient(CORP_ID, SECRET)
def send_wechat_message(user, message):
    """ 发送消息到企业微信用户 """
    data = {
        "touser": user,  # 指定要回复的用户
        "msgtype": "text",
        "agentid": AGENT_ID,
        "text": {"content": message},
        "safe": 0
    }
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={client.access_token}"
    response = requests.post(url, json=data).json()
    return response

@app.route("/wechat", methods=["POST"])
def wechat_callback():
    """ 处理企业微信消息，并调用 ChatGPT 回复 """
    data = request.json
    user = data.get("from")  # 获取消息发送者
    message = data.get("text")  # 获取消息内容

    if not user or not message:
        return json.dumps({"status": "error", "message": "Invalid request"}), 400

    # 让 ChatGPT 处理消息
    response = chat_with_gpt(message)

    # 回复用户
    send_wechat_message(user, response)

    return json.dumps({"status": "success"}), 200

import os
import signal
import sys
import time

from channel import channel_factory
from common import const
from config import load_config
from plugins import *
import threading


def sigterm_handler_wrap(_signo):
    old_handler = signal.getsignal(_signo)

    def func(_signo, _stack_frame):
        logger.info("signal {} received, exiting...".format(_signo))
        conf().save_user_datas()
        if callable(old_handler):  #  check old_handler
            return old_handler(_signo, _stack_frame)
        sys.exit(0)

    signal.signal(_signo, func)


def start_channel(channel_name: str):
    channel = channel_factory.create_channel(channel_name)
    if channel_name in ["wx", "wxy", "terminal", "wechatmp","web", "wechatmp_service", "wechatcom_app", "wework",
                        const.FEISHU, const.DINGTALK]:
        PluginManager().load_plugins()

    if conf().get("use_linkai"):
        try:
            from common import linkai_client
            threading.Thread(target=linkai_client.start, args=(channel,)).start()
        except Exception as e:
            pass
    channel.startup()


def run():
    try:
        # load config
        load_config()
        # ctrl + c
        sigterm_handler_wrap(signal.SIGINT)
        # kill signal
        sigterm_handler_wrap(signal.SIGTERM)

        # create channel
        channel_name = conf().get("channel_type", "wx")

        if "--cmd" in sys.argv:
            channel_name = "terminal"

        if channel_name == "wxy":
            os.environ["WECHATY_LOG"] = "warn"

        start_channel(channel_name)

        while True:
            time.sleep(1)
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)


if __name__ == "__main__":
    run()
