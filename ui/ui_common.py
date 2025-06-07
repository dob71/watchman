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

# We'll need the images and config folders.
IMGDIR = f"{DATA_DIR}/{IMG_dir}"
EVTDIR = f"{DATA_DIR}/{EVT_dir}"
CFGDIR = f"{DATA_DIR}/{CFG_dir}"

# remove the DTS_* from here after restart
MODEL_INTERFACE = MODELS[DTS_label_model_if](model_to_use=DTS_label_model, api_key=os.getenv('OPENAI_API_KEY'))

# Path to the config files
imgsrc_cfg_json_path = f"{CFGDIR}/{CFG_imager}"
objects_cfg_json_path = f"{CFGDIR}/{CFG_objects}"

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
   channels = [channel[CFG_chan_id_key] for channel in sources_data[CFG_channels_key]]
   objects = [obj[CFG_obj_id_key] for obj in objects_data[CFG_obj_objects_key]]
   return channels, objects
