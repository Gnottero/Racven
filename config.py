import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-key-change-me')
    DATABASE_PATH = os.environ.get('DATABASE_PATH')

    TV_CAROUSEL_INTERVAL_SECONDS = int(os.environ.get('TV_CAROUSEL_INTERVAL_SECONDS', 6))
    TV_MESSAGE_DISPLAY_SECONDS = int(os.environ.get('TV_MESSAGE_DISPLAY_SECONDS', 8))
    TV_DUTY_DISPLAY_SECONDS = int(os.environ.get('TV_DUTY_DISPLAY_SECONDS', 15))
