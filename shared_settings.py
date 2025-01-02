# This file contains global vars specifying files & directory names, JSON object structure,
# e.t.c for shared between the components of the system. This file should be copied alongside
# the app script when creating the docker container for each service.

# Config UI values that are shared
CFG_dir = 'sysconfig'            # config files folder location
CFG_imager = 'sources.json'      # video channels config file
CFG_objects = 'objects.json'     # objects of interest config file
# imager config JASON values
CFG_version_key = "version"      # config update counter (for detecting changes)
CFG_channels_key = 'channels'    # name of the channel list object in config JSON
# imager config JASON values for each entry in the channel list
CFG_chan_id_key = 'channel'      # channel ID (used to name folder w/ the channel image data)
CFG_chan_url_key = "url"         # URL to pull the image from
CFG_chan_name_key = "name"       # channel name (for use in speech)
CFG_chan_upd_int_key = "upd_int" # key for the image update interval in channels
CFG_DEF_upd_int = 2              # default update interval for channels (in number of IMG_poll_int_ms intervals)
# objects config JASON
CFG_obj_version_key = "version"  # config update counter (for detecting changes)
CFG_obj_model_key = "model"      # ML model interface ID string (see in the code, default "ollama-simple")
CFG_obj_objects_key = "objects"  # list of objects of interest
# object config JASON keys for each entry in the list of objects of interest
CFG_obj_id_key = "obj_id"        # unique ID of the object of interest (single word, used as the object dir name in the events folder)
CFG_obj_names_key = "names"      # names of the object of interest (object name coming from Alexa should match one of them to get the answer)
CFG_obj_desc_key = "desc"        # object description string suitable for identifying the object by the model (transparently passed to the model interface class)
CFG_obj_svcs_key = "obj_svcs"    # list of services (only location and alert for now) configured for the object of interest
# allowed service names
CFG_loc_svc_name = "location"    # name of the location service (used to generate name of files in the events folder)
CFG_alrt_svc_name = "alert"      # name of the alert service (used to generate name of files in the events folder)
CFG_dset_svc_name = "dataset"    # for debugging, can be used to collect info on positive detection hits for future fine-tuning
# keys for use in service entries under object
CFG_osvc_name_key = "osvc_name"  # name of the service (CFG_loc_svc_name, CFG_alrt_svc_name)
CFG_osvc_msgtpl_key = "msgtpl"   # template of the verbal message to send to Alexa for the service
                                 # [LOCATION] - location description, [CHANNEL] - channel name, [OBJNAME] - first name from CFG_obj_names_key list
                                 # [TIMEAGO] - how log ago, [OBJECT] - object name as was in the question
CFG_osvc_age_out_key = "age_out" # number of seconds after which to remove the event file for this service
CFG_osvc_skip_chan_key = "skip_ch"# list of channel IDs to skip this service on (optional key)
CFG_osvc_mtime_key = "mute_time" # number of seconds to mute the alert after issuing it (for alert service only, i.e. optional key)
CFG_osvc_def_off_key = "def_off" # true to have the service off by default (ask Alexa to turn on when needed)
CFG_osvc_pname_key = "pname"     # for debugging purposes (used w/ special "dataset" service for capturing all positive detection results)

# Imager values that are shared
IMG_poll_int_ms = 1000 # how often to the imager loop is called
IMG_json_file_name = 'image.json' # name of the JSON file w/ image data under the channel folder
IMG_off_file_name = 'image.off'   # name of the file that stops imager from polling from channel URL
IMG_file_name = 'image.jpg'  # where to store raw image for debugging
IMG_dir = 'images'     # locaton of the imager folder
IMG_chan_key = 'cid'   # Channel ID key
IMG_name_key = 'name'  # Verbal description of the channel
IMG_data_key = 'data'  # Image data (base64 encoded)
IMG_time_key = 'time'  # will use epoch time as we will likely report differential
IMG_iter_key = 'iter'  # iteraration number when the image is captured

# Orchestrator shared values
ORCH_poll_int_ms = 500 # for alerts it might be useful to keep this low
# Event DB files/folders names
EVT_dir = 'events'             # locaton of the events DB folder
EVT_obj_file_name = 'obj.json' # obect description file name
# Event DB keys shared between all services
EVT_obj_id_key = "o_id"     # object ID (from CFG_obj_id_key, in events/chan/obj/obj.json)
EVT_obj_names_key = "names" # names of the object of interest from config (object name coming from Alexa should match one of them to get the answer)
EVT_obj_desc_key = "o_desc" # object description string from config (in events/chan/obj/obj.json)
EVT_obj_cid_key = "o_cid"   # object's channel ID from the config (in events/chan/obj/obj.json)
EVT_obj_cname_key = "o_cname" # object's channel name from the config (in events/chan/obj/obj.json)
EVT_osvc_list_key = "osvc_list"  # list of services (names) enabled (not filtered out for the obj on the channel, in events/chan/obj/obj.json)
EVT_osvc_key = "osvc_name"  # event service name from CFG_osvc_name_key
EVT_c_name_key = "c_name"   # event channel name (for use in speech)
EVT_in_time_key = "in_time" # epoch time when the event was reported
EVT_msg_key = "msg"         # message to play for the event
EVT_alrt_mute_time_key = "mtime" # for alerts only, time in seconds mute after reporting

# Individual object of interest config schema (it's getting complex, so better use schema for validation)
CFG_obj_schema = {
    "type": "object",
    "properties": {
        CFG_obj_id_key: {"type": "string"},
        CFG_obj_names_key: {"type": "array", "items": {"type": "string"}, "minItems": 1 },
        CFG_obj_desc_key: {"type": "string"},
        CFG_obj_svcs_key: {"type": "array", "items": 
            {"type": "object", "properties": {
                CFG_osvc_name_key: {"type": "string", "enum": [CFG_loc_svc_name, CFG_alrt_svc_name, CFG_dset_svc_name]},
                CFG_osvc_msgtpl_key: {"type": "string"},
                CFG_osvc_age_out_key: {"type": "integer", "minimum": 0},
                CFG_osvc_def_off_key: {"type": "boolean"},
                CFG_osvc_skip_chan_key: {"type": "array", "items": {"type": "string"}},
                CFG_osvc_mtime_key: {"type": "integer", "minimum": 0},
                },
            "required": [CFG_osvc_name_key, CFG_osvc_msgtpl_key, CFG_osvc_age_out_key, CFG_osvc_def_off_key],
            },
        },
    },
    "required": [CFG_obj_id_key, CFG_obj_names_key, CFG_obj_desc_key],
}
