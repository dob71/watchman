import os
import sys
import json

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("./orchestrator"))

from shared_settings import *
from model_interfaces import *

# Figure the path to the data folders depending on where we run
DATA_DIR = ''
if not os.path.exists('/.dockerenv'):
    from dotenv import load_dotenv
    load_dotenv('./.env')
DATA_DIR = os.getenv('DATA_DIR', DATA_DIR)
IPC_DIR = os.getenv('IPC_DIR', '.ipc')

# We'll need the images and config folders.
IMGDIR = f"{IPC_DIR}/{IMG_dir}"
EVTDIR = f"{IPC_DIR}/{EVT_dir}"
CFGDIR = f"{DATA_DIR}/{CFG_dir}"

# Model configuration
CFG_model = 'model.json'         # tmp, remove later

# Path to the config files
imgsrc_cfg_json_path = f"{CFGDIR}/{CFG_imager}"
objects_cfg_json_path = f"{CFGDIR}/{CFG_objects}"
model_cfg_json_path = f"{CFGDIR}/{CFG_model}"

# Training data pickle file location
pcl_train_data_path = f"{DATA_DIR}/{CFG_dset_svc_name}/{DTS_train_data_file}"

# Constants for boolean selectors
boolean_selection = [True, False]

# Load JSON file
def load_data(file_path):
   with open(file_path, "r") as file:
       data = json.load(file)
   return data

# Extract channel ids and object ids from JSON files
def extract_ids(sources_data, objects_data):
   channels = [channel[CFG_chan_id_key] for channel in sources_data.get(CFG_channels_key, [])]
   objects = [obj[CFG_obj_id_key] for obj in objects_data.get(CFG_obj_objects_key, [])]
   return channels, objects

# Get channel name from ID
def chan_id_to_name(sources_data, c):
    for channel in sources_data.get(CFG_channels_key, []):
        if channel.get(CFG_chan_id_key) == c:
            return channel.get(CFG_chan_name_key, c)
    return c

# Get object name from ID
def obj_id_to_name(objects_data, o):
    for obj in objects_data.get(CFG_obj_objects_key, []):
        if obj.get(CFG_obj_id_key) == o:
            names = obj.get(CFG_obj_names_key, [])
            return names[0] if names else o
    return o
