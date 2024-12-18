The config folder ${DATA_DIR}/sysconfig
This folder contains:
1. sources.json - describes image sources, their names, URls, image preprocessing requirements, e.t.c.
2. objecs.json - describes objects of interest, their alexa names, description for identification, e.t.c.
3. version.txt
Both files are provided by the UI.
The consumers are the imager for 1 and orchestrator for 2.
The version.txt (created by the UI) contains a number the UI should bump up when config is updated.
The consumers of the files should read and record the version, then re-load the config if bumped up.
The UI should do all its writes by writing to .tmp then renaming.
