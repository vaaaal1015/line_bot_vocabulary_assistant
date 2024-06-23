import requests
from mutagen.mp3 import MP3
import tempfile
import urllib

TTS_BASE_URL = 'https://speech.voicetube.com/lang/en-US/pitch/1/speakingRate/1/'


class Speech:

    def __init__(self, text):
        self.text = text

    def get_url(self):
        text = urllib.parse.quote(self.text)
        url = f'{TTS_BASE_URL}{text}.mp3'
        return url

    def get_duration(self):
        url = self.get_url()
        print(url)
        response = requests.get(url)
        tmp = tempfile.NamedTemporaryFile()
        with open(tmp.name, "wb") as f:
            f.write(response.content)
        audio = MP3(tmp.name)
        return int(audio.info.length * 1000)
