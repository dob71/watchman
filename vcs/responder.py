import os
import sys
import json
import time
import humanize
import datetime as dt
import re
import shutil
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv

# Pull in shared variables (file names, JSON object names, ...) and the the model interface classes
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath("."))
from shared_settings import *

# Figure the path to the data folders depending on where we run
DATA_DIR = ''
if not os.path.exists('/.dockerenv'):
    load_dotenv('./.env')
    DATA_DIR = os.getenv('DATA_DIR')

# We'll need to access the evt and imager folders only.
EVTDIR = f"{DATA_DIR}/{EVT_dir}"
IMGDIR = f"{DATA_DIR}/{IMG_dir}"

# Alexa skill ID for request verification
ALEXA_SKILL_ID = os.getenv('ALEXA_SKILL_ID')
if len(ALEXA_SKILL_ID) == 0:
    print(f"Unable to continue, please specify ALEXA_SKILL_ID in the project's .env file!")
    exit(1)

# Special object to match all objects/services/channels
ANYOBJECT = ["everything", "anything"] # all objects
ANYCHANNEL = ["all", "everywhere"] # all channels

# Globals for alexa session state
DYN_VAL_UPDATE = 0 # Time when last updated
IN_LONG_SESSION = False # True from when launc intent was issuesd and until it's cancelled, overrides is_end to False
IN_DIALOG_SESSION = False # True while in skill response dialog session

# Construct comma separated string from a list, separating the last element w/ and
def nice_string_enum(l):
    msg = ""
    if len(l) > 1:
        msg += ", ".join(l[:-1]) + " and "
    msg += l[-1]
    return msg

# Return slot value name and id, "" if not found, for multi-match grabs the first seen.
def get_slot_val(slot):
    ret_id = ""
    ret = slot.get('value', "")
    try:
        rpa = slot["resolutions"]["resolutionsPerAuthority"]
        for r in rpa:
            if r["status"]["code"] == "ER_SUCCESS_MATCH":
                ret_id = r["values"][0]["value"]["id"]
                ret = r["values"][0]["value"]["name"]
                break # grab the first match
    except:
        pass
    return ret, ret_id

# Build response, if "obj_info" is specified, updates the ObjectNameType w/ the list of object choices,
# and ChannelNameType w/ the list of channel names.
# The dialog_delegate True is for delegating the next step of the dialog completion to Alexa.
def build_response(speech_text, obj_info=None, dialog_delegate=False, clear=False, elicit_slot=None, is_end=True):
    global IN_LONG_SESSION
    global DYN_VAL_UPDATE
    global IN_DIALOG_SESSION

    if IN_LONG_SESSION or IN_DIALOG_SESSION:
        is_end = False
    directives = []
    types = []
    obj_types = []
    channels = []
    if not obj_info is None:
        anything = {
            "id": ANYOBJECT[0],
            "name": {
                "value": ANYOBJECT[0],
                "synonyms": ANYOBJECT,
            },
        }
        obj_types = [ anything ]
        obj_types_ids_added = []
        all = {
            "id": ANYCHANNEL[0],
            "name": {
                "value": ANYCHANNEL[0],
                "synonyms": ANYCHANNEL,
            },
        }
        channels = [ all ]
        channels_ids_added = []
        for o in obj_info.values():
            try:
                obj_id = o[EVT_obj_id_key]
                obj_names = o[EVT_obj_names_key]
                obj_names = [ x.lower() for x in obj_names ]
                c_id = o[EVT_obj_cid_key].lower()
                c_name = o[EVT_obj_cname_key].lower()
            except Exception as e:
                print(f"{sys._getframe().f_code.co_name}: error getting values out of obj_info: {e}")
                continue
            if not obj_id in obj_types_ids_added:
                alexa_obj_val = {
                    "id": obj_id,
                    "name": {
                        "value": obj_names[0],
                        "synonyms": obj_names,
                    }
                }
                obj_types.append(alexa_obj_val)
                obj_types_ids_added.append(obj_id)
            if not c_id in channels_ids_added:
                alexa_chan_val = {
                    "id": c_id,
                    "name": {
                        "value": c_name,
                        "synonyms": [],
                    }
                }
                channels.append(alexa_chan_val)
                channels_ids_added.append(c_id)

    if len(obj_types) > 0:
        obj_type = {
                    "name": "ObjectNameType",
                    "values": obj_types,
        }
        types.append(obj_type)
    if len(channels) > 0:
        channel = {
                    "name": "ChannelNameType",
                    "values": channels,
        }
        types.append(channel)
    if dialog_delegate:
        directives.append({"type": "Dialog.Delegate"})
    elif not elicit_slot is None:
        upd_dyn_entries = {
                "type": "Dialog.ElicitSlot",
                "slotToElicit": elicit_slot,
        }
        directives.append(upd_dyn_entries)
    elif clear: # or is_end:
        upd_dyn_entries = {
                "type": "Dialog.UpdateDynamicEntities",
                "updateBehavior": "CLEAR",
        }
        directives.append(upd_dyn_entries)
        DYN_VAL_UPDATE = 0
    elif len(types) > 0:
        # Dialog.UpdateDynamicEntities do not work w/ other Dialog directives
        upd_dyn_entries = {
                "type": "Dialog.UpdateDynamicEntities",
                "updateBehavior": "REPLACE",
                "types": types,
        }
        directives.append(upd_dyn_entries)
        DYN_VAL_UPDATE = time.time()
    rsp = {
        "version": "1.0",
        "response": {
            "shouldEndSession": is_end
        },
    }
    print(f"session end: {is_end}")
    if not speech_text is None:
        output_speech = {
                "type": "PlainText",
                "text": speech_text
            }
        rsp["response"]["outputSpeech"] = output_speech
    if len(directives) > 0:
        rsp["response"]["directives"] = directives

    # print(json.dumps(rsp, indent=2))
    return jsonify(rsp)

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

# Collect info about all event objects from the events folder.
# Returns a dictionary where keys: path to obj folder, values: data from obj.json
def collect_evt_obj_info():
    obj_info = {}
    evt_chans = list(filter(lambda x : not x.startswith('.'), os.listdir(EVTDIR)))
    for ch in evt_chans:
        chan_dir = f"{EVTDIR}/{ch}"
        evt_chan_objs = list(filter(lambda x : not x.startswith('.'), os.listdir(chan_dir)))
        for eco in evt_chan_objs:
            eco_dir = f"{chan_dir}/{eco}"
            eco_file = f"{eco_dir}/{EVT_obj_file_name}"
            try:
                with open(eco_file, "r") as file:
                    obj_data = json.load(file)
            except json.JSONDecodeError as e:
                print(f"{sys._getframe().f_code.co_name}: file {eco_file}, JSON error on line {e.lineno}: {e.msg}")
                continue
            except Exception as e:
                print(f"{sys._getframe().f_code.co_name}: file {eco_file}, Failed to load JSON file: {e}")
                continue
            obj_info[eco_dir] = obj_data
    return obj_info

# Find object name matches and construct array of known objects. Requires passing obj_info from collect_evt_obj_info().
# The function finds the latest event for objects matching "object_name" and having th especified "service" configured.
# On the way it constructs the list of all object names available for the "service" specified (set "object_name" to None
# to do just that, can also set "service" to None to match any service).
# Returns tuple of
#    tracked_obj_list: list of all tracked (for the specified service) object names
#    channels_list: list of the channel names for the tracked_obj_list objects (not all objects are tracked on all channels)
#    all_match_evts: dictionary of the latest matching service events for each object (keyed by object ID)
#    object_found: boolean indicating if there was a match for the object_name and service (but no events)
def scan_obj_info(obj_info, object_name, service):
    tracked_obj_list = set()
    channels_list = set()
    all_match_evts = {}
    object_found = False
    for pn, obj in obj_info.items():
        try:
            obj_id = obj[EVT_obj_id_key]
            obj_names = obj[EVT_obj_names_key]
            obj_names = [ x.lower() for x in obj_names ]
            obj_def_name = obj_names[0]
            chan_name = obj[EVT_obj_cname_key].lower()
        except:
            print(f"{sys._getframe().f_code.co_name}: invalid event object JSON in {pn}")
            continue
        obj_services = obj.get(EVT_osvc_list_key, [])
        if service is not None and not service in obj_services:
            continue
        tracked_obj_list.add(obj_def_name)
        channels_list.add(chan_name)
        if object_name is None:
            continue
        if not object_name in ANYOBJECT and object_name not in obj_names:
            continue
        object_found = True
        if service is None:
            continue
        evt_file_name = f"{pn}/{service}.json"
        try:
            with open(evt_file_name, "r") as file:
                evt_data = json.load(file)
            new_event_time = evt_data[EVT_in_time_key]
        except json.JSONDecodeError as e:
            print(f"{sys._getframe().f_code.co_name}: file {evt_file_name}, JSON error on line {e.lineno}: {e.msg}")
            continue
        except Exception as e:
            continue
        best_match_evt = all_match_evts.get(obj_id, None)
        if best_match_evt is None or best_match_evt[EVT_in_time_key] < new_event_time:
            all_match_evts[obj_id] = evt_data

    # construct response basing on what we've found
    tracked_obj_list = list(tracked_obj_list)
    channels_list = list(channels_list)
    return tracked_obj_list, channels_list, all_match_evts, object_found

# Respond to the the object location request
def where_is_it(object_name):
    obj_info = collect_evt_obj_info()
    tracked_obj_list, _, all_match_evts, object_found = scan_obj_info(obj_info, object_name, CFG_loc_svc_name)
    msg = None
    for evt in all_match_evts.values():
        if msg is None:
            msg = construct_evt_msg(evt, object_name, CFG_loc_svc_name)
        else:
            msg += ". " + construct_evt_msg(evt, object_name, CFG_loc_svc_name)
    if len(tracked_obj_list) == 0:
        msg = "Watchman is not tracking anything, please check the system configuration."
        rsp = build_response(msg)
    if not object_found:
        msg = "Watchman is tracking " + nice_string_enum(tracked_obj_list) + f". Watchman is not trackiong {object_name}. Please repeat your question."
        rsp = build_response(msg, obj_info=obj_info)
    elif msg is None:
        msg = f"Watchman did not see {object_name} recently."
        rsp = build_response(msg, obj_info=obj_info)
    else:
        rsp = build_response(msg, obj_info=obj_info)
    # Add to the response the updated list of teacked object names
    return rsp

def list_services(obj_info):
    svcs_info = {}
    for pn, obj in obj_info.items():
        try:
            obj_id = obj[EVT_obj_id_key]
            obj_names = obj[EVT_obj_names_key]
            obj_names = [ x.lower() for x in obj_names ]
            obj_def_name = obj_names[0]
            chan_id = obj[EVT_obj_cid_key].lower()
            chan_name = obj[EVT_obj_cname_key].lower()
        except:
            print(f"{sys._getframe().f_code.co_name}: invalid event object JSON in {pn}")
            continue
        obj_services = obj.get(EVT_osvc_list_key, [])
        for svc in obj_services:
            if svc == CFG_dset_svc_name: # filter out dataset service (it's for collecting images for fine tuning)
                continue
            svc_channels = svcs_info.get(svc, {})
            svc_chan_objs = svc_channels.get(chan_name, [])
            svc_off_file_name = f"{pn}/{svc}.off"
            if os.path.exists(svc_off_file_name):
                continue
            svc_chan_objs_set = set(svc_chan_objs)
            svc_chan_objs_set.add(obj_def_name)
            svc_chan_objs = list(svc_chan_objs_set)
            svc_channels[chan_name] = svc_chan_objs
            svcs_info[svc] = svc_channels
    # generate response text summarizing the info over channels (if possible)
    msg = ""
    for svc, svc_channels in svcs_info.items():
        count = 0
        chan_to_report = list(svc_channels.keys())
        for chan_name, svc_chan_objs in svc_channels.items():
            if not chan_name in chan_to_report:
                continue
            chan_to_report.remove(chan_name)
            chan_list = [chan_name]
            for chan_name2 in chan_to_report:
                svc_chan_objs2 = svc_channels.get(chan_name2, [])
                if set(svc_chan_objs2) == set(svc_chan_objs): # can combine channels
                    chan_to_report.remove(chan_name2)
                    chan_list.append(chan_name2)
            if len(chan_list) > 0 and len(svc_chan_objs) > 0:
                msg += ", " if count > 0 else ""
                msg += f"{svc} services on " + nice_string_enum(chan_list) + " are active for " + nice_string_enum(svc_chan_objs)
                count += 1
        if count > 0:
            msg += ". "
    if msg == "":
        msg = "No active services to report."
    return msg

def list_items(component_id):
    obj_info = collect_evt_obj_info()
    obj_names_list, channels_list, _, _ = scan_obj_info(obj_info, None, None)
    msg = None
    if component_id == "objects":
        if len(obj_names_list) > 0:
            msg = "I can watch for " + nice_string_enum(obj_names_list) + "."
        else:
            msg = "There are no objects configured for me to watch for."
    elif component_id == "channels":
        if len(channels_list) > 0:
            msg = "I can monitor " + nice_string_enum(channels_list) + "."
        else:
            msg = "There is nothing configured for me to monitor."
    elif component_id == "services":
        msg = list_services(obj_info)
    else:
        msg = "I can list objects, channels or services, what would you like me to list?"
    rsp = build_response(msg, obj_info=obj_info)
    # Add to the response the updated list of teacked object names
    return rsp

# Run a check on any imager channels needing to (de)actiivated due to no
# configured and active objects or service on them.
# obj_info - list of objects from collect_evt_obj_info()
def handle_de_activating_channels(obj_info):
    active_per_chan = {}
    for pn, obj in obj_info.items():
        try:
            chan_id = obj[EVT_obj_cid_key]
            obj_services = obj[EVT_osvc_list_key]
        except:
            continue
        for s in obj_services:
            svc_off_pname = f"{pn}/{s}.off"
            if os.path.exists(svc_off_pname):
                continue
            active_per_chan[chan_id] = active_per_chan.get(chan_id, 0) + 1
    img_chans = list(filter(lambda x : not x.startswith('.'), os.listdir(IMGDIR)))
    for chan_id in img_chans:
        off_file_pathname = f"{IMGDIR}/{chan_id}/{IMG_off_file_name}"
        try:
            if active_per_chan.get(chan_id, 0) > 0:
                os.unlink(off_file_pathname)
            else:
                open(off_file_pathname, 'w').close()
        except:
            pass
    return

# perform the requested service control actions
def service_control(obj_info, operation, service, object_id, channel_id):
    count = 0
    match_obj_name = object_id
    match_chan_name = channel_id
    for pn, obj in obj_info.items():
        try:
            obj_id = obj[EVT_obj_id_key]
            obj_names = obj[EVT_obj_names_key]
            obj_names = [ x.lower() for x in obj_names ]
            chan_name = obj[EVT_obj_cname_key].lower()
            chan_id = obj[EVT_obj_cid_key]
        except:
            print(f"{sys._getframe().f_code.co_name}: invalid event object JSON in {pn}")
            continue
        obj_services = obj.get(EVT_osvc_list_key, [])
        if service is not None and service not in obj_services:
            continue
        if object_id is not None and object_id not in [ANYOBJECT[0], obj_id]:
            continue
        match_obj_name = ANYOBJECT[0] if object_id == ANYOBJECT[0] else obj_names[0]
        if channel_id is not None and channel_id not in [ANYCHANNEL[0], chan_id]:
            continue
        match_chan_name = ANYCHANNEL[0] if channel_id == ANYCHANNEL[0] else chan_name
        svc_off_pname = f"{pn}/{service}.off"
        try:
            if operation == "enable":
                os.unlink(svc_off_pname)
                count += 1
            elif operation == "disable" and not os.path.exists(svc_off_pname):
                open(svc_off_pname, 'w').close()
                count += 1
        except:
            continue
    # If changes were made, check for imager channels that need to be (de)activated
    if count > 0:
        handle_de_activating_channels(obj_info)
    # Generate the response message to return to the user
    msg = f"Done with {operation[:-1]}ing {service} for {match_obj_name} on {match_chan_name} channel"
    msg += ", " if channel_id != ANYCHANNEL[0] else "s, "
    if count > 0:
        msg += f"{operation[:-1]}ed {count} instance" + ("s" if count > 1 else "")
    else:
        msg += f"no changes were necessary"
    return msg

# ====================================================
# =                Flask handlers                    =
# ====================================================
app = Flask(__name__)

@app.before_request
def check_skill_id():
    alexa_request = request.get_json()
    try:
        skill_id = alexa_request["session"]["application"]["applicationId"]
    except KeyError:
        skill_id = alexa_request["context"]["System"]["application"]["applicationId"]
    if skill_id != ALEXA_SKILL_ID:
        abort(403, description="Unauthorized request")

@app.route("/watchman", methods=["POST"])
def handle_alexa_request():
    global IN_LONG_SESSION
    global IN_DIALOG_SESSION
    data = request.json
    request_type = data.get("request", {}).get("type")
    print(f"Got request: {request_type}")

    if request_type == "LaunchRequest":
        msg = "Welcome to Watchman. You can ask me where specific objects are."
        obj_info = collect_evt_obj_info()
        obj_names_list, _, _, _ = scan_obj_info(obj_info, None, None)
        if len(obj_names_list) > 0:
            msg += " I can watch for " + nice_string_enum(obj_names_list) + "."
        IN_LONG_SESSION = True
        return build_response(msg, obj_info=obj_info)

    elif request_type == "IntentRequest":
        intent_name = data["request"]["intent"]["name"]

        if intent_name == "WhereIsItIntent" or intent_name == "WhereIsItNamedIntent":
            object_name, _ = get_slot_val(data["request"]["intent"]["slots"].get("objectname", {}))
            print(f"Found objectname {object_name}")
            if object_name == "":
                object_name = data["request"]["intent"]["slots"].get("object", {}).get("value", "")
                print(f"Found object {object_name}")
            return where_is_it(object_name)

        if intent_name == "ListIntent":
            _, component_id = get_slot_val(data["request"]["intent"]["slots"].get("component", {}))
            return list_items(component_id)

        if intent_name in ["ServiceObjectChannelControlIntent"]:
            #print(json.dumps(data, indent=2))
            _, operation = get_slot_val(data["request"]["intent"]["slots"].get("operation", {}))
            _, service = get_slot_val(data["request"]["intent"]["slots"].get("service", {}))
            object_name, object_id = get_slot_val(data["request"]["intent"]["slots"].get("objectname", {}))
            channel_name, channel_id = get_slot_val(data["request"]["intent"]["slots"].get("channelname", {}))
            dialog_state = data["request"].get("dialogState", "")
            obj_info = collect_evt_obj_info()
            obj_names_list, channels_list, _, _ = scan_obj_info(obj_info, None, None)
            dialog_delegate = False
            elicit_slot = None
            if dialog_state == "STARTED":
                IN_DIALOG_SESSION = True
            if dialog_state != "COMPLETED":
                if len(obj_names_list) <= 0:
                    msg = "Sorry, I'm not in a good mood now, please check my configuration. I'm not configured to track anything."
                elif len(channels_list) <= 0:
                    msg = "Sorry, I'm not in a good mood now, please check my configuration. I'm not configured to monitor any channels."
                elif time.time() - DYN_VAL_UPDATE > 300: # need to send a simple response to update dynamic entries (it doesn't work w/ delegate or elicit)
                    msg = "Sorry, I was distracted, what did you say to watchman?"
                elif operation == "" or service == "": # These are to be handled by Alexa (fingers crossed, Alexa is nuts)
                    dialog_delegate = True
                    msg = None
                elif object_name == "" or object_id == "":
                    elicit_slot = "objectname"
                    msg = f"What should I {operation} {service} for, " + ", ".join(obj_names_list) + f" or {ANYOBJECT[0]}"
                elif not object_id in ANYOBJECT and not object_name in obj_names_list:
                    elicit_slot = "objectname"
                    msg = f"I can't handle {object_name}, please select from " + ", ".join(obj_names_list) + f" or {ANYOBJECT[0]}"
                elif channel_name == "" or channel_id == "":
                    elicit_slot = "channelname"
                    msg = f"Which channel should I {operation} {service} on, " + ", ".join(channels_list) + f" or {ANYCHANNEL[0]}"
                elif not channel_id in ANYCHANNEL and not channel_name in channels_list:
                    elicit_slot = "channelname"
                    msg = f"I can't {operation} {service} on channel {channel_name}, please select from " + ", ".join(channels_list) + f" or {ANYCHANNEL[0]}"
                else: # We've got all we needed 
                    IN_DIALOG_SESSION = False
            else:
                IN_DIALOG_SESSION = False
            if not IN_DIALOG_SESSION:
                msg = service_control(obj_info, operation, service, object_id, channel_id)
            rsp = build_response(msg, obj_info=obj_info, dialog_delegate=dialog_delegate, elicit_slot=elicit_slot)
            return rsp

        elif intent_name == "AMAZON.HelpIntent":
            msg = "You can ask watchman where specific objects are, for example, if looking for people ask 'did you see people?'. "
            msg += "For a single question, prefix it with 'Alexa, ask my watchman'. For multiple, say 'Alexa, open my watchman' to start "
            msg += "the conversation, then ask all your questions directly without any prefix. "
            msg += "To control the system you can ask watchman to enable or disable the alerts or the location services. "
            msg += "You can also ask watchman to list the objects or channels it can monitor."
            return build_response(msg)

        elif intent_name in ["AMAZON.CancelIntent", "AMAZON.StopIntent", "WeAreDoneIntent"]:
            IN_LONG_SESSION = False
            return build_response("Watchman says bye!", clear=True, is_end=True)

    elif request_type == "SessionEndedRequest":
        return jsonify({})  # Respond with an empty JSON body for session end

    return build_response("Watchman not sure how to handle that. Please try again.", is_end=False)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
