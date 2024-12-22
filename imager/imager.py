import os
import sys
import shutil
import requests
import json
import time
import base64
from pathlib import Path
from dotenv import load_dotenv

# Figure the path to the data folders depending on where we run
DATA_DIR = ''
if not os.path.exists('/.dockerenv'):
    load_dotenv('../.env')
    DATA_DIR = os.getenv('DATA_DIR')

# We'll need the images and config folders.
IMGDIR = f"{DATA_DIR}/images"
CFGDIR = f"{DATA_DIR}/sysconfig"

# Imager config file name
IMGR_CONFIG = f"{CFGDIR}/sources.json"

# Config dictionary
CFG={}
CFG_version_key = "version"
CFG_channels_key = 'channels'
CFG_chan_id_key = 'channel'
CFG_chan_url_key = "url"
CFG_chan_name_key = "name"
CFG_chan_upd_int_key = "upd_int"
DEF_upd_int = 2 # default update interval for channels (in seconds)

# Check config, returns None if nothing new, or new config dictionary
# if the config was updated and has to be re-applied.
def read_config():
    global CFG
    # Load JSON first into new config object, 
    # then chack the config version
    with open(IMGR_CONFIG, "r") as file:
        new_cfg = json.load(file)
    if len(new_cfg) == 0 or not CFG_version_key in new_cfg.keys():
        print(f"{sys._getframe().f_code.co_name}: malformed config, no \"{CFG_version_key}\" key found")
        return None
    if not (len(CFG) == 0 or not CFG_version_key in CFG.keys() or CFG[CFG_version_key] < new_cfg[CFG_version_key]):
        return None
    if not CFG_channels_key in new_cfg.keys():
       new_cfg[CFG_channels_key] = []
    return new_cfg

# Read and apply config if new, return False if no changes
def read_and_apply_config():
    global CFG
    new_cfg = read_config()
    if not new_cfg:
        return False
    CFG = new_cfg

    # Remove all the old image folder (if there) and create a new one for the new config
    shutil.rmtree(IMGDIR, ignore_errors=True)
    os.makedirs(IMGDIR, exist_ok=True)

    # Check and cleanup the channel entries, keep only valid ones that we are going to work with
    orig_channels = CFG[CFG_channels_key]
    CFG[CFG_channels_key] = []
    if not isinstance(orig_channels, list):
        print(f"{sys._getframe().f_code.co_name}: malformed config, \"{CFG_channels_key}\" is not a list")
        return True
    channels = []
    for idx, ch in enumerate(orig_channels):
        # Check for the required fields in the channel object
        CFG_chan_id = 'channel'
        if not CFG_chan_id_key in ch.keys():
            print(f"{sys._getframe().f_code.co_name}: malformed config, no \"{CFG_chan_id_key}\" key in channels entry {idx}")
            continue
        elif not CFG_chan_url_key in ch.keys():
            print(f"{sys._getframe().f_code.co_name}: malformed config, no \"{CFG_chan_url_key}\" key in channels entry {idx}")
            continue
        elif not CFG_chan_name_key in ch.keys():
            print(f"{sys._getframe().f_code.co_name}: malformed config, no \"{CFG_chan_name_key}\" key in channels entry {idx}")
            continue
        # Check update interval value
        if not CFG_chan_upd_int_key in ch.keys():
            ch[CFG_chan_upd_int_key] = DEF_upd_int
        try: 
            ch[CFG_chan_upd_int_key] = int(ch[CFG_chan_upd_int_key])
        except ValueError:
            print(f"{sys._getframe().f_code.co_name}: cannot convert {CFG_chan_upd_int_key} to int \"{ch[CFG_chan_upd_int_key]}\" in channels entry {idx}")
            continue
        try:
            os.mkdir(f"{IMGDIR}/{ch[CFG_chan_id_key]}")
        except:
            print(f"{sys._getframe().f_code.co_name}: unable to create \"{CFG_chan_name_key}\" key in channels entry {idx}")
            continue
        channels.append(ch)
    CFG[CFG_channels_key] = channels
    return True

# Main loop (called once a second, might be called back-to-back if blocked for too long)
def main_loop(iteration):
    global CFG
    # Pull images from channels, jasonify and put into the channel folders
    # Store a raw version for debugging/visualization purposes
    channels = CFG[CFG_channels_key]
    for idx, ch in enumerate(channels):
        chan_id = ch[CFG_chan_id_key]
        url = ch[CFG_chan_url_key]
        name = ch[CFG_chan_name_key]
        upd_int = ch[CFG_chan_upd_int_key]
        img_file = 'image.jpg' # assume JPEG, but the resolution and type should come from the config (and coversion made if necessary)
        json_file = 'image.json' # where to store image and metadata

        # Try to spread downloads over to different iterations if intervals allow that
        if (iteration + idx) % upd_int != 0:
            continue

        # Download raw
        img_file_pathname = f"{IMGDIR}/{chan_id}/{img_file}"
        response = requests.get(url, verify=False, stream=True)
        if response.status_code == 200:
            with open(img_file_pathname, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
        else:
            print(f"{sys._getframe().f_code.co_name}: error {response.status_code} fetching {ch[CFG_chan_name_key]} channel image")

        # Construct image JSON file
        json_file_pname = f"{IMGDIR}/{ch[CFG_chan_id_key]}/{json_file}"
        json_tmp_file_pname = f"{json_file_pname}.tmp"
        js = {}
        js['name'] = name # Verbal description of the channel
        js['data'] = base64.b64encode(Path(img_file_pathname).read_bytes()).decode() # Image data
        js['time'] = time.time() # will use epoch time as we will likely report differential
        js['iter'] = iteration # might be useful for tracking changes
        with open(json_tmp_file_pname, "w") as f:
            json.dump(js, f)
        # replace by atomic renaming (reqires Unix)
        try:
            os.rename(json_tmp_file_pname, json_file_pname)
        except:
            print(f"{sys._getframe().f_code.co_name}: unable to do atomic rename of {json_tmp_file_pname} to {json_file_pname}")
    return

# Run the main loop
iteration = 0
while True:
    start_time_ms = int(time.time() * 1000)
    read_and_apply_config()
    main_loop(iteration)
    iteration += 1
    end_time_ms = int(time.time() * 1000)
    if start_time_ms + 1000 > end_time_ms:
        time.sleep((start_time_ms + 1000.0 - end_time_ms) / 1000.0)

