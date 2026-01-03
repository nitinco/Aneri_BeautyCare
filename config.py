import os
from dotenv import load_dotenv

# load .env if present
load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', "aneri_secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', "mysql+pymysql://root:@localhost/aneri_beautycare")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
