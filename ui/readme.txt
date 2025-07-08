To run the UI manually:
  streamlit run ui/main.py

The examples of the config files:

sources.json:
-------------------
{
    "version": 13,
    "channels": [
        {
            "channel": "porch",
            "name": "Porch",
            "url": "file://./.data/dataset/porch/00055.jpg",
            "upd_int": 5,
            "width": 1280,
            "height": 720,
            "quality": 50
        },
        {
            "channel": "driveway",
            "name": "Driveway",
            "url": "file://./.data/dataset/driveway/00054.jpg",
            "upd_int": 5,
            "width": 1280,
            "height": 720,
            "quality": 50
        },
        {
            "channel": "front",
            "name": "Frontyard",
            "url": "file://./.data/dataset/front/00058.jpg",
            "upd_int": 5,
            "width": 1280,
            "height": 720,
            "quality": 50
        },
        {
            "channel": "back",
            "name": "Backyard",
            "url": "file://./.data/dataset/back/00057.jpg",
            "upd_int": 5,
            "width": 1280,
            "height": 720,
            "quality": 50
        }
    ]
}
-------------------

objects.json:
-------------------
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
                }
            ]
        }, {
            "obj_id": "person",
            "names": ["someone", "a person", "anybody", "somebody", "human", "meat pupsicle"],
            "desc": "a person",
            "obj_svcs": [{
                    "osvc_name": "location",
                    "msgtpl": "I saw [OBJNAME] [TIMEAGO] ago on the [CHANNEL] camera. [LOCATION]",
                    "age_out": 86400,
                    "def_off": true,
                    "skip_ch": []
                }, {
                    "osvc_name": "alert",
                    "msgtpl": "I see [OBJNAME] on the [CHANNEL] camera. [LOCATION]",
                    "age_out": 60,
                    "mute_time": 300,
                    "def_off": true,
                    "skip_ch": ["front", "back"]
                }
            ]
        }, {
            "obj_id": "deer",
            "names": ["a voratious pest", "a pest", "a deer", "deer"],
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
                }
            ]
        }
    ]
}
-------------------
