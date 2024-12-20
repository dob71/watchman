import os
import requests
import json
from dotenv import load_dotenv

# Figure the path to the data folders depending on where we run
DATA_DIR = '/'
if not os.path.exists('/.dockerenv'):
    load_dotenv('../.env')
    DATA_DIR = os.getenv('DATA_DIR')
    IMGDIR='/images'
    CFGDIR='/sysconfig'

# We'll need the images and config folders.
IMGDIR=f"{DATA_DIR}/images"
CFGDIR=f"{DATA_DIR}/sysconfig"

# Config dictionary
CFG={}
def read_config():
    # just fake it for now
    CFG['1'] = f""
    CFG['2'] = f""
    CFG['3'] = f""
    CFG['4'] = f""
    CFG[''] = f""
    CFG[''] = f""
    CFG[''] = f""
    CFG[''] = f""
    CFG[''] = f""
    CFG[''] = f""


# Replace with your NVR details
NVR_IP = "192.168.0.10"
NVR_USERNAME = "guest"
NVR_PASSWORD = "guest_passwd"
CHANNEL_NUMBER = 0  # Camera channel you want to capture from

def capture_jpeg(nvr_ip, username, password, channel):
    # Note: https not working w/ Reolink NVR
    url = f"http://{nvr_ip}/cgi-bin/api.cgi?cmd=Snap&width=2560&height=1920&channel={channel}&rs=9999&user={username}&password={password}"
    response = requests.get(url, verify=False, stream=True)

    if response.status_code == 200:
        with open(f"images/captured_image{channel}.jpg", "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print("JPEG image captured successfully!")
    else:
        print("Error fetching image:", response.status_code)

for channel in range(4):
    capture_jpeg(NVR_IP, NVR_USERNAME, NVR_PASSWORD, channel)
