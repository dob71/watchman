The Voice Control Service (vcs) has two major parts, responder (for voice control)
and announcer (for voice alerts).

The responder requires setting up a custom Alexa "skill". The "skill" controls some basic
aspects of the coverstion and sends REST API requests to the responder service running
locally to access the system information and generate dialog responses.
You'll need to expose your local service endpoint (running on port 8080) to the Internet
(HTTPs with a trusted server certificate is required). Unless you already have the means
to achieve that "ngrok" service would be the easiest approach. Note the ngrok URL to use
for accessing your responder service, and make sure to change the certificate type to
"wildcard" in the Watchman skill configuration.


Follow the instructions linked below to set up Alexa dev account and install ASK CLI:
https://developer.amazon.com/en-US/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html
With the ASK CLI installed and Alexa dev account created, you should be able to deply the
"My Watchman" skill. See ./vcs/alexa/readme.txt for some extra help on that.
When the skill is deployed note the skill's ID (it looks like this: "amzn1.ask.skill.123...").

The announcer service runs separately from the responder and can be used with or without Alexa.
The announcer instructions below focus on helping to set it up to work through Alexa, but it
can call a custom script that can do anything user wants.

The announcer supports 2 ways of alerting the user:

1. Alexa notifications.
The https://www.thomptronics.com/about/notify-me service for the alerts to be sent as
notifications to your Alexa. During the setup you should get an e-mail w/ the auth token, 
looking like this: "nmac.XYZ...". Add it to your .env file as NOTIFY_ME_ID.
Alexa makes sound and changes color when it receives notifications. It requires user to
say "Alexa, what are my notifications" to read them out loud.

2. A custom script to process alerts.
For the Watchman alerts it makes more sense to just announce the alerts right away.
This can be achived with the help of https://github.com/thorsten-gehrig/alexa-remote-control script.
You migh have some other means (like Google Home device) to make such announcements. In order to
support various customizations, announcer.py can call a generic script. The script is passed just
1 parameter - the message to announce. Set the ALERT_SCRIPT variable in your .env file to point to
the script path (for running in docker keep in mind that it'll have to be accessible and able to
run from the inside of the container).

You can set up both NOTIFY_ME_ID and ALERT_SCRIPT, or just one of them.

Add the skill ID, the Notify Me auth token, and the ALERT_SCRIPT variables to your .env file:
DATA_DIR=./.data
OLLAMA_MODELS_DIR=/work/models/ollama
ALEXA_SKILL_ID=amzn1.ask.skill.123...
NOTIFY_ME_ID=nmac.XYZ...
ALERT_SCRIPT=/path/to/your/announce.sh

Commands for installing ASK under Ubuntu 22.04 (requires installing nodejs)
---------------------------------------------------------------------------
# you might want to purge the old nodejs version first
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
NODE_MAJOR=22
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
sudo apt-get update
sudo apt-get install nodejs -y
sudo npm install -g ask-cli
ask configure # AWS credentials won't be necessary as we serve locally

# after editing the URI in the vcs/alexa/skill.json
cd vcs/alexa
ask deploy

# If editing in dev console, go to ./vcs/alexa folder and download your own "skill-pkg" with:
#   ask smapi export-package --stage development --skill-id <skill_ID>
# after that you can still edit manually and deploy with "ask deploy".
