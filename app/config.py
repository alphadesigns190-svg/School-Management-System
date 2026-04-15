import os

from dotenv import load_dotenv


class Config:
    def __init__(self):
        load_dotenv()

        self.DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
        self.SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

        self.ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
        self.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
        self.SCHOOL_NAME = os.getenv("SCHOOL_NAME", "Learning Center")

        self.MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
        self.MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
        self.MYSQL_USER = os.getenv("MYSQL_USER", "root")
        self.MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
        self.MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "")
