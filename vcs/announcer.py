import os
import sys
import time
import json
import requests
import shlex
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Pull in shared variables (file names, JSON object names, ...) and the the model interface classes
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))
from shared_settings import *
from vcs_lib import *

# Figure the path to the data folders depending on where we run
DATA_DIR = ''
if not os.path.exists('/.dockerenv'):
    load_dotenv('./.env')
DATA_DIR = os.getenv('DATA_DIR', DATA_DIR)

# Alexa skill ID for request verification
NOTIFY_ME_ID = os.getenv('NOTIFY_ME_ID')
ALERT_SCRIPT = os.getenv('ALERT_SCRIPT')
if (NOTIFY_ME_ID is None or len(NOTIFY_ME_ID) == 0) and (ALERT_SCRIPT is None or len(ALERT_SCRIPT) == 0):
    print(f"Unable to continue, please specify NOTIFY_ME_ID or ALERT_SCRIPT in the project's .env file!")
    exit(1)

# We'll need the images and config folders.
EVTDIR = f"{DATA_DIR}/{EVT_dir}"

# Aler JSON file name
ALERT_JSON = f"{CFG_alrt_svc_name}.json"

# Notify Me API URL, see https://www.thomptronics.com/about/notify-me
NOTIFY_ME_URL = "https://api.notifymyecho.com/v1/NotifyMe"

# Have Alexa do the announcement, return True if announcement is done successfully
def do_announcement(msg):
    res = False

    # call script, normaly thiis would do a verbal announcement
    if ALERT_SCRIPT is not None and len(ALERT_SCRIPT) > 0:
        if os.system(f"{ALERT_SCRIPT} {shlex.quote(msg)}") == 0:
            res = True

    # send NotifyMe notification (that does a chime and adds notification the user
    # ask Alexa to read by saying "Alexa, what are my notifications")
    if NOTIFY_ME_ID is not None and len(NOTIFY_ME_ID) > 0:
        data = {
            "notification": msg,
            "accessCode": NOTIFY_ME_ID
        }
        try:
            response = requests.post(NOTIFY_ME_URL, json=data, timeout=10)
            if int(response.status_code / 100)  == 2:
                res = True
            else:
                print(f"{sys._getframe().f_code.co_name}: error sending alert {response.status_code}, {response.text}")
        except Exception as e:
            print(f"{sys._getframe().f_code.co_name}: error sending alert: {e}")

    return res

# We see the alert file. If th ealert has already be done within the mute time
# we just delete the file, otherwise make the notification.
# The mute time has to be read from the obj.json in the folder.
def process_alert(alert_file_pn):
    pn = alert_file_pn[:-(len(ALERT_JSON) + 1)]
    obj_json_pn = f"{pn}/{EVT_obj_file_name}"
    try:
        with open(obj_json_pn, 'r') as f:
            o = json.load(f)
        obj_names = o[EVT_obj_names_key]
        obj_names = [ x.lower() for x in obj_names ]
        obj_name = obj_names[0]
    except Exception as e:
        print(f"{sys._getframe().f_code.co_name}: ignoring alert {alert_file_pn}, error getting object info: {e}")
        try: os.unlink(alert_file_pn)
        except: pass
        return
    try:
        with open(alert_file_pn, 'r') as f:
            alert_data = json.load(f)
        mute_time = alert_data[EVT_alrt_mute_time_key]
    except Exception as e:
        print(f"{sys._getframe().f_code.co_name}: ignoring alert {alert_file_pn}, error getting alert data: {e}")
        try: os.unlink(alert_file_pn)
        except: pass
        return
    # Check if the previos alert here was within the mute time
    alert_done_pn = f"{pn}/{CFG_alrt_svc_name}_done.json"
    modified_ago = get_modified_time_ago(alert_done_pn)
    # rename the new alert into alert_done.json if want the mute time to start ony if the object
    # is not detected anymore, alternatively, just delete the new alert if within the mute time window
    try:
        os.rename(alert_file_pn, alert_done_pn)
    except:
        print(f"{sys._getframe().f_code.co_name}: unable to do atomic rename of {alert_file_pn} to {alert_done_pn}")
    if modified_ago == -1 or modified_ago > mute_time:
        msg = construct_evt_msg(alert_data, obj_name, CFG_alrt_svc_name)
        if not do_announcement(msg):
            # if failed to announce, just remove the alert_done.json file and hope the alert is triggered again
            print(f"{sys._getframe().f_code.co_name}: error generating alert for {msg}")
            try: os.unlink(alert_done_pn)
            except: pass
    return

class AlertHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        # we do rename, so have to watch the dir change events
        if event.is_directory:
            file_path = f"{event.src_path}/{ALERT_JSON}"
            if os.path.exists(file_path):
                process_alert(file_path)

def watch_folder(path_to_watch):
    observer = Observer()
    event_handler = AlertHandler()
    observer.schedule(event_handler, path=path_to_watch, recursive=True)
    
    print(f"Watching folder: {path_to_watch}")
    observer.start()
    try:
        while True:
            pass  # Keep the script running
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Set the folder to watch
watch_folder(os.path.dirname(EVTDIR))
