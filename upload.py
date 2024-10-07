import argparse
import json
import os
import pickle

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PICKLE_FILE = "token.pickle"


def load_config(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def get_authenticated_service():
    credentials = None
    if os.path.exists(TOKEN_PICKLE_FILE):
        with open(TOKEN_PICKLE_FILE, "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        try:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = (
                    google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                        "client_secrets.json", SCOPES
                    )
                )
                credentials = flow.run_local_server(port=0)

            # Save the refreshed or newly acquired credentials for future use
            with open(TOKEN_PICKLE_FILE, "wb") as token:
                pickle.dump(credentials, token)
        except RefreshError:
            # If refreshing fails, prompt for re-authentication
            print("Refresh failed, requiring re-authentication...")
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json", SCOPES
            )
            credentials = flow.run_local_server(port=0)

            with open(TOKEN_PICKLE_FILE, "wb") as token:
                pickle.dump(credentials, token)

    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)


def upload_video(youtube, config):
    body = {
        "snippet": {
            "title": config["title"],
            "description": config["description"],
            "categoryId": config["category"],
        },
        "status": {"privacyStatus": config["privacy_status"]},
    }
    media = MediaFileUpload(config["file_path"], chunksize=-1, resumable=True)
    try:
        request = youtube.videos().insert(
            part="snippet,status", body=body, media_body=media
        )
        response = request.execute()
        print(f"Video uploaded successfully! Video ID: {response['id']}")
        return True
    except googleapiclient.errors.HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    parser.add_argument(
        "--config_file", help="Path to the JSON configuration file", required=True
    )
    args = parser.parse_args()
    config = load_config(args.config_file)
    youtube = get_authenticated_service()
    upload_video(youtube, config)


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    main()
