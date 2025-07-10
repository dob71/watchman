import streamlit as st
import json
import os
import sys
import random

# Pull in shared variables (file names, JSON object names, ...)
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))

from ui_common import *

def get_default_services():
    """Return default service structure with all parameters preserved when inactive"""
    return {
        CFG_loc_svc_name: {
            'active': False,
            CFG_osvc_name_key: CFG_loc_svc_name,
            CFG_osvc_msgtpl_key: "I saw [OBJNAME] [TIMEAGO] ago on the [CHANNEL] camera. [LOCATION]",
            CFG_osvc_age_out_key: 10800,
            CFG_osvc_def_off_key: True,
            CFG_osvc_skip_chan_key: []
        },
        CFG_alrt_svc_name: {
            'active': False,
            CFG_osvc_name_key: CFG_alrt_svc_name,
            CFG_osvc_msgtpl_key: "I see [OBJNAME] on the [CHANNEL] camera. [LOCATION]",
            CFG_osvc_age_out_key: 60,
            CFG_osvc_mtime_key: 300,
            CFG_osvc_def_off_key: True,
            CFG_osvc_skip_chan_key: []
        },
        CFG_dset_svc_name: {
            'active': False,
            CFG_osvc_name_key: CFG_dset_svc_name,
            CFG_osvc_pname_key: f"{DATA_DIR}/dataset",
            CFG_osvc_def_off_key: True,
            CFG_osvc_msgtpl_key: "",
            CFG_osvc_age_out_key: 0,
            CFG_osvc_skip_chan_key: []
        }
    }

# Create objects.json file
def output_objects_json(objects_dict, model, new_version):
    objects = []
    for obj_id, obj_data in objects_dict.items():
        active_services = []
        for svc in obj_data['svcs'].values():
            if svc.get('active', False):
                svc_to_save = svc.copy()
                if 'active' in svc_to_save:
                    del svc_to_save['active']
                active_services.append(svc_to_save)
        
        objects.append({
            CFG_obj_id_key: obj_id,
            CFG_obj_names_key: [x.strip() for x in obj_data['names'].split(',')],
            CFG_obj_desc_key: obj_data['desc'],
            CFG_obj_svcs_key: active_services
        })

    output = {
        CFG_obj_version_key: new_version,
        CFG_obj_objects_key: objects
    }

    output_json = json.dumps(output, indent=4)
    tmp_path = f"{objects_cfg_json_path}.tmp"
    with open(tmp_path, "w") as file:
        file.write(output_json)
    os.rename(tmp_path, objects_cfg_json_path)
    print(output_json)

# Read objects.json to pre-populate the values
def read_objects_json():
    objects_dict = {}
    version = 1
    if os.path.exists(objects_cfg_json_path):
        with open(objects_cfg_json_path, "r") as file:
            data = json.load(file)
            version = data[CFG_obj_version_key]
            for obj in data[CFG_obj_objects_key]:
                obj_id = obj[CFG_obj_id_key]
                # Merge stored config with default services
                default_services = get_default_services()
                stored_services = {item[CFG_osvc_name_key]: item for item in obj[CFG_obj_svcs_key]}
                
                merged_services = {}
                for svc_name, default_svc in default_services.items():
                    is_active = svc_name in stored_services
                    merged_services[svc_name] = {
                        **default_svc,
                        **stored_services.get(svc_name, {}),
                        'active': is_active
                    }

                objects_dict[obj_id] = {
                    'names': ','.join(obj[CFG_obj_names_key]),
                    'desc': obj[CFG_obj_desc_key],
                    'svcs': merged_services
                }
    return objects_dict, version

# Add a new object with unique ID
def add_object():
    new_id = f"obj_{hex(random.getrandbits(64))[2:]}"
    st.session_state.objects[new_id] = {
        'names': f"New object, alt name...",
        'desc': "Object description",
        'svcs': get_default_services()
    }
    st.session_state.selected_object = new_id
    st.rerun()

def channel_multiselect(service_name, help_text, obj_svcs, obj_id, channel_options):
    current_skip = [
        (chan_id, chan_name)
        for chan_id in obj_svcs.get(service_name, {}).get(CFG_osvc_skip_chan_key, [])
        for chan_id_option, chan_name in channel_options if chan_id_option == chan_id
    ]
    
    session_key = f"cskip_{service_name}_{obj_id}"
    valid_channels = {chan[0] for chan in channel_options}
    filtered_skip = [c for c in current_skip if c[0] in valid_channels]
    
    # Removed manual session state initialization to prevent conflict
    def update_session():
        new_value = [c[0] for c in st.session_state[session_key]]
        st.session_state.objects[obj_id]['svcs'][service_name][CFG_osvc_skip_chan_key] = new_value

    return st.multiselect(
        "Channels to skip",
        options=channel_options,
        default=filtered_skip,
        format_func=lambda x: x[1],
        help=help_text,
        key=session_key,
        on_change=update_session
    )

def get_obj_svcs_dict(obj_id):
    sources_data = load_data(imgsrc_cfg_json_path)
    objects_data = load_data(objects_cfg_json_path) if os.path.exists(objects_cfg_json_path) else {CFG_obj_objects_key: []}
    channels, objects = extract_ids(sources_data, objects_data)
    channel_options = [(chan, chan_id_to_name(sources_data, chan)) for chan in channels]
    
    obj_data = st.session_state.objects[obj_id]
    svcs = obj_data['svcs']

    # Ensure all services exist with defaults
    for svc_name, default_svc in get_default_services().items():
        if svc_name not in svcs:
            svcs[svc_name] = default_svc
    
    with st.container(border=True):
        # Location service
        service_data = svcs[CFG_loc_svc_name]
        location_on = st.toggle("Activate location service",
                              key=f"location_toggle_{obj_id}",
                              value=service_data['active'],
                              help="The location service allows to keep track of the location of the object and report it when requested.")

        msgtpl = st.text_input("Output message", 
                             key=f"msgtpl_{obj_id}",
                             value=service_data.get(CFG_osvc_msgtpl_key, ""),
                             help="Message template using variables: [LOCATION] - object position, [CHANNEL] - camera name, [OBJNAME] - object name, [TIMEAGO] - time since detection, [OBJECT] - name as in the question")
        
        age_out = st.number_input("Age out (secs)", min_value=0,
                                key=f"age_out_{obj_id}",
                                value=service_data.get(CFG_osvc_age_out_key, 0),
                                format="%d",
                                help="How long to keep location updates (0 = never expire)")
        
        def_off = st.selectbox("Default off", boolean_selection,
                            key=f"def_off_{obj_id}",
                            index=boolean_selection.index(service_data.get(CFG_osvc_def_off_key, True)),
                            help="Start with this service disabled by default?")
        
        selected_channels = channel_multiselect(CFG_loc_svc_name, "Select channels to exclude from the location tracking", 
                                              svcs, obj_id, channel_options)
        
        svcs[CFG_loc_svc_name] = {
            'active': location_on,
            CFG_osvc_name_key: CFG_loc_svc_name,
            CFG_osvc_msgtpl_key: msgtpl,
            CFG_osvc_age_out_key: age_out,
            CFG_osvc_def_off_key: def_off,
            CFG_osvc_skip_chan_key: [chan[0] for chan in selected_channels]
        }

    with st.container(border=True):
        # Alert service
        service_data = svcs[CFG_alrt_svc_name]
        alert_on = st.toggle("Activate alert service", 
                           key=f"alert_toggle_{obj_id}",
                           value=service_data['active'],
                           help="The alert service allows to make an announcement when the object is detected")

        msgtpl = st.text_input("Output message", 
                             key=f"msgtpl_alert_{obj_id}",
                             value=service_data.get(CFG_osvc_msgtpl_key, ""),
                             help="Message template using variables: [LOCATION] - object position, [CHANNEL] - camera name, [OBJNAME] - object name, [TIMEAGO] - time since detection, [OBJECT] - default object name")
        
        age_out = st.number_input("Age out (secs)", min_value=0,
                                key=f"age_out_alert_{obj_id}",
                                value=service_data.get(CFG_osvc_age_out_key, 0),
                                format="%d",
                                help="How long to keep alert records (0 = never expire)")
        
        mute_time = st.number_input("Mute time (secs)", min_value=0,
                                  key=f"mute_time_alert_{obj_id}",
                                  value=service_data.get(CFG_osvc_mtime_key, 300),
                                  format="%d",
                                  help="Cooldown period between alerts for the same object")
        
        def_off = st.selectbox("Default off", boolean_selection,
                            key=f"def_off_alert_{obj_id}",
                            index=boolean_selection.index(service_data.get(CFG_osvc_def_off_key, True)),
                            help="Start with alerts disabled by default?")
        
        selected_channels = channel_multiselect(CFG_alrt_svc_name, "Select channels to exclude from the alerts", 
                                              svcs, obj_id, channel_options)

        svcs[CFG_alrt_svc_name] = {
            'active': alert_on,
            CFG_osvc_name_key: CFG_alrt_svc_name,
            CFG_osvc_msgtpl_key: msgtpl,
            CFG_osvc_age_out_key: age_out,
            CFG_osvc_mtime_key: mute_time,
            CFG_osvc_def_off_key: def_off,
            CFG_osvc_skip_chan_key: [chan[0] for chan in selected_channels]
        }

    with st.container(border=True):
        # Dataset service
        service_data = svcs[CFG_dset_svc_name]
        dataset_on = st.toggle("Activate dataset service", 
                             key=f"dataset_toggle_{obj_id}",
                             value=service_data['active'],
                             help="The dataset service collects data for model training")

        pname = st.text_input("Dataset path",
                            key=f"dataset_pname_{obj_id}",
                            value=service_data.get(CFG_osvc_pname_key, "./.data/dataset"),
                            help="Path to store dataset files")
        
        def_off = st.selectbox("Default off", boolean_selection,
                            key=f"dataset_def_off_{obj_id}",
                            index=boolean_selection.index(service_data.get(CFG_osvc_def_off_key, True)),
                            help="Start with this service disabled by default?")
        
        selected_channels = channel_multiselect(CFG_dset_svc_name, "Select channels to exclude from the data collection", 
                                              svcs, obj_id, channel_options)

        svcs[CFG_dset_svc_name] = {
            'active': dataset_on,
            CFG_osvc_name_key: CFG_dset_svc_name,
            CFG_osvc_pname_key: pname,
            CFG_osvc_def_off_key: def_off,
            CFG_osvc_skip_chan_key: [chan[0] for chan in selected_channels],
            CFG_osvc_msgtpl_key: "OBJNAME:[OBJNAME] CHANNEL:[CHANNEL] LOCATION:[LOCATION]",
            CFG_osvc_age_out_key: 0
        }

    return svcs

# handle removal of the objects
def handle_object_removal(obj_id):
    if len(st.session_state.objects) > 1:  # keep one object at a minimum
        del st.session_state.objects[obj_id]
        if st.session_state.objects:
            st.session_state.selected_object = list(st.session_state.objects.keys())[0]
        else:
            st.session_state.selected_object = None

def configure_objects_sm(key):
    st.header("Configure Objects of interest")
    
    # Initialize session state only once when entering the UI
    if "objects" not in st.session_state:
        st.session_state.objects, st.session_state.objects_version = read_objects_json()
    
    # Reset selection if invalid
    if "selected_object" not in st.session_state or \
       (st.session_state.objects and st.session_state.selected_object not in st.session_state.objects):
        st.session_state.selected_object = (
            list(st.session_state.objects.keys())[0] 
            if st.session_state.objects 
            else None
        )

    # Update callback to preserve selection
    def update_selection():
        st.session_state.selected_object = st.session_state.object_select

    st.subheader("Select Object:")
    col1, col2, col3 = st.columns([7.5, 1, 2])
    
    with col1:
        if st.session_state.objects:
            st.session_state["object_select"] = st.session_state.selected_object

            selected_object = st.selectbox(
                "Select object:",
                options=list(st.session_state.objects.keys()),
                format_func=lambda oid: st.session_state.objects[oid]['names'].split(',')[0],
                label_visibility='collapsed',
                key="object_select",
                on_change=update_selection
            )
        else:
            st.selectbox(
                "Select object:",
                options=[],
                label_visibility='collapsed',
                disabled=True,
                help="No objects available"
            )
            st.session_state.selected_object = None
    
    with col2:
        if st.button("Add"):
            add_object()
    
    with col3:
        if st.button("Remove"):
            if st.session_state.objects and st.session_state.selected_object in st.session_state.objects:
                handle_object_removal(st.session_state.selected_object)
                st.rerun()

    if st.session_state.objects and st.session_state.selected_object:
        obj_id = st.session_state.selected_object
        obj_data = st.session_state.objects[obj_id]
        
        st.subheader("Object Configuration")
        
        new_names = st.text_input(
            "Object names (comma separated)",
            value=obj_data['names'],
            help="Comma separated list of the names for referencing the object, the first entry is the default, must be unique across all objects"
        )
        if new_names != obj_data['names']:
            obj_data['names'] = new_names
            st.rerun()
        
        new_desc = st.text_input(
            "Description",
            value=obj_data['desc'],
            help="Verbal description of the object for the AI model, for example: a black and white tuxedo cat"
        )
        if new_desc != obj_data['desc']:
            obj_data['desc'] = new_desc
        
        obj_data['svcs'] = get_obj_svcs_dict(obj_id)

    if st.button('Apply All Changes'):
        # Process auto-generated object IDs
        new_objects = {}
        used_ids = set()
        all_names = []
        
        for obj_id, obj_data in st.session_state.objects.items():
            # Generate base ID from first name if it's an auto-generated ID
            if obj_id.startswith("obj_"):
                # Get first name and sanitize
                base_name = obj_data['names'].split(',')[0].strip().lower()
                base_id = ''.join(c for c in base_name if c.isalnum())
                
                # Handle empty base ID case
                if not base_id:
                    base_id = obj_id
            else:
                base_id = obj_id

            used_ids.add(base_id)
            new_objects[base_id] = obj_data
            all_names.extend([name.strip().lower() for name in obj_data['names'].split(',')])

        # Check if any random IDs remain
        for obj_id in used_ids:
            if obj_id.startswith("obj_"):
                st.error(f"Error: cannot generate unique ID for object {new_objects[obj_id]['names'].split(',')[0]}.")
                return

        # Check for duplicate names
        name_counts = {}
        for name in all_names:
            name_counts[name] = name_counts.get(name, 0) + 1
            
        duplicates = {name for name, count in name_counts.items() if count > 1}
        if duplicates:
            st.error(f"Object names must be unique. Duplicates: {', '.join(sorted(duplicates))}")
        else:
            # Update session state with new IDs
            st.session_state.objects = new_objects
            output_objects_json(st.session_state.objects, [{}], st.session_state.objects_version + 1)
            st.session_state.app_state = "init"
            st.rerun()

    if st.button("Back"):
        st.session_state.app_state = "init"
        st.rerun()
