
import os

import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def get_mongodb_uri():

    # First check local environment variables (.env)
    mongodb_uri = os.getenv("MONGODB_URI")

    # If not found, check Streamlit Cloud Secrets
    if not mongodb_uri:
        try:
            mongodb_uri = st.secrets["MONGODB_URI"]
        except (KeyError, FileNotFoundError):
            mongodb_uri = None

    if not mongodb_uri:
        raise ValueError(
            "MONGODB_URI not found. "
            "Configure it in your .env file or Streamlit Cloud Secrets."
        )

    return mongodb_uri


@st.cache_resource
def get_mongodb_client():

    mongodb_uri = get_mongodb_uri()

    client = MongoClient(
        mongodb_uri,
        serverSelectionTimeoutMS=5000
    )

    # Verify that MongoDB Atlas is reachable
    client.admin.command("ping")

    return client


def get_database():

    client = get_mongodb_client()

    return client["studypod"]
