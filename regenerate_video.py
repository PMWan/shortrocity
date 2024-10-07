#!/usr/bin/env python3

import argparse
import json
import os

import images
import upload
import utils
import video

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process image generation and caption settings.")

    # Required argument
    parser.add_argument(
        "--basedir",
        type=str,
        required=True,
        help="The base directory where the files are located."
    )

    # Optional argument for caption settings
    parser.add_argument(
        "--caption_settings",
        type=str,
        required=False,
        help="Path to the JSON file containing caption settings (optional)."
    )

    # Optional boolean argument to regenerate images
    parser.add_argument(
        "--regenerate_images",
        action="store_true",
        help="Flag to indicate if images should be regenerated (default: False)."
    )

    # Optional argument for selecting an image service
    parser.add_argument(
        "--image_svc",
        choices=["dall_e", "flux_schnell", "flux_pro"],
        default="dall_e",
        type=str,
        help="The image generation service to use (default: 'dall_e')."
    )

    args = parser.parse_args()

    basedir = args.basedir
    narrations = [
        f for f in os.listdir(os.path.join(basedir, "narrations")) if f.endswith(".mp3")
    ]
    caption_settings = {}
    if args.caption_settings:
        with open(args.caption_settings) as f:
            caption_settings = json.load(f)

    print("Regenerating images...")
    if args.regenerate_images:
        data = json.load(open(os.path.join(basedir, "data.json")))
        images.create_images_from_data(
            data, os.path.join(basedir, "images"), args.image_svc
        )

    output_file = "short.avi"

    print("Regenerating video...")
    video.create(
        narrations,
        basedir,
        output_filename=output_file,
        caption_settings=caption_settings,
    )

    print("Normalizing sound...")
    normalized_output_file = f"normalized_{output_file}"
    utils.normalize_sound(basedir, output_file, normalized_output_file)

    print(
        f"DONE! Here's your regenerated video: {os.path.join(basedir, normalized_output_file)}"
    )

    print("Regenerating upload config...")
    upload_config_file = utils.generate_upload_config(basedir)

    # print("Uploading video...")
    # youtube = upload.get_authenticated_service()
    # config = upload.load_config(upload_config_file)
    # if upload.upload_video(youtube, config) is True:
    #     print(f"DONE! Uploaded video to YouTube")
    # else:
    #     print(f"FAILED! Failed to upload video to YouTube")
