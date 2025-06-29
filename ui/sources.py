import streamlit as st
import json
import os
import sys

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))

from ui_common import *

# Create sources.json file
def output_sources_json(channel_input, name_input, url_input, slider_input, new_version):
    channels = list()
    for i in range(len(channel_input)):
        channels.append(
            {
                CFG_chan_id_key: channel_input[i],
                CFG_chan_name_key: name_input[i],
                CFG_chan_url_key: url_input[i],
                CFG_chan_upd_int_key: slider_input[i]
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

# Read sources.json to pre-populate the values in the input boxes
# Return the number of channels which is determined by the number of entries in sources.json and the current version number.
def read_sources_json(channel_input, name_input, url_input, slider_input):
    if not os.path.exists(imgsrc_cfg_json_path):
        # Provide hypothetical defaults when sources.json does not exist
        st.session_state.num_channels = 0
        add_channel(channel_input, name_input, url_input, slider_input)
        version = 1
    else:
        with open(imgsrc_cfg_json_path, "r") as file:
            data = json.load(file)

            # Populate the lists
            for channel in data[CFG_channels_key]:
                channel_input.append(channel[CFG_chan_id_key])
                name_input.append(channel[CFG_chan_name_key])
                url_input.append(channel[CFG_chan_url_key])
                slider_input.append(channel[CFG_chan_upd_int_key])
            
            version = data[CFG_version_key]
    
    return (len(channel_input), version)

# Update selection to new channel and force rerun
def update_selection(channel_id):
    st.session_state.new_channel_select = channel_id
    st.rerun()

# Add an extra source channel
def add_channel(channel_input, name_input, url_input, slider_input):
    url_input.append("http://my.webcam.com/image.jpg")
    slider_input.append(5)
    st.session_state.num_channels += 1
    channel_input.append(f"chan{st.session_state.num_channels}")
    name_input.append(f"Channel {st.session_state.num_channels}")

# handle removal of the channels
def handle_channel_removal(index):
    if st.session_state.num_channels > 1:  #keep one channel at a minimum
        st.session_state.channel_input.pop(index)
        st.session_state.name_input.pop(index)
        st.session_state.url_input.pop(index)
        st.session_state.slider_input.pop(index)
        st.session_state.num_channels -= 1

# Channels state machine section
def configure_sources_sm(key):
    st.header("Configure Input Channels")
    if "num_channels" not in st.session_state or "channel_input" not in st.session_state:
        st.session_state.num_channels = 0

    # Read config if we have no channels initialized                                                                                                                        
    if st.session_state.num_channels == 0:
        st.session_state.channel_input = list()
        st.session_state.name_input = list()
        st.session_state.url_input = list()
        st.session_state.slider_input = list()

        (st.session_state.num_channels, st.session_state.sources_version) = read_sources_json(st.session_state.channel_input,
                                                                                                st.session_state.name_input,
                                                                                                st.session_state.url_input,
                                                                                                st.session_state.slider_input)

    st.subheader(f"Select Channel:")
    col1, col2, col3 = st.columns([7.5, 1, 2])
    with col1:
        # Initialize or update channel selection
        if 'new_channel_select' in st.session_state:
            st.session_state.channel_select = st.session_state.new_channel_select
            del st.session_state.new_channel_select
            
        selected_channel = st.selectbox(
            "Select a channel:",
            options=st.session_state.channel_input,
            help="Select a channel to configure",
            label_visibility='collapsed',
            key="channel_select",
            format_func=lambda x: f"{st.session_state.name_input[st.session_state.channel_input.index(x)]}"
        )
    with col2:
        if st.button("Add"): 
            add_channel(
                st.session_state.channel_input,
                st.session_state.name_input,
                st.session_state.url_input,
                st.session_state.slider_input
            )
            update_selection(st.session_state.channel_input[-1])
    with col3:
        if st.button("Remove"):
            if st.session_state.num_channels > 0 and selected_channel in st.session_state.channel_input:
                handle_channel_removal(st.session_state.channel_input.index(selected_channel))
                st.rerun()

    if st.session_state.num_channels > 0:
        st.subheader(f"Channel Configuration")
        channel_index = st.session_state.channel_input.index(selected_channel)
        #st.session_state.channel_input[channel_index] = st.text_input(
        #    "Channel ID", 
        #    key = "channel", 
        #    value=st.session_state.channel_input[channel_index],
        #    help="Unique identifier used to name the channel's folder (lowercase, no spaces)"
        #)
        st.session_state.name_input[channel_index] = st.text_input(
            "Channel name",
            key = "name",
            value=st.session_state.name_input[channel_index],
            help="Human-readable name for voice responses and UI display"
        )
        st.session_state.url_input[channel_index] = st.text_input(
            "Channel image load URL",
            key = "url",
            value=st.session_state.url_input[channel_index],
            help="Source URL for camera feed (supports http/s, rtsp, and local files)"
        )
        st.session_state.slider_input[channel_index] = st.slider(
            "Image update interval", 0, 10, st.session_state.slider_input[channel_index],
            key='upd_int',
            help="How often to check for new images (in multiples of 1 second)"
        )
        
    if st.button(label='Apply Changes'):
        if len(st.session_state.channel_input) != len(set(st.session_state.channel_input)):
            st.error("Error: Channel IDs should be unique. Please fix before confirmation.")
        else:
            print("Streaming mode: Producing sources.json file")
            st.session_state.sources_version += 1
            output_sources_json(st.session_state.channel_input,
                                st.session_state.name_input,
                                st.session_state.url_input,
                                st.session_state.slider_input,
                                st.session_state.sources_version)

            st.session_state.app_state = "init"
            st.rerun()

    # Add a "Back" button to go back to the start form
    if st.button("Back"):
        st.session_state.app_state = "init"
        st.rerun()
