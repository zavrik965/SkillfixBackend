import os
import uuid

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = uuid.uuid4().hex #os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')\
        or 'sqlite:///' + os.path.join(basedir, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = uuid.uuid4().hex
    HOSTNAME = "http://hosting2.alexavr.ru"
    DOMEN = "http://hosting2.alexavr.ru"
    EMAIL = "qzlab@yandex.com"
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
