from os import environ
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)

CHANNEL_ACCESS_TOKEN = environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = environ.get("CHANNEL_SECRET")
SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")
