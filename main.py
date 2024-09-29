#!/usr/bin/env python3

from openai import OpenAI
import time
import json
import sys
import os

import narration
import images
import video
import utils


def main(system_prompt, caption_settings):

    client = OpenAI()

    short_id = str(int(time.time()))

    output_file = "short.avi"

    basedir = os.path.join("shorts", short_id)
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    print("Generating script...")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Create a YouTube short narration on the following animal:{utils.pick_random_animal('animals.txt')}"
            }
        ]
    )

    response_text = response.choices[0].message.content
    response_text.replace("’", "'").replace("`", "'").replace("…", "...").replace("“", '"').replace("”", '"')

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

    print(f"DONE! Here's your video: {os.path.join(basedir, normalized_output_file)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <system_prompt_file> [caption_settings_file]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        system_prompt = f.read()

    caption_settings = {}
    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            caption_settings = json.load(f)

    main(system_prompt, caption_settings)
