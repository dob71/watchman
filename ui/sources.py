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

    # Save the JSON output to a file
    with open(imgsrc_cfg_json_path, "w") as file:
        file.write(output_json)

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



# Add an extra source channel
def add_channel(channel_input, name_input, url_input, slider_input):
    channel_input.append("Unique lowercase word (used to name channel folders)")
    name_input.append("Human readable channel name, like backyard, porch, ...")
    url_input.append("URL to load the channel image from http://my.webcam.com/image.jpg")
    slider_input.append(3)
    st.session_state.num_channels += 1

# handle removal of the channels
def handle_channel_removal(index):
    if st.session_state.num_channels > 1:  #keep one channel at a minimum
        st.session_state.channel_input.pop(index)
        st.session_state.name_input.pop(index)
        st.session_state.url_input.pop(index)
        st.session_state.slider_input.pop(index)
        st.session_state.num_channels -= 1
        st.rerun()

# Channels state machine section
def configure_sources_sm(key):
    st.header("Configure Input Channels")
    if "num_channels" not in st.session_state:
        st.session_state.num_channels = 0

    with st.form(key = key):
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
            st.subheader(f"Channel {i}")
            st.session_state.channel_input[i] = st.text_input("Channel ID", 
                                                              key = "channel" + str(i), 
                                                              value=st.session_state.channel_input[i])
            st.session_state.name_input[i] = st.text_input("Channel name",
                                                            key = "name" + str(i),
                                                            value=st.session_state.name_input[i])
            st.session_state.url_input[i] = st.text_input("Channel image load URL",
                                                            key = "url" + str(i),
                                                            value=st.session_state.url_input[i])
            st.session_state.slider_input[i] = st.slider("Image update interval", 0, 10, st.session_state.slider_input[i],
                                                            key='upd_int' + str(i))
            # Create a button to handle removal
            if st.form_submit_button(f"Remove Channel {i}"):
                handle_channel_removal(i)

        st.divider()
        if st.form_submit_button(label='Add channel'):
            add_channel(st.session_state.channel_input,
                        st.session_state.name_input,
                        st.session_state.url_input,
                        st.session_state.slider_input)
            st.rerun()  # Rerun to reflect changes immediately

        if st.form_submit_button(label='Confirm configuration', type='primary'):
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
