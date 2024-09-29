import random

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
