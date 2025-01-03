import streamlit as st
import numpy as np
import time

from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import speech_to_text

import json
import os
import shutil
import sys

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))

from dotenv import load_dotenv
from shared_settings import *

# Figure the path to the data folders depending on where we run
DATA_DIR = ''
if not os.path.exists('/.dockerenv'):
    load_dotenv('./.env')
    DATA_DIR = os.getenv('DATA_DIR')

# We'll need the images and config folders.
IMGDIR = f"{DATA_DIR}/{IMG_dir}"
CFGDIR = f"{DATA_DIR}/{CFG_dir}"


# Path of sources.json and objects.json
imager_sources_json_path = f"{CFGDIR}/sources.json"
imager_objects_json_path = f"{CFGDIR}/objects.json"

# Streamlit widgets automatically run the script from top to bottom. 

# Supported classes of objects
# TODO: pick the classes that we want to support in object detection
obj_ids_selection = [
   "cat",
   "person",
   "deer",
]

# Supported models
models_selection = [
    "ollama-simple",
    "ollama-complex"
]

boolean_selection = [True, False]

# Create sources.json file
def output_sources_json(channel_input, name_input, url_input, slider_input, new_version):
    channels = list()
    for i in range(len(channel_input)):
        channels.append(
            {
                "channel": channel_input[i],
                "name": name_input[i],
                "url": url_input[i],
                "upd_int": slider_input[i]
            }
        )

    # Define the final JSON structure
    output = {
        "version": new_version,
        "channels": channels
    }

    # Convert the structure to a JSON string
    output_json = json.dumps(output, indent=4)

    # Save the JSON output to a file
    with open(imager_sources_json_path, "w") as file:
        file.write(output_json)

    # Print the JSON output
    print(output_json)

# Read sources.json to pre-populate the values in the input boxes
# Return the number of channels which is determined by the number of entries in sources.json and the current version number.
def read_sources_json(channel_input, name_input, url_input, slider_input):
    if not os.path.exists(imager_sources_json_path):
        # Provide hypothetical defaults when sources.json does not exist
        for i in range(2):
            channel_input.append(str(i))
            name_input.append(f"channel-{i}")
            url_input.append(f"http://my.webcam.com/webcam-{i}.jpg")
            slider_input.append(3)
        version = 1
    else:
        with open(imager_sources_json_path, "r") as file:
            data = json.load(file)

            # Populate the lists
            for channel in data['channels']:
                channel_input.append(channel['channel'])
                name_input.append(channel['name'])
                url_input.append(channel['url'])
                slider_input.append(channel['upd_int'])
            
            version = data['version']
    
    return (len(channel_input), version)

# Create objects.json file
def output_objects_json(obj_id_input, obj_names_input, desc_input, obj_svcs_input, model, new_version):
    objects = list()
    for i in range(len(obj_id_input)):
        objects.append(
            {
                "obj_id": obj_id_input[i],
                "names": [x.strip() for x in obj_names_input[i].split(',')],
                "desc": desc_input[i],
                "obj_svcs": list(obj_svcs_input[i].values())
            }
        )

    # Define the final JSON structure
    output = {
        "version": new_version,
        "model": model[0],
        "objects": objects
    }

    # Convert the structure to a JSON string
    output_json = json.dumps(output, indent=4)

    # Save the JSON output to a file
    with open(imager_objects_json_path, "w") as file:
        file.write(output_json)

    # Print the JSON output
    print(output_json)

# Read objects.json to pre-populate the values in the input boxes
# Return the number of objects which is determined by the number of entries in objects.json and the current version number.
def read_objects_json(obj_id_input, obj_names_input, desc_input, obj_svcs_input, model):
    if not os.path.exists(imager_objects_json_path):
        # Provide default data as a fallback when sources.json does not exist
        obj_id_input.append("cat")
        obj_names_input.append("the cat")
        desc_input.append("a cat")
        obj_svcs_input.append({"location" : {  #list of dictionaries of string:dictionaries pairs
                    "osvc_name": "location",
                    "msgtpl": "I saw [OBJNAME] [TIMEAGO] ago on the [CHANNEL] camera. [LOCATION]",
                    "age_out": 10800,
                    "def_off": True
                }})
        version = 1
    else:
        with open(imager_objects_json_path, "r") as file:
            data = json.load(file)
            model[0] = data["model"]

            # Populate the lists
            for obj in data["objects"]:
                obj_id_input.append(obj["obj_id"])
                obj_names_input.append(','.join(obj["names"]))
                desc_input.append(obj["desc"])
                svcs_dict = dict()
                for item in obj["obj_svcs"]:
                    svcs_dict[item["osvc_name"]] = item
                obj_svcs_input.append(svcs_dict)
            
            version = data['version']
    
    return (len(obj_id_input), version, model)

# Add an extra source channel
def add_channel(channel_input, name_input, url_input, slider_input):
    channel_input.append("")
    name_input.append("")
    url_input.append("")
    slider_input.append(3)
    st.session_state.num_channels += 1

# Add an extra object
def add_object(obj_id_input, obj_names_input, desc_input, obj_svcs_input):
    obj_id_input.append("cat")
    obj_names_input.append("the cat")
    desc_input.append("a cat")
    obj_svcs_input.append({"location" : {  #list of dictionaries of string:dictionaries pairs
                    "osvc_name": "location",
                    "msgtpl": "I saw [OBJNAME] [TIMEAGO] ago on the [CHANNEL] camera. [LOCATION]",
                    "age_out": 10800,
                    "def_off": True
                }})
    st.session_state.num_objects += 1

# Remove the last object from existing ones
def remove_object(obj_id_input, obj_names_input, desc_input, obj_svcs_input):
    if st.session_state.num_objects > 1:  #keep one object at a minimum
        obj_id_input.pop()
        obj_names_input.pop()
        desc_input.pop()
        obj_svcs_input.pop()
        st.session_state.num_objects -= 1

# Get the object service dictionary associated with object at a specific index 
def get_obj_svcs_dict(obj_svcs_input, index):
    with st.container(border=True):
        location_on = st.toggle("Activate location service",
                                key = "location_toggle" + str(index), 
                                value=("location" in obj_svcs_input[index]))

        msgtpl = st.text_input("Output message", key = "msgtpl" + str(index),
                                value = (
                                    ""  # Default value
                                    if "location" not in obj_svcs_input[index] or "msgtpl" not in obj_svcs_input[index]["location"] 
                                    else obj_svcs_input[index]["location"]["msgtpl"]
                                ),
                               )
        age_out = st.number_input("Age out (hours)", min_value = 0, key = "age_out" + str(index),
                                    value = (
                                        0  # Default value
                                        if "location" not in obj_svcs_input[index] or "age_out" not in obj_svcs_input[index]["location"] 
                                        else obj_svcs_input[index]["location"]["age_out"]
                                    ),                            
                                    format="%d")
        def_off = st.selectbox("Default off", boolean_selection, key = "def_off" + str(index),
                                index = (
                                    0 # Default value
                                    if "location" not in obj_svcs_input[index] or "def_off" not in obj_svcs_input[index]["location"] 
                                    else boolean_selection.index(obj_svcs_input[index]["location"]["def_off"])
                                )
                               )
        skip_ch = st.text_input("Channels to skip (comma separated list)", key = "skip_ch" + str(index),
                                value = (
                                    ""  # Default value
                                    if "location" not in obj_svcs_input[index] or "skip_ch" not in obj_svcs_input[index]["location"] 
                                    else ','.join(obj_svcs_input[index]["location"]["skip_ch"])
                                ),
                               )
        
        obj_svcs_input[index]["location"] = {  #list of dictionaries of string:dictionaries pairs
                                        "osvc_name": "location",
                                        "msgtpl": msgtpl,
                                        "age_out": age_out,
                                        "def_off": def_off,
                                        "skip_ch": [x.strip() for x in skip_ch.split(',')]
                                    }
        
        #if skip_ch contains only empty string, remove it
        if obj_svcs_input[index]["location"]["skip_ch"][0] == "":  
            obj_svcs_input[index]["location"].pop("skip_ch", None)

        if not location_on:
            obj_svcs_input[index].pop("location", None)

    with st.container(border=True):
        alert_on = st.toggle("Activate alert service", key = "alert_toggle" + str(index), value=("alert" in obj_svcs_input[index]))

        msgtpl = st.text_input("Output message", key = "msgtpl_alert" + str(index),
                                value = (
                                    ""  # Default value
                                    if "alert" not in obj_svcs_input[index] or "msgtpl" not in obj_svcs_input[index]["alert"] 
                                    else obj_svcs_input[index]["alert"]["msgtpl"]
                                ),
                              )
        age_out = st.number_input("Age out (hours)", min_value = 0, key = "age_out_alert" + str(index),
                                    value = (
                                        0  # Default value
                                        if "alert" not in obj_svcs_input[index] or "age_out" not in obj_svcs_input[index]["alert"] 
                                        else obj_svcs_input[index]["alert"]["age_out"]
                                    ),                            
                                    format="%d")
        mute_time = st.number_input("Mute time (secs)", min_value = 0, key = "mute_time_alert" + str(index),
                                    value = (
                                        600  # Default value
                                        if "alert" not in obj_svcs_input[index] or "mute_time" not in obj_svcs_input[index]["alert"] 
                                        else obj_svcs_input[index]["alert"]["mute_time"]
                                    ),                            
                                    format="%d")
        def_off = st.selectbox("Default off", boolean_selection, key = "def_off_alert" + str(index),
                                index = (
                                    0 # Default value
                                    if "alert" not in obj_svcs_input[index] or "def_off" not in obj_svcs_input[index]["alert"] 
                                    else boolean_selection.index(obj_svcs_input[index]["alert"]["def_off"])
                                )
                              )
        skip_ch = st.text_input("Channels to skip (comma separated list)", key = "skip_ch_alert" + str(index),
                                value = (
                                    ""  # Default value
                                    if "alert" not in obj_svcs_input[index] or "skip_ch" not in obj_svcs_input[index]["alert"] 
                                    else ','.join(obj_svcs_input[index]["alert"]["skip_ch"])
                                ),
                               )

        obj_svcs_input[index]["alert"] = {  #list of dictionaries of string:dictionaries pairs
                                        "osvc_name": "alert",
                                        "msgtpl": msgtpl,
                                        "age_out": age_out,
                                        "mute_time": mute_time,
                                        "def_off": def_off,
                                        "skip_ch": [x.strip() for x in skip_ch.split(',')] 
                                    }
        
        #if skip_ch contains only empty string, remove it
        if obj_svcs_input[index]["alert"]["skip_ch"][0] == "":  
            obj_svcs_input[index]["alert"].pop("skip_ch", None)

        if not alert_on:
            obj_svcs_input[index].pop("alert", None)

    return obj_svcs_input[index]

# handle removal of the channels
def handle_removal(index):
    if st.session_state.num_channels > 1:  #keep one channel at a minimum
        st.session_state.channel_input.pop(index)
        st.session_state.name_input.pop(index)
        st.session_state.url_input.pop(index)
        st.session_state.slider_input.pop(index)
        st.session_state.num_channels -= 1
        st.rerun()

# Main application state machine
# initial state --> streaming_configure_sources --> initial state
#               |                               |
#               -----> configure_objects -------- 
if __name__ == "__main__":
    st.title("Watchman")
    if "app_state" not in st.session_state or st.session_state.app_state == "init":
        def sources_callback():
            st.session_state.app_state = "streaming_configure_sources"

        def objects_callback():
            st.session_state.app_state = "configure_objects"

        with st.form(key='start_form'):
            st.write("Select which you would like to configure")
            st.form_submit_button(label='Input Channels', on_click=sources_callback)
            st.form_submit_button(label='Objects of interest', on_click=objects_callback)

    elif st.session_state.app_state == "streaming_configure_sources":
        st.header("Streaming sources configuration")
        if "num_channels" not in st.session_state:
            st.session_state.num_channels = 0

        with st.form(key='streaming_configure_sources_form'):
            if st.session_state.num_channels == 0:
                st.session_state.channel_input = list()
                st.session_state.name_input = list()
                st.session_state.url_input = list()
                st.session_state.slider_input = list()

                (st.session_state.num_channels, st.session_state.sources_version) = read_sources_json(st.session_state.channel_input,
                                                                                                      st.session_state.name_input,
                                                                                                      st.session_state.url_input,
                                                                                                      st.session_state.slider_input)

            st.subheader("List of channels")
            for i in range(st.session_state.num_channels):
                st.divider()
                st.session_state.channel_input[i] = st.text_input("Channel "+ str(i), 
                                                                  key = "channel" + str(i), 
                                                                  value=st.session_state.channel_input[i])
                st.session_state.name_input[i] = st.text_input("Name "+ str(i),
                                                               key = "name" + str(i),
                                                               value=st.session_state.name_input[i])
                st.session_state.url_input[i] = st.text_input("Url "+ str(i),
                                                              key = "url" + str(i),
                                                              value=st.session_state.url_input[i])
                st.session_state.slider_input[i] = st.slider('Update interval '+ str(i), 0, 10, st.session_state.slider_input[i],
                                                             key='upd_int' + str(i))
                # Create a hidden field to handle removal
                if st.form_submit_button(f"Remove Channel {i}"):
                    handle_removal(i)

            st.divider()
            if st.form_submit_button(label='Add channel'):
                add_channel(st.session_state.channel_input,
                            st.session_state.name_input,
                            st.session_state.url_input,
                            st.session_state.slider_input)
                st.rerun()  # Rerun to reflect changes immediately

            if st.form_submit_button(label='Confirm configuration', type='primary'):
                print("Streaming mode: Producing sources.json file")
                st.session_state.sources_version += 1
                output_sources_json(st.session_state.channel_input,
                                    st.session_state.name_input,
                                    st.session_state.url_input,
                                    st.session_state.slider_input,
                                    st.session_state.sources_version)

                st.session_state.app_state = "init"
                st.rerun()

    elif st.session_state.app_state == "configure_objects":
        st.header("Objects configuration")
        if "num_objects" not in st.session_state:
            st.session_state.num_objects = 0

        with st.form(key='streaming_configure_objects_form'):
            if st.session_state.num_objects == 0:
                st.session_state.obj_id_input = list()
                st.session_state.obj_names_input = list()
                st.session_state.desc_input = list()
                st.session_state.obj_svcs_input = list()
                st.session_state.model = ["ollama-simple"]

                (st.session_state.num_objects, st.session_state.objects_version, st.session_state.model) = read_objects_json(st.session_state.obj_id_input,
                                                                                                                            st.session_state.obj_names_input,
                                                                                                                            st.session_state.desc_input,
                                                                                                                            st.session_state.obj_svcs_input,
                                                                                                                            st.session_state.model)

            st.session_state.model[0] = st.selectbox("AI Model", models_selection,
                                                     index=models_selection.index(st.session_state.model[0]))

            for i in range(st.session_state.num_objects):
                st.divider()
                st.session_state.obj_id_input[i] = st.selectbox("Object type " + str(i), obj_ids_selection,
                                                                key="obj_id" + str(i),
                                                                index=obj_ids_selection.index(st.session_state.obj_id_input[i]))
                st.session_state.obj_names_input[i] = st.text_input("Object names " + str(i) + " (comma separated list)",
                                                                    key="obj_names" + str(i),
                                                                    value=st.session_state.obj_names_input[i])
                st.session_state.desc_input[i] = st.text_input("Description " + str(i),
                                                               key="desc" + str(i),
                                                               value=st.session_state.desc_input[i])
                st.session_state.obj_svcs_input[i] = get_obj_svcs_dict(st.session_state.obj_svcs_input, i)

            st.divider()
            if st.form_submit_button(label='Add object'):
                add_object(st.session_state.obj_id_input,
                            st.session_state.obj_names_input,
                            st.session_state.desc_input,
                            st.session_state.obj_svcs_input)
                st.rerun()  # Rerun to reflect changes immediately

            if st.form_submit_button(label='Remove object'):
                remove_object(st.session_state.obj_id_input,
                               st.session_state.obj_names_input,
                               st.session_state.desc_input,
                               st.session_state.obj_svcs_input)
                st.rerun()  # Rerun to reflect changes immediately

            if st.form_submit_button(label='Confirm configuration', type='primary'):
                print("Streaming mode: Producing objects.json file")
                st.session_state.objects_version += 1
                output_objects_json(st.session_state.obj_id_input,
                                    st.session_state.obj_names_input,
                                    st.session_state.desc_input,
                                    st.session_state.obj_svcs_input,
                                    st.session_state.model,
                                    st.session_state.objects_version)
                st.session_state.app_state = "init"
                st.rerun()

    else:
        st.write("Unexpected error occurred.")
