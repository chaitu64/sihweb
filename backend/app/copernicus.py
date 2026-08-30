import os
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BASE_DIR.parent

for env_path in (BASE_DIR / ".env", ROOT_DIR / ".env"):
    if env_path.exists():
        load_dotenv(env_path, override=False)

CLIENT_ID = os.getenv("COPERNICUS_CLIENT_ID") or os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("COPERNICUS_CLIENT_SECRET") or os.getenv("CLIENT_SECRET")
USERNAME = os.getenv("COPERNICUS_USERNAME") or os.getenv("USERNAME")
PASSWORD = os.getenv("COPERNICUS_PASSWORD") or os.getenv("PASSWORD")

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)


def _request_token(payload: dict[str, str]):
    response = requests.post(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text.strip()
        raise RuntimeError(
            f"Copernicus authentication failed ({response.status_code}): {detail or 'check your credentials'}"
        ) from exc

    try:
        token = response.json()["access_token"]
    except (ValueError, KeyError) as exc:
        raise RuntimeError(f"Copernicus token response was invalid: {response.text[:500]}" ) from exc

    if not token:
        raise RuntimeError("Copernicus returned an empty access token.")

    return token


def get_access_token():
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    username = USERNAME
    password = PASSWORD

    if username and password:
        payload = {
            "grant_type": "password",
            "username": username,
            "password": password,
        }
        if client_id:
            payload["client_id"] = client_id
        if client_secret:
            payload["client_secret"] = client_secret
        return _request_token(payload)

    if client_id and client_secret:
        return _request_token(
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            }
        )

    raise RuntimeError(
        "Copernicus credentials are missing. Add COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET "
        "or COPERNICUS_USERNAME and COPERNICUS_PASSWORD to backend/.env or the repo root .env."
    )