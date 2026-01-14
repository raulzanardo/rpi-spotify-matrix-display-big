import os
import inspect
import sys
import math
import time
import configparser
import argparse
import warnings
from PIL import Image

from apps_v2 import spotify_player
from modules import spotify_module


def main():
    canvas_width = 192
    canvas_height = 128

    # get arguments
    parser = argparse.ArgumentParser(
        prog='RpiSpotifyMatrixDisplay',
        description='Displays album art of currently playing song on an LED matrix')

    parser.add_argument('-f', '--fullscreen', action='store_true',
                        help='Always display album art in fullscreen')
    args = parser.parse_args()

    is_full_screen_always = args.fullscreen

    # get config
    currentdir = os.path.dirname(os.path.abspath(
        inspect.getfile(inspect.currentframe())))
    sys.path.append(currentdir+"/rpi-rgb-led-matrix/bindings/python")

    # import rgbmatrix bindings after adding to path
    from rgbmatrix import RGBMatrix, RGBMatrixOptions

    config = configparser.ConfigParser()
    parsed_configs = config.read('../config.ini')

    if len(parsed_configs) == 0:
        print("no config file found")
        sys.exit()

    # connect to Spotify and create display image
    modules = {'spotify': spotify_module.SpotifyModule(config)}
    app_list = [spotify_player.SpotifyScreen(
        config, modules, is_full_screen_always, canvas_width, canvas_height)]

    # setup matrix
    options = RGBMatrixOptions()
    options.hardware_mapping = config.get(
        'Matrix', 'hardware_mapping', fallback='regular')
    # Use panel configuration from config.ini — rows must be <=64
    options.rows = config.getint('Matrix', 'rows', fallback=64)
    options.cols = config.getint('Matrix', 'cols', fallback=64)
    options.chain_length = config.getint('Matrix', 'chain_length', fallback=1)
    options.parallel = config.getint('Matrix', 'parallel', fallback=1)
    options.brightness = config.getint('Matrix', 'brightness', fallback=100)
    options.gpio_slowdown = config.getint(
        'Matrix', 'gpio_slowdown', fallback=1)
    options.limit_refresh_rate_hz = config.getint(
        'Matrix', 'limit_refresh_rate_hz', fallback=0)
    options.drop_privileges = False
    matrix = RGBMatrix(options=options)

    shutdown_delay = config.getint('Matrix', 'shutdown_delay', fallback=600)
    black_screen = Image.new("RGB", (canvas_width, canvas_height), (0, 0, 0))
    last_active_time = math.floor(time.time())

    # generate image
    while (True):
        frame, is_playing = app_list[0].generate()
        current_time = math.floor(time.time())

        if frame is not None:
            if is_playing:
                last_active_time = math.floor(time.time())
            elif current_time - last_active_time >= shutdown_delay:
                frame = black_screen
        else:
            frame = black_screen

        matrix.SetImage(frame)
        time.sleep(0.08)


if __name__ == '__main__':
    try:
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        main()
    except KeyboardInterrupt:
        print('Interrupted with Ctrl-C')
        sys.exit(0)
