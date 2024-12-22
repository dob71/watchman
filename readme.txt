Design doc:
https://docs.google.com/document/d/1FqfiEmbQ6IQClg8hCWp0W1PeTREskdzSkgSx6LMQHN4

You'd need to specify 
DATA_DIR=<path/where/to/store/data/files/for/services/communication>
in .env file (here, in the project root).
For example:
DATA_DIR=.data
will result in the "events", "images" and "sysconfig" folders to be
under ./.data.
Start scripts from the root folder of the project (i.e."python3 ./imager/imager.py")
