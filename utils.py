import json
import os
import random
import subprocess

import dotenv
from openai import OpenAI

import constants
import upload

dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_uploaded_video_titles(youtube):
    uploads_playlist_id = upload.get_uploads_playlist_id(youtube)
    if not uploads_playlist_id:
        return []

    titles = []
    next_page_token = None

    while True:
        playlist_items_response = (
            youtube.playlistItems()
            .list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )
            .execute()
        )

        for item in playlist_items_response["items"]:
            titles.append(item["snippet"]["title"])

        next_page_token = playlist_items_response.get("nextPageToken")
        if not next_page_token:
            break

    return titles


def filter_animals(animals_file_path, youtube):
    with open(animals_file_path, "r") as file:
        all_animals = set(file.read().splitlines())

    uploaded_titles = get_uploaded_video_titles(youtube)
    used_animals = set()

    for title in uploaded_titles:
        title_lower = title.lower()
        for animal in all_animals:
            if animal.lower() in title_lower:
                used_animals.add(animal)

    return list(all_animals - used_animals)


def pick_random_animal(file_path, youtube):
    filtered_animals = filter_animals(file_path, youtube)

    if not filtered_animals:
        return None

    return random.choice(filtered_animals)


def normalize_sound(basedir, input_file, output_file):
    input_file_path = os.path.join(basedir, input_file)
    output_file_path = os.path.join(basedir, output_file)

    ffmpeg_command = [
        "ffmpeg",
        "-i",
        input_file_path,
        "-c:v",
        "copy",
        "-af",
        "loudnorm=I=-14:TP=-2:LRA=11",
        output_file_path,
    ]

    subprocess.run(ffmpeg_command, capture_output=True)

    os.remove(input_file_path)


def generate_upload_config(basedir):

    with open(os.path.join(basedir, "response.txt"), "r") as file:
        script = file.read()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that generates catchy YouTube short titles and descriptions.",
            },
            {
                "role": "user",
                "content": f"Please generate a catchy title and description for the following youtube short script: {script}. "
                "Include relevant emojis at the end of the title and description. "
                "Return the title and description as valid JSON.",
            },
        ],
        response_format={"type": "json_object"},
    )

    response_text = response.choices[0].message.content

    # Use json.loads() to parse the response into a Python dict
    try:
        config = json.loads(response_text)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        # You may need to clean or correct the response to extract valid JSON

    config["file_path"] = os.path.join(basedir, "normalized_short.avi")
    config["category"] = "15"
    config["privacy_status"] = "private"
    config["description"] = f"{config['description']}\n\n{constants.DISCLAIMER}"

    print(config)

    with open(os.path.join(basedir, "upload_config.json"), "w") as f:
        json.dump(config, f)

    return os.path.join(basedir, "upload_config.json")
