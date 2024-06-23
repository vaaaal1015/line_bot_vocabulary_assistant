import unittest
from src.speech import Speech


class TestSpeech(unittest.TestCase):

    def test_get_url(self):
        speech = Speech("hello")
        url = speech.get_url()
        self.assertEqual(url,
                         (r"https://speech.voicetube.com/lang/en-US/pitch/1/"
                          r"speakingRate/1/hello.mp3"))

    def test_get_duration(self):
        speech = Speech("hello")
        duration = speech.get_duration()
        self.assertEqual(
            duration,
            888,
        )


if __name__ == "__main__":
    unittest.main()
