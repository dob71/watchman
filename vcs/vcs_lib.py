# Shared routines for VCS files
import os
import sys
import time
import re
import humanize
import datetime as dt

# Pull in shared variables (file names, JSON object names, ...) and the the model interface classes
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))
from shared_settings import *

# Gets the number of seconds since the file was last modified (-1 if error)
def get_modified_time_ago(filepath):
    try: 
        modification_time = os.path.getmtime(filepath)
        current_time = time.time()
        time_difference = current_time - modification_time
    except:
        time_difference = -1
    return time_difference

# Constructs event message from the event data
def construct_evt_msg(evt_data, ref_name, service):
    msg = evt_data.get(EVT_msg_key, f"invalid data for {ref_name} {service}")
    try:
        timeago_sec = time.time() - evt_data[EVT_in_time_key]
        delta = dt.timedelta(seconds=int(timeago_sec))
        timeago_human = humanize.naturaldelta(delta, minimum_unit="seconds")
    except:
        timeago_human = "unknown time period"
    d = {'TIMEAGO': timeago_human, 'OBJECT': ref_name}
    msg = re.sub(r'\[([^\]]*)\]', lambda x:d.get(x.group(1)) if x.group(1) in d.keys() else f"[{x.group(1)}]", msg)
    return msg
