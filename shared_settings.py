# This file contains files, directories and JSON object names that are shared between
# the components of the system. This file should be copied alongside the app script when
# creating the docker container for each service.

# Config UI values that are shared
CFG_dir = 'sysconfig'            # config files folder location
CFG_imager = 'sources.json'      # video channels config file
CFG_objects = 'objects.json'     # objects of interest config file
# imager config JASON values
CFG_version_key = "version"      # config update counter (for detecting changes)
CFG_channels_key = 'channels'    # name of the channel list object in config JSON
CFG_chan_id_key = 'channel'      # channel ID (used to name folder w/ the channel image data)
CFG_chan_url_key = "url"         # URL to pull the image from
CFG_chan_name_key = "name"       # channel name (for use in speech)
CFG_chan_upd_int_key = "upd_int" # key for the image update interval in channels
CFG_DEF_upd_int = 2              # default update interval for channels (in number of IMG_poll_int_ms intervals)

# Imager values that are shared
IMG_dir = 'images'     # locaton of the imager folder
IMG_poll_int_ms = 1000 # how often to the imager loop is called
IMG_json_file_name = 'image.json' # name of the JSON file w/ image data under the channel folder
IMG_chan_key = 'cid'   # Channel ID key
IMG_name_key = 'name'  # Verbal description of the channel
IMG_data_key = 'data'  # Image data (base64 encoded)
IMG_time_key = 'time'  # will use epoch time as we will likely report differential
IMG_iter_key = 'iter'  # iteraration number when the image is captured

