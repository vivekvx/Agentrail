import os

from fastapi import FastAPI

app = FastAPI()
database_url = os.environ["DATABASE_URL"]
