from flask import Flask, request, abort
from dotenv import dotenv_values
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from .shared.db import db
from .models.vocabulary import Vocabulary
from math import ceil
from sqlalchemy.sql.expression import func

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)
with app.app_context():
    db.create_all()

config = dotenv_values(dotenv_path="../.env")

configuration = Configuration(access_token=config["CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(config["CHANNEL_SECRET"])


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info(
            r"Invalid signature. "
            r"Please check your channel access token/channel secret.")
        abort(400)
    return "OK"


def add_vocabulary(english: str, chinese: str) -> str:
    app.logger.debug(f"enginsh:{english}")
    app.logger.debug(f"chinese:{chinese}")
    exists = Vocabulary.query.filter_by(english=english).first()
    if exists:
        return "新增失敗，單字已存在"
    vocabulary = Vocabulary(english=english, chinese=chinese)
    db.session.add(vocabulary)
    db.session.commit()
    return "新增成功"


def list_vocabulary(page: int) -> str:
    if page == 0:
        count = Vocabulary.query.count()
        return f"總頁數:{ceil(count / 10)}"

    obj = Vocabulary.query.order_by(Vocabulary.id.asc())
    page_objs = obj.paginate(
        page=page,
        per_page=10,
    ).items
    string = f"第{page}頁\n"
    string = string + "\n".join(map(str, page_objs))
    return string


def remove_vocabulary(english: str) -> str:
    count = Vocabulary.query.filter_by(english=english).delete()
    db.session.commit()
    if count == 0:
        return "刪除失敗，沒有該單字"
    return "刪除成功"


def exam_vocabulary() -> str:
    question = Vocabulary.query.order_by(func.random()).limit(5)
    string = f"{question.first().english}\n----------\n"
    string = string + "\n".join([item.chinese for item in question])
    return string


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        msg = event.message.text.lower().split()
        reply = "失敗，沒有符合的指令"

        if (msg[0] == ":add" and len(msg) == 3):
            reply = add_vocabulary(english=msg[1], chinese=msg[2])
        elif (msg[0] == ":ls"):
            if (len(msg) == 2):
                reply = list_vocabulary(page=int(msg[1]))
            else:
                reply = list_vocabulary(page=0)
        elif (msg[0] == ":rm" and len(msg) == 2):
            reply = remove_vocabulary(msg[1])
        elif (msg[0] == ":exam"):
            reply = exam_vocabulary()

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)],
            ))


if __name__ == "__main__":
    app.run()
