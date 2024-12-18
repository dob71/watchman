The images folder ${DATA_DIR}/images
The images are stored in subfolders by channel.
Example:
./
├── 1/
│   └── image.json
├── 2/
│   └── image.json
...
The exact content of the folders and files is TBD.
The 0,1,... are input channels (i.e. image sources: webcams, surveilance cameras, ...)
The supplier of the information should write image data (base64) along w/ metadata to
the .tmp first, then use rename to replace. The reader should rename to image.rd.tmp,
then read and delete. The channel name should be a part of the image metadata. Dropping
a raw .jpg alongside the image.json could be useful for debugging.
