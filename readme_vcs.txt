The Voice Control Service (vcs) is implemented w/ Amazon Alexa.
For the responder it creates a custom skill that is serving the requests locally.
You'll need to expose yout local service running on port 8080 to the world over
HTTPs with a trusted server certificate. Unless you already have the means to
achieve that "ngrok" service would be the easiest approach. Note the URL to use
for accessing your responder service.

Folow the instructions on the page below to set up Alexa dev account and install ASK CLI:
https://developer.amazon.com/en-US/docs/alexa/smapi/quick-start-alexa-skills-kit-command-line-interface.html

With the ASK CLI installed and Alexa dev account created, you should be able to deply the
"My Watchman" skill. See ./vcs/alexa/readme.txt for some extra help on that.
When the skill is deployed note the skill's ID (it looks like this: "amzn1.ask.skill.123...").

The https://www.thomptronics.com/about/notify-me service has to be set up for the alerts to work.
During the setup you should get an e-mail w/ the auth token, looking like this: "nmac.XYZ...".

Add the skill ID and the Notify Me auth token to your .env file:
DATA_DIR=./.data
OLLAMA_MODELS_DIR=/work/models/ollama
ALEXA_SKILL_ID=amzn1.ask.skill.123...
NOTIFY_ME_ID=nmac.XYZ...

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
# then edit and deploy.
