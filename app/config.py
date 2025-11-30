import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'project.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CHART_OUTPUT_DIR = os.path.join(BASE_DIR, "app", "static", "charts")
