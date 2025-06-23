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
        # Load existing model config if available
        if os.path.exists(model_cfg_json_path):
            with open(model_cfg_json_path, "r") as file:
                model_config = json.load(file)
            # Initialize version if missing
            model_config.setdefault(CFG_model_version_key, 1)
        else:
            model_config = {
                CFG_model_version_key: 1,
                CFG_obj_model_key: "ollama-simple",
                CFG_obj_model_name_key: "",
                CFG_obj_model_url_key: "",
                CFG_obj_model_tkn_key: "",
                CFG_lbl_model_key: "openai-generic",
                CFG_lbl_model_name_key: "",
                CFG_lbl_model_url_key: "",
                CFG_lbl_model_tkn_key: ""
            }

        st.subheader("Object Detection Model")
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

        st.subheader("Auto-labeling Model")
        col3, col4 = st.columns(2)
        with col3:
            st.session_state.model[0][CFG_lbl_model_key] = st.text_input(
                "Model Interface ID",
                key="label_model_interface",
                value=st.session_state.model[0].get(CFG_lbl_model_key, "openai-generic"),
                help="Identifier from model_interfaces.py (e.g. openai-generic)"
            )
            st.session_state.model[0][CFG_lbl_model_url_key] = st.text_input(
                "Model URL",
                key="label_model_url",
                value=st.session_state.model[0].get(CFG_lbl_model_url_key, ""),
                help="Endpoint URL for auto-labeling API"
            )
            
        with col4:
            st.session_state.model[0][CFG_lbl_model_name_key] = st.text_input(
                "Model Name", 
                key="label_model_name",
                value=st.session_state.model[0].get(CFG_lbl_model_name_key, ""),
                help="Model name for auto-labeling (e.g. gpt-4o-mini)"
            )
            st.session_state.model[0][CFG_lbl_model_tkn_key] = st.text_input(
                "API Token/Key",
                key="label_model_token",
                value=st.session_state.model[0].get(CFG_lbl_model_tkn_key, ""),
                help="Authentication token for auto-labeling",
                type="password"
            )

        if st.form_submit_button(label='Save Model Configuration', type='primary'):
            # Save to model.json with version increment using atomic write
            new_version = model_config.get(CFG_model_version_key, 0) + 1
            new_config = {
                CFG_model_version_key: new_version,
                **st.session_state.model[0]
            }
            tmp_path = f"{model_cfg_json_path}.tmp"
            with open(tmp_path, "w") as file:
                json.dump(new_config, file, indent=4)
            os.rename(tmp_path, model_cfg_json_path)
            
            st.session_state.app_state = "init"
            st.rerun()

    if st.button("Back"):
        st.session_state.app_state = "init"
        st.rerun()
