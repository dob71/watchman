# This is a debugging/development tool for the project.
# It's purpose it to collect a large number of the images 
# captured by the imager for evaluating the model objects 
# detection capabilities. 
# Warning: it's the image consumer, do not run at the same time
#          with the orchestrator script.
import os
import sys
import time
import json
import base64
from pathlib import Path
from dotenv import load_dotenv

# Pull in shared variables (file names, JSON object names, ...)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from shared_settings import *

# Figure the path to the data folders depending on where we run
DATA_DIR = ''
if not os.path.exists('/.dockerenv'):
    load_dotenv('./.env')
    DATA_DIR = os.getenv('DATA_DIR')

# We'll need the images and config folders.
IMGDIR = f"{DATA_DIR}/{IMG_dir}"

# Will also need some location where to keep the archive
DATASET_DIR = f"{DATA_DIR}/dataset"

# Atomic rename and load of the image data
def read_image_json(img_json_fname):
    img_json_tmp_fname = img_json_fname + ".rd.tmp"
    if not os.path.exists(img_json_fname):
        return None
    try:
        os.rename(img_json_fname, img_json_tmp_fname)
    except:
        print(f"{sys._getframe().f_code.co_name}: unable to do atomic rename of {img_json_fname} to {img_json_tmp_fname}")
        return None
    try:
        with open(img_json_tmp_fname, "r") as file:
            js = json.load(file)
    except json.JSONDecodeError as e:
        print(f"{sys._getframe().f_code.co_name}: file {img_json_tmp_fname}, JSON error on line {e.lineno}: {e.msg}")
        return None
    except Exception as e:
        print(f"{sys._getframe().f_code.co_name}: file {img_json_tmp_fname}, Failed to load JSON file:", e)
        return None
    if len(js) == 0:
        print(f"{sys._getframe().f_code.co_name}: no data in {img_json_fname}")
        return None
    return js

# Main loop (called w/ some fraction of the IMG_poll_int_ms frequency)
def main_loop(iteration):
    # Loop over the channel folders 
    for chan in os.listdir(IMGDIR):
        chan_dir = f"{IMGDIR}/{chan}"
        if chan.startswith('.') or not os.path.isdir(chan_dir):
            continue
        img_json_fname = f"{chan_dir}/image.json"
        js = read_image_json(img_json_fname)
        if js is None:
            continue

        chan_id = js[IMG_chan_key]
        #name = js[IMG_name_key]
        data = base64.b64decode(js[IMG_data_key])
        #epoch_sec = js[IMG_time_key]
        img_iter = js[IMG_iter_key]

        # If capturing every 3sec, 20/min, 1200/hour, 28800/24h
        # ~50KB each 1440000KB, ~1.3GB per each channel
        dst_file_dir = f"{DATASET_DIR}/{chan_id}"
        dst_file = f"{dst_file_dir}/{img_iter:05}.jpg"
        os.makedirs(dst_file_dir, exist_ok=True)
        Path(dst_file).write_bytes(data)
    return

# Run the main loop
iteration = 0
loop_interval = int(IMG_poll_int_ms / 1)
while True:
    start_time_ms = int(time.time() * 1000)
    main_loop(iteration)
    iteration += 1
    end_time_ms = int(time.time() * 1000)
    if start_time_ms + loop_interval > end_time_ms:
        time.sleep((start_time_ms + loop_interval - end_time_ms) / 1000.0)
