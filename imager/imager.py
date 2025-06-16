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
import cv2
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

# Reduce FFMPG log level to "fatal" only (otherwise it prints errors when stream rewinds)
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '8'

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
        self.img_h = ch[CFG_chan_img_h_key]
        self.img_w = ch[CFG_chan_img_w_key]
        self.img_q = ch[CFG_chan_img_q_key]
        self.rtsp_bf_retries = ch[CFG_chan_rtsp_bf_retries_key]
        self.rtsp_bf_thresh = ch[CFG_chan_rtsp_bf_thesh_key]
        self.pid = -1
        self.rtsp_cap = None
        self.iteration_file = f"{IMGDIR}/{self.chan_id}/iteration.txt"
        self.last_reported_iteration = -1
        self.idle_counter = 0

    def __del__(self):
        if self.rtsp_cap != None:
            self.rtsp_cap.release()
            self.rtsp_cap = None
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

    # process and post the image for the consumers
    def post_image(self, img, img_file_pathname):
        img_file_pathname_tmp = f"{img_file_pathname}.tmp.jpg"
        resized_img = cv2.resize(img, (self.img_w, self.img_h))
        ret = cv2.imwrite(img_file_pathname_tmp, resized_img, [cv2.IMWRITE_JPEG_QUALITY, self.img_q])
        if not ret:
            raise Exception(f"error, unable to write image to {img_file_pathname_tmp}")
        os.rename(img_file_pathname_tmp, img_file_pathname)

    # handle a file URL
    def get_file(self, url, img_file_pathname):
        src_file = url[len("file://"):]
        if not os.path.isfile(src_file):
            raise Exception(f"error, {src_file} is not a file")
        img = cv2.imread(src_file)
        if img is None:
            raise Exception(f"error, cv2.imread() failed to read {src_file}")
        self.post_image(img, img_file_pathname)

    # handle an HTTP or HTTPs URL
    def get_http(self, url, img_file_pathname):
        response = requests.get(url, verify=False, stream=True, timeout=10)
        response.raise_for_status() # Check for HTTP errors
        image_bytes = np.asarray(bytearray(response.content), dtype="uint8")
        img = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        if img is None:
            raise Exception(f"error, cv2.imdecode() failed for {url}")
        self.post_image(img, img_file_pathname)

    # Detect corrupt RTSP frames by checking for repeating rows of pixels at the bottom
    def is_frame_corrupt(self, img):
        num_pixels = img.shape[1]
        sum_diff = 0.0
        step = int(img.shape[0] / 100)
        step = step if step > 0 and step < 20 else 10
        # copare 5 rows at the bottom 10% of the image to each other
        last_row = img[-1, :]
        for i in range(1 + step, step * 6, step):
            current_row = img[-i, :]
            diff = np.sum(np.abs(last_row - current_row))
            sum_diff += diff
            last_row = current_row
        avg_diff_per_pixel = sum_diff / (num_pixels * 4)
        perc_diff = avg_diff_per_pixel / (3 * 255)
        # the corruption caused by missing some of the stream data is, typically, stretching
        # of some pattern down to the bottom of the image, that usually results in more
        # similaratities (~10% difference) between rows of pixels than the normal image
        # (50% diffrence).
        return  perc_diff < self.rtsp_bf_thresh

    # handle an RTSP URL
    def get_rtsp(self, url, img_file_pathname):
        if self.rtsp_cap == None:
            self.rtsp_cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            #self.rtsp_cap(cv2.CAP_PROP_BUFFERSIZE, 3) # might work for some backends
        if not self.rtsp_cap.isOpened():
            self.rtsp_cap.release()
            self.rtsp_cap = None
            raise Exception(f"error, RTSP cannot open {url}")
        fps = self.rtsp_cap.get(cv2.CAP_PROP_FPS)
        fps = fps if fps >= 5 and fps <= 60 else 30
        self.rtsp_cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1.0) # rewind to the end
        for ii in range(self.rtsp_bf_retries):
            time.sleep(1.0 / fps)
            ret, img = self.rtsp_cap.read()
            if not ret or img is None:
                raise Exception(f"error, RSTP cannot read from {url}")
            if not self.is_frame_corrupt(img):
                break
            print(f"retrying frame attempt {ii} fps:{fps}")
        self.post_image(img, img_file_pathname)

    # This loop runs in the child process only
    def channel_loop(self, iteration, prev_res = True):
        if iteration % self.upd_int != 0:
            return prev_res

        ch = self.ch
        chan_id = self.chan_id
        url = ch[CFG_chan_url_key]
        name = ch[CFG_chan_name_key]
        img_file = IMG_file_name # assume JPEG, but the resolution and type should come from the config (and coversion made if necessary)
        json_file = IMG_json_file_name # where to store image and metadata

        # Check if the channel is disabled by the responder due to no services being enabled on it
        off_file_pathname = f"{IMGDIR}/{chan_id}/{IMG_off_file_name}"
        if os.path.exists(off_file_pathname):
            return True

        # Write the current iteration to a file to watch for hangs
        try:
            with open(f"{self.iteration_file}.tmp", "w") as f:
                f.write(str(iteration))
            os.rename(f"{self.iteration_file}.tmp", self.iteration_file)
        except: pass

        # Download raw
        img_file_pathname = f"{IMGDIR}/{chan_id}/{img_file}"
        try:
            if url.lower().startswith("file://"):
                self.get_file(url, img_file_pathname)
            elif url.lower().startswith("http://") or url.lower().startswith("https://"):
                self.get_http(url, img_file_pathname)
            elif url.lower().startswith("rtsp://"):
                self.get_rtsp(url, img_file_pathname)
            else:
                raise Exception(f"error, unable to handle {url}")

        except Exception as e:
            print(f"{sys._getframe().f_code.co_name}: {e}")
            return False

        # Make sure we downloaded an image
        file_type = imghdr.what(img_file_pathname)
        if not file_type in ['gif', 'jpeg', 'png', 'webp']: # for now just pass through what LLAMA 3.2 Vision supports
            print(f"{sys._getframe().f_code.co_name}: only 'gif', 'jpeg', 'png' and 'webp' are allowed, got '{file_type}' from {url}")
            return False

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
        res = json_atomic_write(js, json_tmp_file_pname, json_file_pname)

        if res and not prev_res:
            print(f"{ch[CFG_chan_name_key]}: recovered from error")
        return res

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
        prev_res = True # assume success when starting
        while True:
            start_time_ms = int(time.time() * 1000)
            prev_res = self.channel_loop(iteration, prev_res)
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
    # Set some defaults if the config is missing the relevant optional keys
    for ch in new_cfg[CFG_channels_key]:
        ch[CFG_chan_img_h_key] = ch.get(CFG_chan_img_h_key, 720)
        ch[CFG_chan_img_w_key] = ch.get(CFG_chan_img_w_key, 1280)
        ch[CFG_chan_img_q_key] = ch.get(CFG_chan_img_q_key, 50)
        ch[CFG_chan_rtsp_bf_retries_key] = ch.get(CFG_chan_rtsp_bf_retries_key, 5)
        ch[CFG_chan_rtsp_bf_thesh_key] = ch.get(CFG_chan_rtsp_bf_thesh_key, 0.20)

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
        else:
            try:
                with open(c_runner.iteration_file, "r") as f:
                    iteration = int(f.read().strip())
            except: iteration = 0
            if c_runner.last_reported_iteration == iteration:
                c_runner.idle_counter += 1
                if c_runner.idle_counter > 30: # give it 30sec max
                    print(f"{sys._getframe().f_code.co_name}: imager thread for {chan_id} hung, terminating...")
                    del c_runner
                    CRUN[chan_id] = ChannelDownloadRunner(ch)
            else:
                c_runner.idle_counter = 0
                c_runner.last_reported_iteration = iteration
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
