Design doc:
https://docs.google.com/document/d/1FqfiEmbQ6IQClg8hCWp0W1PeTREskdzSkgSx6LMQHN4
System Demo Video:
https://youtu.be/TY_8oiRfh9s

Follow the following steps to set the system up to run locally.
1. Pull in the code from the https://github.com/dob71/watchman repository.
2. Go through all the readme files.
3. Set up the required external services (OLLAMA w/ LLAMA 3.2 Vision model, Amazon Alexa’s “My Watchman” skill, 
   Notify Me service (optional), Alexa control script setup (optional)).
4. Set up python virtual environment (use requirements.txt in the root of the project).
5. Create a .env file w/ the system specific settings, for example:
     DATA_DIR=./.data
     OLLAMA_MODELS_DIR=/home/user/models/ollama
     ALEXA_SKILL_ID=amzn1.ask.skill.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
     NOTIFY_ME_ID=nmac.XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
     ALERT_SCRIPT=/work/alexa_announce.sh
6. Launch the services (using start_local.sh script from the project root folder),
   examine the logs under DATA_DIR/logs folder to confirm all services are running happily.
7. Open the UI and configure the system for the video feeds to monitor and objects to track.
8. Confirm the system is operational (explore the folders under the DATA_DIR to confirm
   that the images are downloaded from the soures, event files are generated, announcements
   are working and "My Watchman" Alexa skill can answer questions).
