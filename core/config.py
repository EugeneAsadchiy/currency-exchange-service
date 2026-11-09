import os

from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ["POSTGRES_DB"]
NBRB_RATES_URL = os.getenv("NBRB_RATES_URL", "https://api.nbrb.by/exrates/rates?periodicity=0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

PRODUCT_NAME = "Currency Exchange Service"
