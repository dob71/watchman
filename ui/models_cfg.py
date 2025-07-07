import streamlit as st
import json
import os
import sys

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))

from ui_common import *

# Mapping between model parameter keys and config keys
MODEL_KEY_MAP = {
    'object': {
        'model_to_use': CFG_obj_model_name_key,
        'api_base': CFG_obj_model_url_key,
        'api_key': CFG_obj_model_tkn_key
    },
    'label': {
        'model_to_use': CFG_lbl_model_name_key,
        'api_base': CFG_lbl_model_url_key, 
        'api_key': CFG_lbl_model_tkn_key
    }
}

def configure_models_sm(key):
    st.header("Configure AI Models")
    
    # Initialize model config working copy
    if "model_config" not in st.session_state:
        # Get defaults from model interfaces
        default_obj_model = MODELS["ollama-simple"].model_parameters()
        default_label_model = MODELS["openai-generic"].model_parameters()
        
        # Map model parameters to config keys using direct mapping
        working_copy = {
            CFG_obj_model_key: "ollama-simple",
            CFG_lbl_model_key: "openai-generic",
            CFG_model_version_key: 1
        }
        
        # Object model parameters
        for param, value in default_obj_model.items():
            if param in MODEL_KEY_MAP['object']:
                working_copy[MODEL_KEY_MAP['object'][param]] = value
                
        # Label model parameters
        for param, value in default_label_model.items():
            if param in MODEL_KEY_MAP['label']:
                working_copy[MODEL_KEY_MAP['label'][param]] = value

        # Load existing config and merge with defaults
        if os.path.exists(model_cfg_json_path):
            with open(model_cfg_json_path, "r") as f:
                saved_config = json.load(f)
                # Update working copy with saved values using direct key access
                for k, v in saved_config.items():
                    if k in working_copy:
                        working_copy[k] = v
                # Preserve version
                working_copy[CFG_model_version_key] = saved_config.get(CFG_model_version_key, 1)

        st.session_state.model_config = working_copy

    # Get available model interfaces
    model_interfaces = list(MODELS.keys())
    label_interfaces = list(MODELS.keys())  # Changed to include all model interfaces

    # Initialize model selections in session state
    if 'current_obj_model_select' not in st.session_state:
        st.session_state.current_obj_model_select = st.session_state.model_config[CFG_obj_model_key]
    if 'current_lbl_model_select' not in st.session_state:
        st.session_state.current_lbl_model_select = st.session_state.model_config[CFG_lbl_model_key]

    # Callbacks to update session state when selections change
    def update_obj_model_selection():
        st.session_state.current_obj_model_select = st.session_state.obj_model_select
        # Update parameters immediately when selection changes
        new_obj_if = st.session_state.obj_model_select
        defaults = MODELS[new_obj_if].model_parameters()
        for param, value in defaults.items():
            if param in MODEL_KEY_MAP['object']:
                cfg_key = MODEL_KEY_MAP['object'][param]
                st.session_state.model_config[cfg_key] = value
        st.session_state.model_config[CFG_obj_model_key] = new_obj_if

    def update_lbl_model_selection():
        st.session_state.current_lbl_model_select = st.session_state.lbl_model_select
        # Update parameters immediately when selection changes
        new_lbl_if = st.session_state.lbl_model_select
        defaults = MODELS[new_lbl_if].model_parameters()
        for param, value in defaults.items():
            if param in MODEL_KEY_MAP['label']:
                cfg_key = MODEL_KEY_MAP['label'][param]
                st.session_state.model_config[cfg_key] = value
        st.session_state.model_config[CFG_lbl_model_key] = new_lbl_if

    st.subheader("Object Detection Model")
    col1, col2 = st.columns(2)
    
    with col1:
        # Model interface selection
        current_obj_if = st.session_state.current_obj_model_select
        new_obj_if = st.selectbox(
            "Model Interface ID",
            options=model_interfaces,
            index=model_interfaces.index(current_obj_if),
            help="Identifier from model_interfaces.py (e.g. ollama-complex, vllm-complex)",
            key="obj_model_select",
            on_change=update_obj_model_selection
        )

        # Get current model's parameters
        current_obj_params = MODELS[new_obj_if].model_parameters()
        
        # Conditionally show URL input
        if 'api_base' in current_obj_params:
            st.session_state.model_config[CFG_obj_model_url_key] = st.text_input(
                "Model URL",
                value=st.session_state.model_config.get(CFG_obj_model_url_key, ""),
                help="Endpoint URL for the object detection model interface",
                key=f"obj_url_{new_obj_if}"  # Unique key based on selection
            )
        
    with col2:
        # Conditionally show Model Name input
        if 'model_to_use' in current_obj_params:
            st.session_state.model_config[CFG_obj_model_name_key] = st.text_input(
                "Model Name",
                value=st.session_state.model_config.get(CFG_obj_model_name_key, ""),
                help="Model name for the object detection model interface (e.g. llama3.2-vision:11b-instruct-fp16)",
                key=f"obj_name_{new_obj_if}"  # Unique key based on selection
            )
        
        # Conditionally show API Token input
        if 'api_key' in current_obj_params:
            st.session_state.model_config[CFG_obj_model_tkn_key] = st.text_input(
                "API Token/Key",
                value=st.session_state.model_config.get(CFG_obj_model_tkn_key, ""),
                help="Authentication token if required by the API. Leave empty to read from environment variables (e.g. OPENAI_API_KEY, VLLM_API_KEY)",
                type="password",
                key=f"obj_tkn_{new_obj_if}"  # Unique key based on selection
            )

    st.subheader("Auto-labeling Model")
    col3, col4 = st.columns(2)
    
    with col3:
        # Label model interface selection
        current_lbl_if = st.session_state.current_lbl_model_select
        new_lbl_if = st.selectbox(
            "Model Interface ID",
            options=label_interfaces,
            index=label_interfaces.index(current_lbl_if),
            help="Identifier from model_interfaces.py (e.g. openai-generic)",
            key="lbl_model_select",
            on_change=update_lbl_model_selection
        )

        # Get current label model's parameters
        current_lbl_params = MODELS[new_lbl_if].model_parameters()
        
        # Conditionally show URL input
        if 'api_base' in current_lbl_params:
            st.session_state.model_config[CFG_lbl_model_url_key] = st.text_input(
                "Model URL",
                value=st.session_state.model_config.get(CFG_lbl_model_url_key, ""),
                help="Endpoint URL for the auto-labeling model interface",
                key=f"lbl_url_{new_lbl_if}"  # Unique key based on selection
            )
        
    with col4:
        # Conditionally show Model Name input
        if 'model_to_use' in current_lbl_params:
            st.session_state.model_config[CFG_lbl_model_name_key] = st.text_input(
                "Model Name", 
                value=st.session_state.model_config.get(CFG_lbl_model_name_key, ""),
                help="Model name for the auto-labeling model interface (e.g. gpt-4o-mini)",
                key=f"lbl_name_{new_lbl_if}"  # Unique key based on selection
            )
        
        # Conditionally show API Token input
        if 'api_key' in current_lbl_params:
            st.session_state.model_config[CFG_lbl_model_tkn_key] = st.text_input(
                "API Token/Key",
                value=st.session_state.model_config.get(CFG_lbl_model_tkn_key, ""),
                help="Authentication token for the auto-labeling model interface. Leave empty to read from environment variables (e.g. OPENAI_API_KEY, VLLM_API_KEY)",
                type="password",
                key=f"lbl_tkn_{new_lbl_if}"  # Unique key based on selection
            )

    if st.button(label='Save Model Configuration', type='primary'):
        # Prepare final config with version
        final_config = {
            CFG_model_version_key: st.session_state.model_config.get(CFG_model_version_key, 1) + 1,
            CFG_obj_model_key: st.session_state.model_config[CFG_obj_model_key],
            CFG_lbl_model_key: st.session_state.model_config[CFG_lbl_model_key]
        }
        
        # Add existing parameters using direct key access
        for key in st.session_state.model_config:
            if key not in final_config and key.startswith((CFG_obj_model_key, CFG_lbl_model_key)):
                final_config[key] = st.session_state.model_config[key]

        # Save atomically
        tmp_path = f"{model_cfg_json_path}.tmp"
        with open(tmp_path, "w") as file:
            json.dump(final_config, file, indent=4)
        os.rename(tmp_path, model_cfg_json_path)
        
        st.session_state.app_state = "init"
        st.rerun()

    if st.button("Back"):
        st.session_state.app_state = "init"
        st.rerun()
