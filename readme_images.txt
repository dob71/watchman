The images folder ${DATA_DIR}/images
The images are stored in subfolders by channel.
Example:
./
├── porch/
│   └── image.json
├── driveway/
│   └── image.json
...
The exact content of the folders and files is TBD.
The porch, driveway, ... are the video input channels (i.e. image sources: webcams, 
surveilance cameras, ...). The channel ids have to be strings compliant to the file/directory
naming conventions (i.e. porch, driveway, 1, 2, 3, ...).
The supplier of the information (imager service) should write image data (base64) along 
w/ metadata to the image.json.tmp first, then use rename to replace. The reader should
rename to image.json.rd.tmp first, then read and delete (or use alternative methods to
identify when the data is updated to avoid repeatedly running inference on the same image). 
The channel name should be a part of the image metadata. Dropping a raw .jpg alongside 
the image.json could be useful for debugging.
