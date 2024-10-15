import argparse
import json
import os
import pickle

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

import constants

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
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
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json", SCOPES
            )
            credentials = flow.run_local_server(port=0)

        # Save the credentials for the next run
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


def get_uploads_playlist_id(youtube):
    channels_response = (
        youtube.channels().list(part="contentDetails", mine=True).execute()
    )

    if not channels_response["items"]:
        print("No channel found for the authenticated user.")
        return None

    return channels_response["items"][0]["contentDetails"]["relatedPlaylists"][
        "uploads"
    ]


def update_video_descriptions(youtube, disclaimer, batch_size=50):
    uploads_playlist_id = get_uploads_playlist_id(youtube)
    if not uploads_playlist_id:
        return

    page_token = None
    updated_count = 0
    total_count = 0

    while True:
        # Fetch video IDs from the uploads playlist
        playlist_items_response = (
            youtube.playlistItems()
            .list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=batch_size,
                pageToken=page_token,
            )
            .execute()
        )

        video_ids = [
            item["contentDetails"]["videoId"]
            for item in playlist_items_response["items"]
        ]
        total_count += len(video_ids)

        if not video_ids:
            break

        # Fetch video details
        videos_response = (
            youtube.videos().list(part="snippet", id=",".join(video_ids)).execute()
        )

        # Prepare batch request
        batch = youtube.new_batch_http_request()
        batch_count = 0

        for video in videos_response["items"]:
            snippet = video["snippet"]
            current_description = snippet["description"]
            if not current_description.endswith(disclaimer):
                snippet["description"] = current_description + "\n\n" + disclaimer
                batch.add(
                    youtube.videos().update(
                        part="snippet", body={"id": video["id"], "snippet": snippet}
                    )
                )
                batch_count += 1
                updated_count += 1
                print(
                    f"Updating video: {video['snippet']['title']} (ID: {video['id']})"
                )

        # Execute batch request if there are updates
        if batch_count > 0:
            batch.execute()
            print(f"Updated {batch_count} video descriptions in this batch.")

        page_token = playlist_items_response.get("nextPageToken")
        if not page_token:
            break

    print(f"Updated {updated_count} out of {total_count} video descriptions.")


def main():
    parser = argparse.ArgumentParser(
        description="Upload a video to YouTube or update video descriptions."
    )
    parser.add_argument(
        "--config_file", help="Path to the JSON configuration file", required=False
    )
    parser.add_argument(
        "--update_descriptions",
        action="store_true",
        help="Update all video descriptions",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=50,
        help="Batch size for updating descriptions (max 50)",
    )
    args = parser.parse_args()

    youtube = get_authenticated_service()

    if args.update_descriptions:
        update_video_descriptions(youtube, constants.DISCLAIMER, args.batch_size)
    elif args.config_file:
        config = load_config(args.config_file)
        upload_video(youtube, config)
    else:
        print("Please specify either --config_file or --update_descriptions")


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    main()
