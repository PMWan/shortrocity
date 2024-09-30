#!/usr/bin/env python3

import video
import os
import json
import argparse
import utils
import upload

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--basedir", type=str, required=True)
    parser.add_argument("--caption_settings", type=str, required=False)
    args = parser.parse_args()

    basedir = args.basedir
    narrations = [f for f in os.listdir(os.path.join(basedir, "narrations")) if f.endswith(".mp3")]
    caption_settings = {}
    if args.caption_settings:
        with open(args.caption_settings) as f:
            caption_settings = json.load(f)

    output_file = "short.avi"

    video.create(narrations, basedir, output_filename=output_file, caption_settings=caption_settings)

    print("Normalizing sound...")
    normalized_output_file = f"normalized_{output_file}"
    utils.normalize_sound(basedir, output_file, normalized_output_file)

    print(f"DONE! Here's your generated video: {os.path.join(basedir, normalized_output_file)}")

    print("Generating upload config...")
    upload_config_file = utils.generate_upload_config(basedir)

    print("Uploading video...")
    youtube = upload.get_authenticated_service()
    config = upload.load_config(upload_config_file)
    if upload.upload_video(youtube, config) is True:
        print(f"DONE! Uploaded video to YouTube")
    else:
        print(f"FAILED! Failed to upload video to YouTube")
