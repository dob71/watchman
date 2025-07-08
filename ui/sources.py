import streamlit as st
import json
import os
import sys
import random

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))

from ui_common import *

# Create sources.json file
def output_sources_json(channel_input, name_input, url_input, slider_input, width_input, height_input, quality_input, new_version):
    channels = list()
    for i in range(len(channel_input)):
        channels.append(
            {
                CFG_chan_id_key: channel_input[i],
                CFG_chan_name_key: name_input[i],
                CFG_chan_url_key: url_input[i],
                CFG_chan_upd_int_key: slider_input[i],
                CFG_chan_img_w_key: width_input[i],
                CFG_chan_img_h_key: height_input[i],
                CFG_chan_img_q_key: quality_input[i]
            }
        )

    # Define the final JSON structure
    output = {
        CFG_version_key: new_version,
        CFG_channels_key: channels
    }

    # Convert the structure to a JSON string
    output_json = json.dumps(output, indent=4)

    # Save the JSON output atomically using temporary file
    tmp_path = f"{imgsrc_cfg_json_path}.tmp"
    with open(tmp_path, "w") as file:
        file.write(output_json)
    os.rename(tmp_path, imgsrc_cfg_json_path)

    # Print the JSON output
    print(output_json)

# Add an extra source channel
def add_channel():
    rnd = hex(random.getrandbits(64))[2:]
    chan_id = f"chan_{rnd}"
    st.session_state.channels[chan_id] = {
        "name": f"New channel",
        "url": "http://my.webcam.com/image.jpg",
        "slider": 5,
        "width": 1280,
        "height": 720,
        "quality": 50
    }
    return chan_id

# Read sources.json to pre-populate the values in the input boxes
# Return the number of channels which is determined by the number of entries in sources.json and the current version number.
def read_sources_json():
    channels = {}
    version = 1
    if os.path.exists(imgsrc_cfg_json_path):
        with open(imgsrc_cfg_json_path, "r") as file:
            data = json.load(file)
            version = data[CFG_version_key]
            for channel in data[CFG_channels_key]:
                chan_id = channel[CFG_chan_id_key]
                channels[chan_id] = {
                    "name": channel[CFG_chan_name_key],
                    "url": channel[CFG_chan_url_key],
                    "slider": channel[CFG_chan_upd_int_key],
                    "width": channel.get(CFG_chan_img_w_key, 1280),
                    "height": channel.get(CFG_chan_img_h_key, 720),
                    "quality": channel.get(CFG_chan_img_q_key, 50)
                }
    return (channels, version)

# Update selection to new channel and force rerun
def update_selection(channel_id):
    st.session_state.current_channel_select = channel_id

# handle removal of the channels
def handle_channel_removal(chan_id):
    if len(st.session_state.channels) > 1:  # Keep at least one channel
        del st.session_state.channels[chan_id]

# Channels state machine section
def configure_sources_sm(key):
    st.header("Configure Input Channels")
    
    # Initialize session state only once when entering the UI
    if "channels" not in st.session_state:
        st.session_state.channels, st.session_state.sources_version = read_sources_json()
    
    # Reset selection if invalid
    if "current_channel_select" not in st.session_state or \
       (st.session_state.channels and st.session_state.current_channel_select not in st.session_state.channels):
        st.session_state.current_channel_select = (
            list(st.session_state.channels.keys())[0] 
            if st.session_state.channels 
            else None
        )

    st.subheader(f"Select Channel:")
    col1, col2, col3 = st.columns([7.5, 1, 2])
    
    with col1:
        options = list(st.session_state.channels.keys()) if st.session_state.channels else []
        
        # Always show selectbox even when empty
        if options:
            # Validate current selection exists
            if st.session_state.current_channel_select not in options:
                st.session_state.current_channel_select = options[0]
            
            st.session_state["channel_select"] = st.session_state.current_channel_select

            selected_channel = st.selectbox(
                "Select a channel:",
                options=options,
                help="Select a channel to configure",
                label_visibility='collapsed',
                key="channel_select",
                format_func=lambda x: st.session_state.channels[x]["name"],
                on_change=lambda: update_selection(st.session_state["channel_select"])
            )
        else:
            st.selectbox(
                "Select a channel:",
                options=[],
                label_visibility='collapsed',
                disabled=True,
                help="No channels available"
            )
            st.session_state.current_channel_select = None
    
    with col2:
        if st.button("Add"): 
            new_chan_id = add_channel()
            update_selection(new_chan_id)
            st.rerun()
    
    with col3:
        if st.button("Remove"):
            if st.session_state.channels and st.session_state.current_channel_select in st.session_state.channels:
                handle_channel_removal(st.session_state.current_channel_select)
                st.rerun()

    if st.session_state.channels and st.session_state.current_channel_select:
        st.subheader(f"Channel Configuration")
        chan_id = st.session_state.current_channel_select
        channel = st.session_state.channels[chan_id]
        
        # Channel name input
        new_name = st.text_input(
            "Channel name",
            value=channel["name"],
            help="Human-readable name for voice responses and UI display",
            key=f"name_{chan_id}"
        )
        if new_name != channel["name"]:
            st.session_state.channels[chan_id]["name"] = new_name
            st.rerun()
        
        # URL input with immediate session state update
        new_url = st.text_input(
            "Channel image load URL",
            value=channel["url"],
            help="Source URL for camera feed (supports http/s, rtsp, and local files)",
            key=f"url_{chan_id}"
        )
        if new_url != channel["url"]:
            st.session_state.channels[chan_id]["url"] = new_url
            st.rerun()
        
        # Image dimensions and quality
        col_dim1, col_dim2, col_qual = st.columns(3)
        with col_dim1:
            new_width = st.number_input(
                f"{CFG_chan_img_w_key.title()} (pixels)",
                min_value=26,
                max_value=3840,
                value=channel["width"],
                help=f"{CFG_chan_img_w_key} in pixels (26-3840)",
                key=f"width_{chan_id}"
            )
            if new_width != channel["width"]:
                st.session_state.channels[chan_id]["width"] = new_width
                st.rerun()
        
        with col_dim2:
            new_height = st.number_input(
                f"{CFG_chan_img_h_key.title()} (pixels)",
                min_value=26,
                max_value=2160,
                value=channel["height"],
                help=f"{CFG_chan_img_h_key} in pixels (26-2160)",
                key=f"height_{chan_id}"
            )
            if new_height != channel["height"]:
                st.session_state.channels[chan_id]["height"] = new_height
                st.rerun()
        
        with col_qual:
            new_quality = st.slider(
                f"{CFG_chan_img_q_key.title()} (%)",
                min_value=1,
                max_value=100,
                value=channel["quality"],
                help=f"{CFG_chan_img_q_key} for JPEG compression (1-100)",
                key=f"quality_{chan_id}"
            )
            if new_quality != channel["quality"]:
                st.session_state.channels[chan_id]["quality"] = new_quality
                st.rerun()
        
        # Update interval slider
        new_slider = st.slider(
            "Image update interval", 0, 10, channel["slider"],
            help="How often to check for new images (in seconds)",
            key=f"slider_{chan_id}"
        )
        if new_slider != channel["slider"]:
            st.session_state.channels[chan_id]["slider"] = new_slider
            st.rerun()
        
    if st.button(label='Apply All Changes'):
        # Process auto-generated channel IDs
        new_channels = {}
        used_ids = set()
        id_mapping = {}  # Track old ID -> new ID mapping
        
        for chan_id, chan_data in st.session_state.channels.items():
            if chan_id.startswith("chan_"):
                # Generate base ID from name
                base_name = chan_data["name"].lower().strip()
                base_id = ''.join(c for c in base_name if c.isalnum())
                
                # Handle empty base ID case
                if not base_id:
                    base_id = chan_id
            else:
                base_id = chan_id

            id_mapping[chan_id] = base_id
            used_ids.add(base_id)
            new_channels[base_id] = chan_data

        # Update selected channel if it was renamed
        if st.session_state.current_channel_select in id_mapping:
            st.session_state.current_channel_select = id_mapping[st.session_state.current_channel_select]

        # Check if any random IDs remain
        for chan_id in used_ids:
            if chan_id.startswith("chan_"):
                st.error(f"Error: cannot generate unique ID for channel {new_channels[chan_id]['name']}.")
                return

        # Check for unique IDs and names
        channel_ids = list(new_channels.keys())
        channel_names = [chan["name"] for chan in new_channels.values()]

        # Check for duplicate IDs
        if len(channel_ids) != len(set(channel_ids)):
            st.error("Error: Channel IDs must be unique.")
            return

        # Check for duplicate names
        if len(channel_names) != len(set(channel_names)):
            st.error("Error: Channel names must be unique.")
            return
        
        # Update session state with new IDs before saving
        st.session_state.channels = new_channels
        st.session_state.sources_version += 1
        
        output_sources_json(
            list(st.session_state.channels.keys()),
            [chan["name"] for chan in st.session_state.channels.values()],
            [chan["url"] for chan in st.session_state.channels.values()],
            [chan["slider"] for chan in st.session_state.channels.values()],
            [chan["width"] for chan in st.session_state.channels.values()],
            [chan["height"] for chan in st.session_state.channels.values()],
            [chan["quality"] for chan in st.session_state.channels.values()],
            st.session_state.sources_version
        )
        st.session_state.app_state = "init"
        st.rerun()

    # Add a "Back" button to go back to the start form
    if st.button("Back"):
        st.session_state.app_state = "init"
        st.rerun()
