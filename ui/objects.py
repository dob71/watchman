import streamlit as st
import json
import os
import sys

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))

from ui_common import *

# Create objects.json file
def output_objects_json(obj_id_input, obj_names_input, desc_input, obj_svcs_input, model, new_version):
    objects = list()
    for i in range(len(obj_id_input)):
        objects.append(
            {
                CFG_obj_id_key: obj_id_input[i],
                CFG_obj_names_key: [x.strip() for x in obj_names_input[i].split(',')],
                CFG_obj_desc_key: desc_input[i],
                CFG_obj_svcs_key: list(obj_svcs_input[i].values())
            }
        )

    # Define the final JSON structure
    output = {
        CFG_obj_version_key: new_version,
        CFG_obj_model_key: model[0],
        CFG_obj_objects_key: objects
    }

    # Convert the structure to a JSON string
    output_json = json.dumps(output, indent=4)

    # Save the JSON output to a file
    with open(objects_cfg_json_path, "w") as file:
        file.write(output_json)

    # Print the JSON output
    print(output_json)

# Read objects.json to pre-populate the values in the input boxes
# Return the number of objects which is determined by the number of entries in objects.json and the current version number.
def read_objects_json(obj_id_input, obj_names_input, desc_input, obj_svcs_input, model):
    if not os.path.exists(objects_cfg_json_path):
        # Provide default data as a fallback when objects.json does not exist
        st.session_state.num_objects = 0
        add_object(obj_id_input, obj_names_input, desc_input, obj_svcs_input)
        version = 1
    else:
        with open(objects_cfg_json_path, "r") as file:
            data = json.load(file)
            model[0] = data[CFG_obj_model_key]

            # Populate the lists
            for obj in data[CFG_obj_objects_key]:
                obj_id_input.append(obj[CFG_obj_id_key])
                obj_names_input.append(','.join(obj[CFG_obj_names_key]))
                desc_input.append(obj[CFG_obj_desc_key])
                svcs_dict = dict()
                for item in obj[CFG_obj_svcs_key]:
                    svcs_dict[item[CFG_osvc_name_key]] = item
                obj_svcs_input.append(svcs_dict)
            
            version = data[CFG_obj_version_key]
    
    return (len(obj_id_input), version, model)

# Add an extra object
def add_object(obj_id_input, obj_names_input, desc_input, obj_svcs_input):
    obj_id_input.append("Unique lowercase word (used to name object folders)")
    obj_names_input.append("Comma separated list of various ways you'd reference the object: my cat, a cat,...")
    desc_input.append("Verbal description of the object for the AI model")
    obj_svcs_input.append({CFG_loc_svc_name : {  #list of dictionaries of string:dictionaries pairs
                CFG_osvc_name_key: CFG_loc_svc_name,
                CFG_osvc_msgtpl_key: "I saw [OBJNAME] [TIMEAGO] ago on the [CHANNEL] camera. [LOCATION]",
                CFG_osvc_age_out_key: 10800,
                CFG_osvc_def_off_key: True
            }})
    st.session_state.num_objects += 1

# Get the object service dictionary associated with object at a specific index 
def get_obj_svcs_dict(obj_svcs_input, index):
    with st.container(border=True):
        location_on = st.toggle("Activate location service",
                                key = "location_toggle" + str(index), 
                                value=(CFG_loc_svc_name in obj_svcs_input[index]))

        msgtpl = st.text_input("Output message", key = "msgtpl" + str(index),
                                value = (
                                    ""  # Default value
                                    if CFG_loc_svc_name not in obj_svcs_input[index] or CFG_osvc_msgtpl_key not in obj_svcs_input[index][CFG_loc_svc_name] 
                                    else obj_svcs_input[index][CFG_loc_svc_name][CFG_osvc_msgtpl_key]
                                ),
                               )
        age_out = st.number_input("Age out (secs)", min_value = 0, key = "age_out" + str(index),
                                    value = (
                                        0  # Default value
                                        if CFG_loc_svc_name not in obj_svcs_input[index] or CFG_osvc_age_out_key not in obj_svcs_input[index][CFG_loc_svc_name] 
                                        else obj_svcs_input[index][CFG_loc_svc_name][CFG_osvc_age_out_key]
                                    ),                            
                                    format="%d")
        def_off = st.selectbox("Default off", boolean_selection, key = "def_off" + str(index),
                                index = (
                                    0 # Default value
                                    if CFG_loc_svc_name not in obj_svcs_input[index] or CFG_osvc_def_off_key not in obj_svcs_input[index][CFG_loc_svc_name] 
                                    else boolean_selection.index(obj_svcs_input[index][CFG_loc_svc_name][CFG_osvc_def_off_key])
                                )
                               )
        skip_ch = st.text_input("Channels to skip (comma separated list)", key = "skip_ch" + str(index),
                                value = (
                                    ""  # Default value
                                    if CFG_loc_svc_name not in obj_svcs_input[index] or CFG_osvc_skip_chan_key not in obj_svcs_input[index][CFG_loc_svc_name] 
                                    else ','.join(obj_svcs_input[index][CFG_loc_svc_name][CFG_osvc_skip_chan_key])
                                ),
                               )
        
        obj_svcs_input[index][CFG_loc_svc_name] = {  #list of dictionaries of string:dictionaries pairs
                                        CFG_osvc_name_key: CFG_loc_svc_name,
                                        CFG_osvc_msgtpl_key: msgtpl,
                                        CFG_osvc_age_out_key: age_out,
                                        CFG_osvc_def_off_key: def_off,
                                        CFG_osvc_skip_chan_key: [x.strip() for x in skip_ch.split(',')]
                                    }
        
        #if skip_ch contains only empty string, remove it
        if obj_svcs_input[index][CFG_loc_svc_name][CFG_osvc_skip_chan_key][0] == "":  
            obj_svcs_input[index][CFG_loc_svc_name].pop(CFG_osvc_skip_chan_key, None)

        if not location_on:
            obj_svcs_input[index].pop(CFG_loc_svc_name, None)

    with st.container(border=True):
        alert_on = st.toggle("Activate alert service", key = "alert_toggle" + str(index), value=(CFG_alrt_svc_name in obj_svcs_input[index]))

        msgtpl = st.text_input("Output message", key = "msgtpl_alert" + str(index),
                                value = (
                                    ""  # Default value
                                    if CFG_alrt_svc_name not in obj_svcs_input[index] or CFG_osvc_msgtpl_key not in obj_svcs_input[index][CFG_alrt_svc_name] 
                                    else obj_svcs_input[index][CFG_alrt_svc_name][CFG_osvc_msgtpl_key]
                                ),
                              )
        age_out = st.number_input("Age out (secs)", min_value = 0, key = "age_out_alert" + str(index),
                                    value = (
                                        0  # Default value
                                        if CFG_alrt_svc_name not in obj_svcs_input[index] or CFG_osvc_age_out_key not in obj_svcs_input[index][CFG_alrt_svc_name] 
                                        else obj_svcs_input[index][CFG_alrt_svc_name][CFG_osvc_age_out_key]
                                    ),                            
                                    format="%d")
        mute_time = st.number_input("Mute time (secs)", min_value = 0, key = "mute_time_alert" + str(index),
                                    value = (
                                        600  # Default value
                                        if CFG_alrt_svc_name not in obj_svcs_input[index] or CFG_osvc_mtime_key not in obj_svcs_input[index][CFG_alrt_svc_name] 
                                        else obj_svcs_input[index][CFG_alrt_svc_name][CFG_osvc_mtime_key]
                                    ),                            
                                    format="%d")
        def_off = st.selectbox("Default off", boolean_selection, key = "def_off_alert" + str(index),
                                index = (
                                    0 # Default value
                                    if CFG_alrt_svc_name not in obj_svcs_input[index] or CFG_osvc_def_off_key not in obj_svcs_input[index][CFG_alrt_svc_name] 
                                    else boolean_selection.index(obj_svcs_input[index][CFG_alrt_svc_name][CFG_osvc_def_off_key])
                                )
                              )
        skip_ch = st.text_input("Channels to skip (comma separated list)", key = "skip_ch_alert" + str(index),
                                value = (
                                    ""  # Default value
                                    if CFG_alrt_svc_name not in obj_svcs_input[index] or CFG_osvc_skip_chan_key not in obj_svcs_input[index][CFG_alrt_svc_name] 
                                    else ','.join(obj_svcs_input[index][CFG_alrt_svc_name][CFG_osvc_skip_chan_key])
                                ),
                               )

        obj_svcs_input[index][CFG_alrt_svc_name] = {  #list of dictionaries of string:dictionaries pairs
                                        CFG_osvc_name_key: CFG_alrt_svc_name,
                                        CFG_osvc_msgtpl_key: msgtpl,
                                        CFG_osvc_age_out_key: age_out,
                                        CFG_osvc_mtime_key: mute_time,
                                        CFG_osvc_def_off_key: def_off,
                                        CFG_osvc_skip_chan_key: [x.strip() for x in skip_ch.split(',')] 
                                    }
        
        #if skip_ch contains only empty string, remove it
        if obj_svcs_input[index][CFG_alrt_svc_name][CFG_osvc_skip_chan_key][0] == "":  
            obj_svcs_input[index][CFG_alrt_svc_name].pop(CFG_osvc_skip_chan_key, None)

        if not alert_on:
            obj_svcs_input[index].pop(CFG_alrt_svc_name, None)

    return obj_svcs_input[index]

# handle removal of the objects
def handle_object_removal(index):
    if st.session_state.num_objects > 1:  #keep one object at a minimum
        st.session_state.obj_id_input.pop(index)
        st.session_state.obj_names_input.pop(index)
        st.session_state.desc_input.pop(index)
        st.session_state.obj_svcs_input.pop(index)
        st.session_state.num_objects -= 1
        st.rerun()

# Objects state machine section
def configure_objects_sm(key):
    st.header("Configure Objects of interest")
    if "num_objects" not in st.session_state:
        st.session_state.num_objects = 0

    with st.form(key=key):
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

        st.session_state.model[0] = st.text_input("AI Model Interface",
                                                  key="model_interface",
                                                  value=st.session_state.model[0])

        for i in range(st.session_state.num_objects):
            st.divider()
            st.subheader(f"Object {i}")
            st.session_state.obj_id_input[i] = st.text_input(f"Object ID ",
                                                            key="obj_id" + str(i),
                                                            value=st.session_state.obj_id_input[i])
            st.session_state.obj_names_input[i] = st.text_input(f"Object names (comma separated list)",
                                                                key="obj_names" + str(i),
                                                                value=st.session_state.obj_names_input[i])
            st.session_state.desc_input[i] = st.text_input("Description " + str(i),
                                                            key="desc" + str(i),
                                                            value=st.session_state.desc_input[i])
            st.session_state.obj_svcs_input[i] = get_obj_svcs_dict(st.session_state.obj_svcs_input, i)

            # Create a button to handle removal
            if st.form_submit_button(f"Remove Object {i}"):
                handle_object_removal(i)

        st.divider()
        if st.form_submit_button(label='Add object'):
            add_object(st.session_state.obj_id_input,
                        st.session_state.obj_names_input,
                        st.session_state.desc_input,
                        st.session_state.obj_svcs_input)
            st.rerun()  # Rerun to reflect changes immediately

        if st.form_submit_button(label='Confirm configuration', type='primary'):
            if len(st.session_state.obj_id_input) != len(set(st.session_state.obj_id_input)):
                st.error("Error: Object IDs should be unique. Please fix before confirmation.")
            else:
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

    # Add a "Back" button to go back to the start form
    if st.button("Back"):
        st.session_state.app_state = "init"
        st.rerun()
