import streamlit as st
import json
import os
import sys

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))

from ui_common import *

def configure_models_sm(key):
    st.header("Configure AI Models")
    
    if "model" not in st.session_state:
        st.session_state.model = [{
            CFG_obj_model_key: "ollama-simple",
            CFG_obj_model_name_key: "",
            CFG_obj_model_url_key: "",
            CFG_obj_model_tkn_key: ""
        }]
        
        # Load existing config if available
        if os.path.exists(objects_cfg_json_path):
            with open(objects_cfg_json_path, "r") as file:
                data = json.load(file)
                model_config = data.get(CFG_obj_model_key, {})
                if isinstance(model_config, str):
                    st.session_state.model[0] = {
                        CFG_obj_model_key: model_config,
                        CFG_obj_model_name_key: "",
                        CFG_obj_model_url_key: "",
                        CFG_obj_model_tkn_key: ""
                    }
                else:
                    st.session_state.model[0] = {
                        CFG_obj_model_key: model_config.get(CFG_obj_model_key, "ollama-simple"),
                        CFG_obj_model_name_key: model_config.get(CFG_obj_model_name_key, ""),
                        CFG_obj_model_url_key: model_config.get(CFG_obj_model_url_key, ""),
                        CFG_obj_model_tkn_key: model_config.get(CFG_obj_model_tkn_key, "")
                    }

    with st.form(key=key):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.model[0][CFG_obj_model_key] = st.text_input(
                "Model Interface ID",
                key="model_interface",
                value=st.session_state.model[0].get(CFG_obj_model_key, "ollama-simple"),
                help="Identifier from model_interfaces.py (e.g. ollama-complex, vllm-complex)"
            )
            st.session_state.model[0][CFG_obj_model_url_key] = st.text_input(
                "Model URL",
                key="model_url",
                value=st.session_state.model[0].get(CFG_obj_model_url_key, ""),
                help="Endpoint URL for the model API"
            )
            
        with col2:
            st.session_state.model[0][CFG_obj_model_name_key] = st.text_input(
                "Model Name",
                key="model_name",
                value=st.session_state.model[0].get(CFG_obj_model_name_key, ""),
                help="Specific model name/version (e.g. llama3.2-vision:11b-instruct-fp16)"
            )
            st.session_state.model[0][CFG_obj_model_tkn_key] = st.text_input(
                "API Token/Key",
                key="model_token",
                value=st.session_state.model[0].get(CFG_obj_model_tkn_key, ""),
                help="Authentication token if required by the API",
                type="password"
            )

        if st.form_submit_button(label='Save Model Configuration', type='primary'):
            # Save to objects.json model section
            if os.path.exists(objects_cfg_json_path):
                with open(objects_cfg_json_path, "r") as file:
                    data = json.load(file)
            else:
                data = {CFG_obj_objects_key: []}

            data[CFG_obj_model_key] = st.session_state.model[0]
            with open(objects_cfg_json_path, "w") as file:
                json.dump(data, file, indent=4)
            
            st.session_state.app_state = "init"
            st.rerun()

    if st.button("Back"):
        st.session_state.app_state = "init"
        st.rerun()
