import streamlit as st
import os
import sys

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))

from ui_common import *
from status import system_status_sm
from sources import configure_sources_sm
from objects import configure_objects_sm
from models_cfg import configure_models_sm
from dataset import dataset_labeling_sm, dataset_management_sm

# Main application state machine
# initial state --> streaming_configure_sources --> initial state
#               |                               |
#               -----> configure_objects -------- 
#               |                               |
#               -----> dataset_image_labeling --- 
#               |                               |
#               -----> dataset_management ------- 
#               |                               |
#               -----> system_status ------------ 
if __name__ == "__main__":
    st.title("Watchman")
    if "app_state" not in st.session_state or st.session_state.app_state == "init":
        def status_callback():
            st.session_state.app_state = "system_status"

        def sources_callback():
            st.session_state.app_state = "streaming_configure_sources"

        def objects_callback():
            st.session_state.app_state = "configure_objects"

        def models_callback():
            st.session_state.app_state = "configure_models"

        def dataset_lbl_callback():
            st.session_state.app_state = "dataset_image_labeling"

        def dataset_mgmt_callback():
            st.session_state.app_state = "dataset_management"

        with st.form(key='start_form'):
            col1, col2 = st.columns(2)
            col2.markdown("### **Configuration**")
            col2.form_submit_button(label='Configure LLMs', on_click=models_callback)
            col2.form_submit_button(label='Configure Input Channels', on_click=sources_callback)
            col2.form_submit_button(label='Configure Objects of interest', on_click=objects_callback)
            col1.markdown("### **System Management**")
            col1.form_submit_button(label='System Status', on_click=status_callback)
            col1.form_submit_button(label='Data Collection', on_click=dataset_mgmt_callback)
            col1.form_submit_button(label='Training on Collected Data', on_click=dataset_lbl_callback)

    elif st.session_state.app_state == "system_status":
        system_status_sm('system_status_form')

    elif st.session_state.app_state == "streaming_configure_sources":
        configure_sources_sm('streaming_configure_sources_form')

    elif st.session_state.app_state == "configure_objects":
        configure_objects_sm('streaming_configure_objects_form')
    
    elif st.session_state.app_state == "configure_models":
        configure_models_sm('configure_models_form')

    elif st.session_state.app_state == "dataset_management":
        dataset_management_sm('dataset_management_form')

    elif st.session_state.app_state == "dataset_image_labeling":
        dataset_labeling_sm('dataset_labeling_form')

    else:
        st.write("Unexpected error occurred.")
