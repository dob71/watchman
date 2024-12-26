# Orchestrator reads the objects of interest configuration,
# collects the images from the imager channel folders, and
# calls the LLM module to locate each obect location on each
# image. For each Watchman service configured for the object
# the verbal message is generated from the config template
# and saved along w/ the other service event info in files
# under the events folder.
# For now, it's single threaded, but for performance it has
# to run a thread or fork for each image source channel.
import os
import sys
import time
import re
import json
import base64
import shutil
from pathlib import Path
from dotenv import load_dotenv
from jsonschema import validate

# Pull in shared variables (file names, JSON object names, ...) and the the model interface classes
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))
from shared_settings import *
from model_interfaces import *

# Figure the path to the data folders depending on where we run
DATA_DIR = ''
if not os.path.exists('/.dockerenv'):
    load_dotenv('./.env')
    DATA_DIR = os.getenv('DATA_DIR')

# We'll need the images and config folders.
CFGDIR = f"{DATA_DIR}/{CFG_dir}"
IMGDIR = f"{DATA_DIR}/{IMG_dir}"
EVTDIR = f"{DATA_DIR}/{EVT_dir}"

# Objects of interest config file name
OBJ_CONFIG = f"{CFGDIR}/{CFG_objects}"

# Config dictionary
CFG = {}
# Channel runners dictionary (instances of ChannelOrchestrator, keyed by channel ID)
CRUN = {}
# Model interface class instance for communicating w/ the configured ML model
MODEL = None

# Write json to a file using atomic rename
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

# Gets the number of seconds since the file was last modified (-1 if error)
def get_modified_time_ago(filepath):
    try: 
        modification_time = os.path.getmtime(filepath)
        current_time = time.time()
        time_difference = current_time - modification_time
    except:
        time_difference = -1
    return time_difference

# Check config, returns None if nothing new, or new config dictionary
# if the config was updated and has to be re-applied.
def read_config():
    global CFG
    # Load JSON first into new config object, 
    # then chack the config version
    try:
        with open(OBJ_CONFIG, "r") as file:
            new_cfg = json.load(file)
    except json.JSONDecodeError as e:
        print(f"{sys._getframe().f_code.co_name}: file {OBJ_CONFIG}, JSON error on line {e.lineno}: {e.msg}")
        return None
    except Exception as e:
        print(f"{sys._getframe().f_code.co_name}: file {OBJ_CONFIG}, Failed to load JSON file:", e)
        return None
    if len(new_cfg) == 0 or not CFG_obj_version_key in new_cfg.keys():
        print(f"{sys._getframe().f_code.co_name}: malformed config, no \"{CFG_obj_version_key}\" key found")
        return None
    if len(CFG) != 0 and CFG_obj_version_key in CFG.keys() and CFG[CFG_obj_version_key] >= new_cfg[CFG_obj_version_key]:
        return None
    if not CFG_obj_objects_key in new_cfg.keys():
       new_cfg[CFG_channels_key] = []
    return new_cfg

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

# Read and apply objects of iterest config if new or changed. Do nothing and return False if no changes.
# If config changed, re-instantiate the ML model interface, remove all the existent entries in the events
# folder, and destroy all the ChannelOrchestrator instances, then update the global CFG dictionary and
# return True.
def read_and_apply_config():
    global CFG
    global CRUN
    global MODEL
    global MODELS

    new_cfg = read_config()
    if not new_cfg:
        return False
    for c_runner in CRUN:
        del c_runner # TBD: channel runners should run in individual threads or processes
    CRUN = {}
    CFG = new_cfg

    # Remove all the old events folder (if there) and create a new one for the new config
    shutil.rmtree(EVTDIR, ignore_errors=True)
    os.makedirs(EVTDIR, exist_ok=True)

    # Some sanity checking and defaults handling for top level config keys
    if not CFG_obj_model_key in CFG.keys():
        CFG[CFG_obj_model_key] = 'ollama-simple'
    if not MODEL is None:
        del MODEL
    if CFG[CFG_obj_model_key] in MODELS.keys():
        MODEL = MODELS[CFG[CFG_obj_model_key]]()
    else: # no matching model interface, can't do anything
        print(f"{sys._getframe().f_code.co_name}: no \"{CFG[CFG_obj_model_key]}\" model interface found")
        CFG[CFG_obj_objects_key] = []
        return True

    if not CFG_obj_objects_key in CFG.keys() or not isinstance(CFG[CFG_obj_objects_key], list):
        CFG[CFG_obj_objects_key] = []
        return True
    
    orig_objects = CFG[CFG_obj_objects_key]
    objects = []
    for idx, o in enumerate(orig_objects):
        try:
            validate(instance=o, schema=CFG_obj_schema)
            objects.append(o)
        except Exception as e:
            print(f"{sys._getframe().f_code.co_name}: error in JSON for object {idx}: {e}")
    CFG[CFG_obj_objects_key] = objects
    return True

class ChannelOrchestrator:
    def __init__(self, chan):
        self.chan = chan

    # Read image data from the channel, return True if successful
    def read_image_data(self):
        chan = self.chan
        chan_dir = f"{IMGDIR}/{chan}"
        img_json_fname = f"{chan_dir}/{IMG_json_file_name}"
        image_js = read_image_json(img_json_fname)
        if image_js is None:
            return False
        # Get image data
        try:
            self.chan_id = image_js[IMG_chan_key]
            self.chan_name = image_js[IMG_name_key]
            self.img_data = base64.b64decode(image_js[IMG_data_key])
            self.img_time = image_js[IMG_time_key]
            self.img_iter = image_js[IMG_iter_key]
        except:
            print(f"{sys._getframe().f_code.co_name}: malformed {img_json_fname}")
            return False
        return True

    # All the info is collected and ready, generate the service data files.
    def loop_run_update(self, obj_js, e_list):
        obj_id = obj_js[EVT_obj_id_key]
        obj_dir =  f"{EVTDIR}/{self.chan}/{obj_id}"
        for e in e_list:
            # For debugging, and fine tuning it migh tbe useful to capture the image
            # that triggered the event.
            if EVT_img_data in e.keys():
                obj_svc_img_file = f"{obj_dir}/{e[EVT_osvc_key]}.jpg"
                Path(obj_svc_img_file).write_bytes(e[EVT_img_data])
                del e[EVT_img_data] # Note: already decoded, don't try to save in JSON
            # Make the event JSON file
            obj_svc_file = f"{obj_dir}/{e[EVT_osvc_key]}.json"
            obj_svc_tmp_file = f"{obj_svc_file}.tmp"
            json_atomic_write(e, obj_svc_tmp_file, obj_svc_file)
        return e_list

    # Run detection on one of the objects in the channel image, and generate messages for reporting
    def loop_run_inference(self, obj_js, e_list):
        if MODEL is None:
            return []
        obj_name = obj_js[EVT_obj_names_key][0]
        obj_desc = obj_js[EVT_obj_desc_key]
        # technically, it makes sense to have processing tuned for each service, but for efficiency
        # we do inference for the object described by obj_desc once, then use message templates to
        # tweak the results to the purpose of the specific service.
        res, loc_msg = MODEL.locate(self.img_data, obj_desc, self.chan_name)
        if not res:
            return [] # object is not on the image or no result
        # update event services objects w/ the inference data
        for e in e_list:
            e[EVT_in_time_key] = time.time()
            d = {'LOCATION': loc_msg, 'CHANNEL': self.chan_name, 'OBJNAME': obj_name}
            msg = re.sub(r'\[([^\]]*)\]', lambda x:d.get(x.group(1)) if x.group(1) in d.keys() else f"[{x.group(1)}]", e[EVT_msg_key])
            e[EVT_msg_key] = msg
            e[EVT_img_data] = self.img_data
        return e_list

    # Prepare object events folder and handle service files
    def loop_run_handle_object(self, o):
        obj_id = o[CFG_obj_id_key]
        obj_names = o[CFG_obj_names_key]
        obj_desc = o[CFG_obj_desc_key]
        obj_svcs = o[CFG_obj_svcs_key]
        # prep object of interest event info json
        obj_js = {
            EVT_obj_id_key: obj_id,
            EVT_obj_names_key: obj_names,
            EVT_obj_desc_key: obj_desc,
        }
        # Object events directory
        obj_dir =  f"{EVTDIR}/{self.chan}/{obj_id}"
        obj_file = f"{obj_dir}/{EVT_obj_file_name}"
        init_obj_folder = False
        if not os.path.exists(obj_file):
            os.makedirs(obj_dir, exist_ok=True)
            # Create obect json file for the folder
            if not json_atomic_write(obj_js, f"{obj_file}.tmp", obj_file):
                return obj_js, [] # Do not process anything until we can create the proper file tree
            init_obj_folder = True
        # For new folder need to populate the folder w/ <svc>.off files for CFG_osvc_def_off_key option
        if init_obj_folder:
            for s in obj_svcs:
                if s[CFG_osvc_def_off_key]:
                    obj_svc_off_file = f"{obj_dir}/{s[CFG_osvc_name_key]}.off"
                    open(obj_svc_off_file, 'w').close()
        # Handle skipping channels, ageing out and turning off services. Create event list to work with.
        e_list = []
        for s in obj_svcs:
            obj_svc_file = f"{obj_dir}/{s[CFG_osvc_name_key]}.json"
            obj_svc_off_file = f"{obj_dir}/{s[CFG_osvc_name_key]}.off"
            skip_chan_list = [] if not CFG_osvc_skip_chan_key in s.keys() else s[CFG_osvc_skip_chan_key]
            if os.path.exists(obj_svc_off_file) or self.chan_id in skip_chan_list:
                try: os.unlink(obj_svc_file)
                except: pass
                continue
            if get_modified_time_ago(obj_svc_file) >= s[CFG_osvc_age_out_key]:
                try: os.unlink(obj_svc_file)
                except: pass
            evt = {
                EVT_osvc_key: s[CFG_osvc_name_key],
                EVT_c_name_key: self.chan_name,
                EVT_in_time_key: 0, # populated after inference
                EVT_msg_key: s[CFG_osvc_msgtpl_key], # putting template here for now
                EVT_alrt_mute_time_key: 0 if not CFG_osvc_mtime_key in s.keys() else s[CFG_osvc_mtime_key]
            }
            e_list.append(evt)
        return obj_js, e_list

    # Handle channel (called from main loop to process each channel),
    # it should run in its own thread or process eventually
    def loop_run(self):
        global CFG
        # read image JSON
        if not self.read_image_data():
            return
        # get list of objects to go over (conformity to schema already verified)
        objects = CFG[CFG_obj_objects_key]
        # Go over the objects of interest, ask ML model about them in the image
        # and if discovered anything interesting update the event files
        for o in objects:
            obj_js, e_list = self.loop_run_handle_object(o)
            if len(e_list) == 0:
                continue
            e_list = self.loop_run_inference(obj_js, e_list)
            if len(e_list) == 0:
                continue
            self.loop_run_update(obj_js, e_list)
        return

# Main loop (called w/ ORCH_poll_int_ms interval)
def main_loop(iteration):
    # Make the lists of input (imager) and output (events) channels
    img_chans = list(filter(lambda x : not x.startswith('.'), os.listdir(IMGDIR)))
    evt_chans = list(filter(lambda x : not x.startswith('.'), os.listdir(EVTDIR)))
    # Remove event channels that are no longer present in sources
    for ch in evt_chans:
        if ch not in img_chans:
            crun_ch_ids = CRUN.keys()
            if ch in crun_ch_ids:
                del CRUN[ch]
            shutil.rmtree(f"{EVTDIR}/{ch}", ignore_errors=True)

    # Read objects of interest config, if new, remove all the existent event entries
    # and ChannelOrchestrator instances
    read_and_apply_config()

    # Note, that there might be problems with racing conditions between channel updates
    #       propagating through the imager and the objects config read here. They have
    #       to be decoupled as much as possible. 

    # Loop over the channel folders we need to process
    crun_ch_ids = CRUN.keys()
    for ch in img_chans:
        if not ch in crun_ch_ids:
            CRUN[ch] = ChannelOrchestrator(ch)
        co = CRUN[ch]
        co.loop_run()
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
