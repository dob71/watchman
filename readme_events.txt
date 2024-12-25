The events folder ${DATA_DIR}/events
The events are stored in subfolders, in channel/events.json
Example:
./.data/events
├── porch/
│   ├── cat/
│   │    ├── obj.json
│   │    ├── location.json
│   │    └── alert.json
│   └── person/
├── backyard/
│   ├── cat/
│   │    └── location.json
│   └── person/
│   │    ├── obj.json
│   │    ├── alert.json
│        └── read_alert.json
...
The porch, backyard, ... are the input channels (i.e. image sources).
The supplier of the information should write the event data to the .tmp first, 
then use atomic rename to replace. The reader should open and read at once
(no re-opening). The alert.json file is removed after configured age out time.
If the alert info chnages, the file is updated (i.e. aging out starts when
the alert conditions are no longer detected). In additioon to the alert message,
the alert.json contains the configured mute time. The reader can track it to
avoid repeating alerts unnecessarily often.
Similarly to the alerts, the location.json is removed after its age out time.
The obj.json files are created at the same time as the object folders and stay
unchangesd throughout the orhestrator operation. They contain the object of
interest information like object names and description that might be useful
for the events consumer service even in the bsence of the event files (without
requiring it to read the config).
