"""
Created on Aug 28, 2018

@author: ionut
"""

import logging

logging.basicConfig(level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S",
                    format="[%(asctime)s] - %(levelname)s - %(message)s")

ADDRESS = "127.0.0.1"
PORT = 9000
TEMPLATE_PATH = "templates"
STATIC_PATH = "static"

CAMERA = {
    "width": 1312,
    "height": 736,
    "framerate": 24,
    "vflip": False,
    "hflip": False
}
