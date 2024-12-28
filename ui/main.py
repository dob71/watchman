import streamlit as st
import numpy as np
import time

from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import speech_to_text

import json

# Path where test image would be saved
test_save_path = "/home/user/capstone/.data/images/captured_test_image.jpg"
# Path of sources.json
imager_sources_json_path = "/home/user/capstone/watchman/imager/sources.json"

# Streamlit widgets automatically run the script from top to bottom. 

# Create sources.json file
def output_sources_json(channel_input, name_input, url_input, slider_input):
    channels = list()
    for i in range(4):
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
        "version": 1,
        "channels": channels
    }

    # Convert the structure to a JSON string
    output_json = json.dumps(output, indent=4)

    # Save the JSON output to a file
    with open(imager_sources_json_path, "w") as file:
        file.write(output_json)

    # Print the JSON output
    print(output_json)

def collect_speech(test_mode):
    text = speech_to_text(
        language='en',
        start_prompt="Press to record voice query",
        stop_prompt="Stop recording",
        just_once=False,
        use_container_width=False,
        callback=None,
        args=(),
        kwargs={},
        key=None
    )
    if text:
        st.write("Voice query: " + text)
        if st.button("Submit recorded query", type="primary"):
            #TODO: Notify orchestrator and wait for results

            #output results
            st.write("Hit the play button to hear the results...")
            sound_file = BytesIO()
            tts = gTTS('The cat is in the top-right-hand corner of channel 1, next to the plant', lang='en')
            tts.write_to_fp(sound_file)
            st.audio(sound_file)
    else:
        st.write("No voice query recorded")
    

# Main application state machine
# initial state -> streaming_configure -> streaming_run
#      |
#      --> test
if __name__ == "__main__":
    st.write("Watchman")
    if "app_state" not in st.session_state:
        def streaming_callback():
            st.session_state.app_state = "streaming_configure"

        def test_callback():
            st.session_state.app_state = "test"

        def configure_callback():
            st.session_state.app_state = "streaming_run"

        with st.form(key='mode_form'):
            st.form_submit_button(label='Streaming mode', on_click=streaming_callback)
            st.form_submit_button(label='Test using a single image', on_click=test_callback)

    elif st.session_state.app_state == "streaming_configure":
        st.write("Streaming mode configuration")

        with st.form(key='streaming_configure_form'):
            channel_input = list()
            name_input = list()
            url_input = list()
            slider_input = list()
            for i in range(4):
                channel_input.append(st.text_input("Channel "+str(i), key="channel"+str(i)))
                name_input.append(st.text_input("Name "+str(i), key="name"+str(i)))
                url_input.append(st.text_input("Url "+str(i), key="url"+str(i)))
                slider_input.append(st.slider('Update interval '+str(i), 0, 10, 3, key='upd_int'+str(i)))

            submit = st.form_submit_button(label='Confirm configuration')
            if submit:
                print("Streaming mode: Producing json file and sending all inputs to orchestrator")
                output_sources_json(channel_input, name_input, url_input, slider_input)
                st.session_state.app_state = "streaming_run"
                st.rerun()

    elif st.session_state.app_state == "streaming_run":
        st.write("Streaming mode")
        collect_speech(test_mode = False)

    elif st.session_state.app_state == "test":

        def set_clicked():
            st.session_state.clicked = True
            print("set_clicked")

        def run_test_callback():
            if 'uploaded_image_file' in st.session_state:
                print("VW:")
                print(st.session_state.uploaded_image_file)
                with open(test_save_path, mode='wb') as w:
                    w.write(st.session_state.uploaded_image_file.getvalue())
                #TODO: run image against model and output result
                print("Test mode: Sending inputs to orchestrator")
            else:
                print("Invalid image file")
                st.session_state.clicked = False
                
        st.write("Test mode")
        if "test_form_enabled" not in st.session_state:
            st.session_state.test_form_enabled = True

        if 'clicked' not in st.session_state:
            st.session_state.clicked = False

        if st.session_state.test_form_enabled:
            with st.form(key='test_form'):
                #st.button('Upload File', on_click=set_clicked)
                st.session_state.upload_image_button = st.form_submit_button(label='Upload Image', 
                                                                            on_click=set_clicked)
                if st.session_state.clicked:
                    st.session_state.uploaded_file = st.file_uploader("Choose a file")
                    if st.session_state.uploaded_file is not None:
                        print("read file as bytes")
                        bytes_data = st.session_state.uploaded_file.getvalue()
                        print(bytes_data)
                        #st.write(bytes_data)

                submit = st.form_submit_button(label='Confirm') 
                if submit:
                    if 'uploaded_file' in st.session_state:
                        # Save the uploaded file
                        print(st.session_state.uploaded_file)
                        with open(test_save_path, mode='wb') as w:
                            w.write(st.session_state.uploaded_file.getvalue())
                        
                        # Disable form
                        st.session_state.test_form_enabled = False
                        st.rerun()
                    else:
                        print("Invalid image file")
                        st.session_state.clicked = False

        if 'uploaded_file' in st.session_state and st.session_state.uploaded_file is not None:
            collect_speech(test_mode = True)
    else:
        st.write("Unexpected error occurred.")
