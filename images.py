import argparse
import base64
import os

import dotenv
import replicate
import requests
from openai import OpenAI

dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def create_from_data(data, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image_number = 0
    for element in data:
        if element["type"] != "image":
            continue
        image_number += 1
        image_name = f"image_{image_number}.webp"
        # generate_using_dall_e(
        #     element["description"] + ". Vertical image, fully filling the canvas.",
        #     os.path.join(output_dir, image_name),
        # )
        image_url = generate_using_flux(
            element["description"] + ". Vertical image, fully filling the canvas.",
        )
        save_image_from_flux_url(image_url, os.path.join(output_dir, image_name))


def generate_using_dall_e(prompt, output_file, size="1024x1792"):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality="standard",
        response_format="b64_json",
        n=1,
    )

    image_b64 = response.data[0].b64_json

    with open(output_file, "wb") as f:
        f.write(base64.b64decode(image_b64))


def generate_using_flux(prompt: str, aspect_ratio="9:16") -> str:
    output = replicate.run(
        "black-forest-labs/flux-schnell",
        input={
            "prompt": prompt,
            "go_fast": True,
            "num_outputs": 1,
            "aspect_ratio": aspect_ratio,
            "output_format": "webp",
            "output_quality": 80,
            "num_inference_steps": 4,
        },
    )
    return output[0]


def save_image_from_flux_url(url, output_file):
    response = requests.get(url)
    with open(output_file, "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--output_file", type=str, required=True)
    args = parser.parse_args()
    # generate_using_dall_e(args.prompt, args.output_file)
    image_url = generate_using_flux(args.prompt)
    save_image_from_flux_url(args.image_url, args.output_file)
