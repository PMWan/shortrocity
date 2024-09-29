import random
import subprocess
import os


def pick_random_animal(file_path):
    selected_animal = None
    count = 0

    # Open the file and iterate through each line
    with open(file_path, 'r') as file:
        for line in file:
            count += 1
            # Replace the currently selected animal with probability 1/count
            if random.randint(1, count) == 1:
                selected_animal = line.strip()

    return selected_animal


def normalize_sound(basedir, input_file, output_file):
    input_file_path = os.path.join(basedir, input_file)
    output_file_path = os.path.join(basedir, output_file)

    ffmpeg_command = [
        'ffmpeg',
        '-i', input_file_path,
        '-c:v', 'copy',
        '-af', 'loudnorm=I=-14:TP=-2:LRA=11',
        output_file_path
    ]

    subprocess.run(ffmpeg_command, capture_output=True)

    os.remove(input_file_path)


def generate_upload_config(basedir):
    from openai import OpenAI
    import json

    client = OpenAI()
    with open(os.path.join(basedir, "response.txt"), 'r') as file:
        script = file.read()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that generates catchy YouTube short titles and descriptions."
            },
            {
                "role": "user",
                "content": f"Please generate a catchy title and description for the following youtube short script: {script}. "
                "Include relevant emojis at the end of the title and description. "
                "Return the title and description as valid JSON."
            }
        ],
        response_format={ "type": "json_object" }
    )

    response_text = response.choices[0].message.content

    # Use json.loads() to parse the response into a Python dict
    try:
        config = json.loads(response_text)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        # You may need to clean or correct the response to extract valid JSON

    print(config)

    config["file_path"] = os.path.join(basedir, "normalized_short.avi")
    config["category"] = "15"
    config["privacy_status"] = "private"

    with open(os.path.join(basedir, "upload_config.json"), "w") as f:
        json.dump(config, f)

    return os.path.join(basedir, "upload_config.json")
