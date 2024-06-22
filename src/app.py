from flask import Flask, request, abort
from dotenv import dotenv_values
import requests
from mutagen.mp3 import MP3
import tempfile
import urllib

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    AudioMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

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
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)
    return "OK"


def get_audio_len_from_url(url):
    response = requests.get(url)
    tmp = tempfile.NamedTemporaryFile()
    with open(tmp.name, "wb") as f:
        f.write(response.content)
    audio = MP3(tmp.name)
    return int(audio.info.length * 1000)


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        mp3_file_name = urllib.parse.quote(event.message.text)
        audio_url = f"https://speech.voicetube.com/lang/en-US/pitch/1/speakingRate/1/{mp3_file_name}.mp3"
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    AudioMessage(
                        originalContentUrl=audio_url,
                        duration=get_audio_len_from_url(audio_url),
                    )
                ],
            )
        )


if __name__ == "__main__":
    app.run()
