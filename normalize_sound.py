import utils
import sys

if __name__ == "__main__":
    basedir = sys.argv[1]  # path to the shorts directory containing the video file
    utils.normalize_sound(basedir, "short.avi", "normalized_short.avi")
