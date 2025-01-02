The config folder ${DATA_DIR}/sysconfig
This folder contains:
1. sources.json - describes image sources, their names, URls, image preprocessing requirements, e.t.c.
2. objecs.json - describes objects of interest, their alexa names, description for identification, e.t.c.
Both files are provided by the UI.
The consumers are the imager for 1 and orchestrator for 2.
Both configs should have "version" field containing a number the UI should bump up when the data is updated.
The consumers of the files should record the version, then periodically re-read and check the config verson
re-applying when seeing the version change.
The UI should do all its updates by writing to .tmp then atomically renaming.

Example of the sources config:
{
  "version": 1,           <-- config version
  "channels": [
    {
      "channel": "porch", <-- channel id
      "name": "Porch",    <-- channel name
      "url": "http://192.168.0.100/cgi-bin/api.cgi?cmd=Snap&width=2560&height=1440&channel=0&rs=9999",
      "upd_int": 3        <-- image update interval
    },
    {
      "channel": "driveway",
      "name": "Driveway",
      "url": "http://192.168.0.100/cgi-bin/api.cgi?cmd=Snap&width=2560&height=1440&channel=1&rs=9999",
      "upd_int": 3
    }
  ]
}

Example of the objects of interest config:
{
    "version": 5,
    "model": "ollama-simple",
    "objects": [ {
            "obj_id": "cat",
            "names": ["a cat", "panda", "my cat", "cat", "the cat", "that stupid cat"],
            "desc": "a black and white tuxedo cat",
            "obj_svcs": [{
                    "osvc_name": "location",
                    "msgtpl": "I saw [OBJNAME] [TIMEAGO] ago on the [CHANNEL] camera. [LOCATION]",
                    "age_out": 10800,
                    "def_off": true
                }, {
                    "osvc_name": "dataset",
                    "msgtpl": "OBJNAME:[OBJNAME] CHANNEL:[CHANNEL] LOCATION:[LOCATION]",
                    "pname": "./.data/dataset",
                    "age_out": 60,
                    "def_off": true,
                    "skip_ch": []
                }
            ]
        }, {
            "obj_id": "person",
            "names": ["people", "a person", "anybody", "somebody", "human", "meat pupsicle"],
            "desc": "a person",
            "obj_svcs": [{
                    "osvc_name": "location",
                    "msgtpl": "I saw [OBJNAME] [TIMEAGO] ago on the [CHANNEL] camera. [LOCATION]",
                    "age_out": 86400,
                    "def_off": true,
                    "skip_ch": []
                }, {
                    "osvc_name": "alert",
                    "msgtpl": "[OBJNAME] is on the [CHANNEL] camera. [LOCATION]",
                    "age_out": 60,
                    "mute_time": 300,
                    "def_off": true,
                    "skip_ch": ["front", "back"]
                }, {
                    "osvc_name": "dataset",
                    "msgtpl": "OBJNAME:[OBJNAME] CHANNEL:[CHANNEL] LOCATION:[LOCATION]",
                    "pname": "./.data/dataset",
                    "age_out": 60,
                    "def_off": true,
                    "skip_ch": []
                }
            ]
        }, {
            "obj_id": "deer",
            "names": ["a deer", "a voratious pest", "a pest", "deer"],
            "desc": "a deer",
            "obj_svcs": [{
                    "osvc_name": "alert",
                    "msgtpl": "[OBJNAME] is on the [CHANNEL] camera. [LOCATION]",
                    "age_out": 60,
                    "mute_time": 600,
                    "def_off": true,
                    "skip_ch": ["porch", "driveway"]
                }, {
                    "osvc_name": "location",
                    "msgtpl": "I saw [OBJNAME] [TIMEAGO] ago on the [CHANNEL] camera. [LOCATION]",
                    "age_out": 86400,
                    "def_off": true,
                    "skip_ch": ["porch", "driveway"]
                }, {
                    "osvc_name": "dataset",
                    "msgtpl": "OBJNAME:[OBJNAME] CHANNEL:[CHANNEL] LOCATION:[LOCATION]",
                    "pname": "./.data/dataset",
                    "age_out": 60,
                    "def_off": true,
                    "skip_ch": []
                }
            ]
        }
    ]
}
