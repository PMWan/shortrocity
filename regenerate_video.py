#!/usr/bin/env python3

import video
import sys
import os
import json

if __name__ == "__main__":
    basedir = sys.argv[1]
    narrations = [f for f in os.listdir(os.path.join(basedir, "narrations")) if f.endswith(".mp3")]
    caption_settings = {}
    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            caption_settings = json.load(f)
    video.create(narrations, basedir, output_filename="short.avi", caption_settings=caption_settings)
