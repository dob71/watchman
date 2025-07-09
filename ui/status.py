import streamlit as st
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))

from ui_common import *

EVENT_DIR = f"{IPC_DIR}/{IMG_dir}"
IMAGE_DIR = f"{IPC_DIR}/{EVT_dir}"

# System status state machine section
def system_status_sm(key):
    st.header("System Status")

    # Load data from JSON files
    sources_data = load_data(imgsrc_cfg_json_path)
    objects_data = load_data(objects_cfg_json_path)
    # Extract channel ids and object ids
    channels, objects = extract_ids(sources_data, objects_data)

    # Channel selection with a refresh button
    st.markdown("### **Select a channel:**")
    col1, col2 = st.columns([4, 1])  # Create two columns with a ratio of 4:1
    with col1:
        selected_channel = st.selectbox("channel", label_visibility='collapsed', 
                                        options=[f"{chan}" for chan in channels],
                                        format_func=lambda c:chan_id_to_name(sources_data, c))
    with col2:
        if st.button('Refresh'):
            st.rerun()  # Rerun the app to refresh the page

    # Display channel's current image
    image_path = f"{IMAGE_DIR}/{selected_channel}/{IMG_file_name}"
    try:
        with open(image_path, "rb") as img_file:
            img = Image.open(img_file)
            st.image(img, use_container_width=True)
    except:
        # If image cannot be loaded, display the error one
        load_error_path = os.path.dirname(__file__) + "/load_error.jpg"
        with open(load_error_path, "rb") as img_file:
            img = Image.open(img_file)
            st.image(img, use_container_width=True)
        
    image_off_path = f"{IMAGE_DIR}/{selected_channel}/{IMG_off_file_name}"
    if os.path.exists(image_off_path):
        st.markdown("Note: the channel with no services turned on is automaticaly disabled")

    available_obj_dirs = [objdir for objdir in objects if os.path.exists(f"{EVENT_DIR}/{selected_channel}/{objdir}")]
    for object in available_obj_dirs:
        event_path = f"{EVENT_DIR}/{selected_channel}/{object}"
        try: obj_json = load_data(f"{event_path}/{EVT_obj_file_name}")
        except: continue
        obj_name = obj_json[EVT_obj_names_key][0]
        obj_services = obj_json[EVT_osvc_list_key]        
        st.markdown(f"### Object: {obj_name}")
        for index, service in enumerate(obj_services):
            off_file = f"{event_path}/{service}.off"
            if os.path.exists(off_file):
                initial_state = False
            else:
                initial_state = True
            state = st.toggle(label=service, value=initial_state, key=f'{selected_channel}_{object}_{service}')
            # Update the service status based on toggle state
            if state and os.path.exists(off_file):
                try: os.remove(off_file)
                except: pass
            elif not state and not os.path.exists(off_file):
                try: open(off_file, 'a').close()
                except: pass

    if st.button("Back"):
        st.session_state.app_state = "init"
        st.rerun()
