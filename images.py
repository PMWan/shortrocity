import argparse
import base64
import os

import dotenv
import replicate
import requests
from openai import OpenAI

dotenv.load_dotenv()


def create_images_from_data(data, output_dir, image_svc) -> None:
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image_number = 0
    for element in data:
        if element["type"] != "image":
            continue
        image_number += 1
        image_name = f"image_{image_number}.webp"
        prompt = element["description"] + ". Vertical image, fully filling the canvas."
        create_image_from_prompt(
            prompt, os.path.join(output_dir, image_name), image_svc
        )


def create_image_from_prompt(prompt, output_file, image_svc):
    if image_svc == "dall_e":
        image_b64 = generate_using_dall_e(prompt)
        save_image_from_dall_e_b64(image_b64, output_file)
    elif image_svc == "flux_schnell":
        image_url = generate_using_flux_schnell(prompt)
        save_image_from_flux_url(image_url, output_file)
    elif image_svc == "flux_pro":
        image_url = generate_using_flux_pro(prompt)
        save_image_from_flux_url(image_url, output_file)
    else:
        raise ValueError(f"Unknown image service: {image_svc}")


def generate_using_dall_e(prompt, size="1024x1792"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality="standard",
        response_format="b64_json",
        n=1,
    )
    return response.data[0].b64_json


def save_image_from_dall_e_b64(image_b64, output_file) -> None:
    with open(output_file, "wb") as f:
        f.write(base64.b64decode(image_b64))


def generate_using_flux_schnell(prompt: str, aspect_ratio="9:16") -> str:
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


def generate_using_flux_pro(prompt: str, aspect_ratio="9:16") -> str:
    output = replicate.run(
        "black-forest-labs/flux-1.1-pro",
        input={
            "prompt": prompt,
            "num_outputs": 1,
            "aspect_ratio": aspect_ratio,
            "output_format": "webp",
            "output_quality": 80,
            "num_inference_steps": 4,
        },
    )
    return output


def save_image_from_flux_url(url, output_file):
    response = requests.get(url)
    with open(output_file, "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--output_file", type=str, required=True)
    parser.add_argument(
        "--image_svc",
        choices=["dall_e", "flux_schnell", "flux_pro"],
        default="dall_e",
        type=str,
    )
    args = parser.parse_args()
    create_image_from_prompt(args.prompt, args.output_file, args.image_svc)
