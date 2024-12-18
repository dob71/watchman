The events folder ${DATA_DIR}/events
The events are stored in subfolders by channel/object/event
Example:
./.data/events
├── 1/
│   ├── cat/
│   │    ├── last_seen.json
│   │    └── alert.json
│   └── person/
├── 2/
│   ├── cat/
│   │    └── last_seen.json
│   └── person/
│        └── alert.json
...
The exact content of the folders and files is TBD.
The 0,1,... are input channels (i.e. image sources: webcams, surveilance cameras, ...)
The supplier of the information should write image data (base64) along w/ metadata to
the .tmp first, then use rename to replace. The reader should open and read at once
(no re-opening). For the alert the reader reanmes to .reader.tmp first, then reads
and deletes. The object names should (normally) be identifiers, but it's ok for the start.
