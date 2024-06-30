from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (Configuration, ApiClient, MessagingApi,
                                  ReplyMessageRequest, TextMessage,
                                  MessageAction, FlexMessage, FlexBubble,
                                  FlexBox, FlexText, FlexButton)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from shared.db import db
from models.vocabulary import Vocabulary
from sqlalchemy.sql.expression import func
import random
from settings import (CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET,
                      SQLALCHEMY_DATABASE_URI)
from sqlalchemy import select, delete

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
db.init_app(app)
with app.app_context():
    db.create_all()

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


def add_vocabulary(english: str, chinese: str) -> TextMessage:
    exists = db.session.execute(
        select(Vocabulary).where(Vocabulary.english == english)).scalar()
    if exists:
        return TextMessage(text="新增失敗，單字已存在")
    db.session.add(Vocabulary(english=english, chinese=chinese))
    db.session.commit()
    return TextMessage(text="新增成功")


def list_vocabulary(page: int) -> TextMessage:
    if page <= 0:
        page = 1
    pagination = db.paginate(select=select(Vocabulary).order_by(Vocabulary.id),
                             page=page,
                             per_page=10)
    string = f"第{pagination.page}頁, 共{pagination.pages}頁\n" + "\n".join(
        map(str, pagination))
    return TextMessage(text=string)


def remove_vocabulary(english: str) -> TextMessage:
    vocabulary = db.session.execute(
        delete(Vocabulary).where(
            Vocabulary.english == english).returning(Vocabulary)).scalar()
    db.session.commit()
    if vocabulary:
        return TextMessage(text="刪除成功")
    return TextMessage(text="刪除失敗，沒有該單字")


def exam_vocabulary() -> FlexMessage:
    selection = db.session.execute(
        select(Vocabulary).order_by(Vocabulary.point,
                                    func.random()).limit(5)).scalars().all()
    buttons = [
        FlexButton(action=MessageAction(
            label=item.chinese,
            text=f":ans {selection[0].english} {item.chinese}"))
        for item in selection
    ]
    random.shuffle(buttons)
    return FlexMessage(altText="exam",
                       contents=FlexBubble(
                           size="micro",
                           header=FlexBox(
                               layout="vertical",
                               alignItems="center",
                               contents=[FlexText(text=selection[0].english)]),
                           body=FlexBox(layout="vertical", contents=buttons)))


def answer_vocabulary(question: str, answer: str) -> TextMessage:
    vocabulary = db.session.execute(
        select(Vocabulary).where(Vocabulary.english == question)).scalar()
    if vocabulary:
        if vocabulary.chinese == answer:
            vocabulary.bonus_point()
            reply = TextMessage(text="回答正確")
        else:
            vocabulary.deduct_point()
            reply = TextMessage(text=f"回答錯誤，{str(vocabulary)}")
        db.session.commit()
        return reply
    else:
        return TextMessage(text="回答失敗，沒有該單字")


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


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        msg = event.message.text.lower().split()

        if (msg[0] == ":add" and len(msg) == 3):
            messages = add_vocabulary(english=msg[1], chinese=msg[2])
        elif (msg[0] == ":ls" and len(msg) == 2):
            messages = list_vocabulary(page=int(msg[1]))
        elif (msg[0] == ":ls" and len(msg) == 1):
            messages = list_vocabulary(page=0)
        elif (msg[0] == ":rm" and len(msg) == 2):
            messages = remove_vocabulary(msg[1])
        elif (msg[0] == ":exam"):
            messages = exam_vocabulary()
        elif (msg[0] == ":ans" and len(msg) == 3):
            messages = answer_vocabulary(question=msg[1], answer=msg[2])
        else:
            messages = TextMessage(text="失敗，沒有符合的指令")

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[messages],
            ))


if __name__ == "__main__":
    app.run()
