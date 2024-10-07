#!/usr/bin/env python3

import argparse
import json
import os
import time

import dotenv
from openai import OpenAI

import images
import narration
import upload
import utils
import video

dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def main(system_prompt, user_prompt=None, caption_settings={}):

    short_id = str(int(time.time()))

    output_file = "short.avi"

    basedir = os.path.join("shorts", short_id)
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    print("Generating script...")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    user_prompt
                    if user_prompt
                    else f"Create a YouTube narration about the following animal:{utils.pick_random_animal('animals.txt')}"
                ),
            },
        ],
    )

    response_text = response.choices[0].message.content
    response_text.replace("’", "'").replace("`", "'").replace("…", "...").replace(
        "“", '"'
    ).replace("”", '"')

    with open(os.path.join(basedir, "response.txt"), "w") as f:
        f.write(response_text)

    data, narrations = narration.parse(response_text)
    with open(os.path.join(basedir, "data.json"), "w") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"Generating narration...")
    narration.create(data, os.path.join(basedir, "narrations"))

    print("Generating images...")
    images.create_from_data(data, os.path.join(basedir, "images"))

    print("Generating video...")
    video.create(narrations, basedir, output_file, caption_settings)

    print("Normalizing sound...")
    normalized_output_file = f"normalized_{output_file}"
    utils.normalize_sound(basedir, output_file, normalized_output_file)

    print(
        f"DONE! Here's your generated video: {os.path.join(basedir, normalized_output_file)}"
    )

    print("Generating upload config...")
    upload_config_file = utils.generate_upload_config(basedir)

    print("Uploading video...")
    youtube = upload.get_authenticated_service()
    config = upload.load_config(upload_config_file)
    if upload.upload_video(youtube, config) is True:
        print(f"DONE! Uploaded video to YouTube")
    else:
        print(f"FAILED! Failed to upload video to YouTube")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--system_prompt", type=str, required=True)
    parser.add_argument("--user_prompt", type=str, required=False)
    parser.add_argument("--caption_settings", type=str, required=False)
    args = parser.parse_args()

    with open(args.system_prompt) as f:
        system_prompt = f.read()

    user_prompt = args.user_prompt if args.user_prompt else None

    caption_settings = {}
    if args.caption_settings:
        with open(args.caption_settings) as f:
            caption_settings = json.load(f)

    main(system_prompt, user_prompt, caption_settings)
