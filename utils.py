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
