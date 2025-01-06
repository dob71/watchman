# Pulls images from the channels. It forks creating aa separate process for
# each properly configured channel. Requires a unix system.
import os
import sys
import shutil
import requests
import json
import time
import base64
import signal
import imghdr
from pathlib import Path
from dotenv import load_dotenv

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))
from shared_settings import *

# Figure the path to the data folders depending on where we run
DATA_DIR = ''
if not os.path.exists('/.dockerenv'):
    load_dotenv('./.env')
DATA_DIR = os.getenv('DATA_DIR', DATA_DIR)

# We'll need the images and config folders.
IMGDIR = f"{DATA_DIR}/{IMG_dir}"
CFGDIR = f"{DATA_DIR}/{CFG_dir}"

# Imager config file name
IMGR_CONFIG = f"{CFGDIR}/{CFG_imager}"

# Config dictionary
CFG = {}
# Channel runners (instances of ChannelDownloadRunner)
CRUN = {}
# Am I the manager process?
MANAGER = True

# Check if the process with a given pid is running (assumes the caller can send signal to the process)
def is_pid_running(pid):
    if pid <= 0:
        return False
    if pid > 0:
        try:
            os.kill(pid, 0)
        except:
            return False
    return True

# write json to a file using atomic rename
def json_atomic_write(js, json_tmp_file_pname, json_file_pname):
    res = False
    try:
        with open(json_tmp_file_pname, "w") as f:
            json.dump(js, f)
        try:
            os.rename(json_tmp_file_pname, json_file_pname)
            res = True
        except:
            print(f"{sys._getframe().f_code.co_name}: unable to do atomic rename of {json_tmp_file_pname} to {json_file_pname}")
    except:
        print(f"{sys._getframe().f_code.co_name}: unable to write {json_tmp_file_pname}")
    return res

# Class for handling the image retrieval work for individual channels (forks when run)
class ChannelDownloadRunner:
    def __init__(self, ch):
        self.ch = ch
        self.chan_id = ch[CFG_chan_id_key]
        self.upd_int = ch[CFG_chan_upd_int_key]
        self.pid = -1        

    def __del__(self):
        if MANAGER and self.pid > 0 and is_pid_running(self.pid):
            os.kill(self.pid, signal.SIGTERM)
            for i in range(10):
                _, status = os.waitpid(self.pid, os.WNOHANG)
                if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                    self.pid = -1
                    break    
                time.sleep(0.5)
            if self.pid > 0:
                os.kill(self.pid, signal.SIGKILL)
                self.pid = -1

    # Check if the instance process is running
    def is_running(self):
        if self.pid > 0:
            return is_pid_running(self.pid)
        if self.pid < 0:
            return False
        return True # must be the instance running in its own process

    # Handle sigterm signal for the channel image downloader process
    @staticmethod
    def signal_handler(signum, frame):
        print(f"Received SIGTERM, exiting downloader with pid: {os.getpid()}")
        exit(0)

    # This loop runs in the child process only (no return)
    def channel_loop(self, iteration):
        if iteration % self.upd_int != 0:
            return

        ch = self.ch
        chan_id = self.chan_id
        url = ch[CFG_chan_url_key]
        name = ch[CFG_chan_name_key]
        img_file = IMG_file_name # assume JPEG, but the resolution and type should come from the config (and coversion made if necessary)
        json_file = IMG_json_file_name # where to store image and metadata

        # Check if the channel is disabled by the responder due to no services being enabled on it
        off_file_pathname = f"{IMGDIR}/{chan_id}/{IMG_off_file_name}"
        if os.path.exists(off_file_pathname):
            return

        # Download raw
        img_file_pathname = f"{IMGDIR}/{chan_id}/{img_file}"
        try:
            if url.lower().startswith("file://"):
                src_file = url[len("file://"):]
                if os.path.isfile(src_file):
                    shutil.copyfile(src_file, img_file_pathname)
                else:
                    print(f"{sys._getframe().f_code.co_name}: error, {src_file} is not a file")
                    return
            else:
                response = requests.get(url, verify=False, stream=True)
                if response.status_code == 200:
                    with open(img_file_pathname, "wb") as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                else:
                    print(f"{sys._getframe().f_code.co_name}: error {response.status_code} fetching {ch[CFG_chan_name_key]} channel image")
                    return
        except:
            print(f"{sys._getframe().f_code.co_name}: error loading image from {url}")
            return

        # Make sure we downloaded an image
        file_type = imghdr.what(img_file_pathname)
        if not file_type in ['gif', 'jpeg', 'png', 'webp']: # for now just pass through what LLAMA 3.2 Vision supports
            print(f"{sys._getframe().f_code.co_name}: only 'gif', 'jpeg', 'png' and 'webp' are allowed, got '{file_type}' from {url}")
            return

        # Construct image JSON file
        json_file_pname = f"{IMGDIR}/{ch[CFG_chan_id_key]}/{json_file}"
        json_tmp_file_pname = f"{json_file_pname}.tmp"
        js = {}
        js[IMG_chan_key] = chan_id # Channel ID from channel config
        js[IMG_name_key] = name # Verbal description of the channel
        js[IMG_data_key] = base64.b64encode(Path(img_file_pathname).read_bytes()).decode() # Image data
        js[IMG_time_key] = time.time() # will use epoch time as we will likely report differential
        js[IMG_iter_key] = iteration # might be useful for tracking changes
        # write file and replace by atomic renaming (requires Unix)
        json_atomic_write(js, json_tmp_file_pname, json_file_pname)

    def run(self, iteration):
        global MANAGER
        self.pid = os.fork()
        if self.pid < 0:
            print(f"{sys._getframe().f_code.co_name}: received SIGTERM, exiting downloader {os.getpid()}")
            return False
        if self.pid > 0:
            return True
        # the below will run in the child process only        
        MANAGER = False # record that we are the runner (so we do not try to cleanup when terminating)
        signal.signal(signal.SIGTERM, ChannelDownloadRunner.signal_handler)
        print(f"Started downloader for channel: {self.chan_id}, pid: {os.getpid()}")
        while True:
            start_time_ms = int(time.time() * 1000)
            self.channel_loop(iteration)
            iteration += 1
            end_time_ms = int(time.time() * 1000)
            if start_time_ms + IMG_poll_int_ms > end_time_ms:
                time.sleep((start_time_ms + IMG_poll_int_ms - end_time_ms) / 1000.0)

# Check config, returns None if nothing new, or returns the new config dictionary
# if the config was updated and has to be re-applied.
def read_config():
    global CFG

    # Load JSON first into new config object, 
    # then chack the config version
    try:
        with open(IMGR_CONFIG, "r") as file:
            new_cfg = json.load(file)
    except json.JSONDecodeError as e:
        print(f"{sys._getframe().f_code.co_name}: file {IMGR_CONFIG}, JSON error on line {e.lineno}: {e.msg}")
        return None
    except Exception as e:
        print(f"{sys._getframe().f_code.co_name}: file {IMGR_CONFIG}, Failed to load JSON file:", e)
        return None
    if len(new_cfg) == 0 or not CFG_version_key in new_cfg.keys():
        print(f"{sys._getframe().f_code.co_name}: malformed config, no \"{CFG_version_key}\" key found")
        return None

    if len(CFG) != 0 and CFG_version_key in CFG.keys() and CFG[CFG_version_key] >= new_cfg[CFG_version_key]:
        return None
    if not CFG_channels_key in new_cfg.keys():
       new_cfg[CFG_channels_key] = []
    return new_cfg

# Read and apply config if new, return False if no changes
def read_and_apply_config():
    global CFG
    global CRUN

    new_cfg = read_config()
    if not new_cfg:
        return False
    CFG = new_cfg

    # Destroy the runner instances (kills all the downloader processes)
    for c_runner in CRUN:
        del c_runner

    # Remove all the old image folder (if there) and create a new empty one for the new config
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
            ch[CFG_chan_upd_int_key] = CFG_DEF_upd_int
        try: 
            ch[CFG_chan_upd_int_key] = int(ch[CFG_chan_upd_int_key])
        except ValueError:
            print(f"{sys._getframe().f_code.co_name}: cannot convert {CFG_chan_upd_int_key} to int \"{ch[CFG_chan_upd_int_key]}\" in channels entry {idx}")
            continue
        chan_id = ch[CFG_chan_id_key]
        try:
            os.mkdir(f"{IMGDIR}/{chan_id}")
        except:
            print(f"{sys._getframe().f_code.co_name}: unable to create \"{IMGDIR}/{chan_id}\" folder")
            continue
        CRUN[chan_id] = ChannelDownloadRunner(ch)
        channels.append(ch)

    CFG[CFG_channels_key] = channels
    return True

# Main loop (see below, called once in IMG_poll_int_ms)
def main_loop(iteration):
    global CFG
    global CRUN
    # Pull images from channels, jasonify and put into the channel folders
    # Store a raw version for debugging/visualization purposes
    if CFG_channels_key not in CFG:
        return
    channels = CFG[CFG_channels_key]
    for idx, ch in enumerate(channels):
        chan_id = ch[CFG_chan_id_key]
        c_runner = CRUN[chan_id]
        if not c_runner.is_running():
            c_runner.run(iteration + idx) # offset iteration by idx to help spread downloads
    return

# Run the main loop. It's responsible for watching sources config file, loading it,
# then kicking off and monitoring the individual channel image downloader loops.
iteration = 0
while True:
    start_time_ms = int(time.time() * 1000)
    read_and_apply_config()
    main_loop(iteration)
    iteration += 1
    end_time_ms = int(time.time() * 1000)
    if start_time_ms + IMG_poll_int_ms > end_time_ms:
        time.sleep((start_time_ms + IMG_poll_int_ms - end_time_ms) / 1000.0)
