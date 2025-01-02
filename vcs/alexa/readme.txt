Before deploying...
Create ".ask" folder here and write .ask/ask-states.json file w/ the following content:
-------------- cut ----------------
{
  "askcliStatesVersion": "2020-03-31",
  "profiles": {
    "default": {
      "skillId": ""
    }
  }
}
------------- end cut -------------

If it's the first time you are deploying the skill and have no "skillId", then leave it empty.
Don't forget to change the "uri": "https://your.url.com/path" (./skill-package/skill.json)
to point to your responder.

Deploy using "ask deploy" command, or install Alexa ASK extension for VS code, set it up,
load the local skill from this folder and deploy using the extension interface.
Before deploying, make sure to change uri": "https://..." in the skill.json
to the URL serving where the watchman's responder is serving the requests. Note that
it has to be HTTPS w/ a trusted certificate (use ngrok for that).

After a successful deplyment ask will generate a new "skillId" and update the ask-states.json.
Don't forget to add that skill ID to your project .env file (it is used by the responder to
verify the requests are coming from your Alexa skill).

The ask tool can be used to test the conversation w/ the skill without using any voice input
devices by running: "ask dialog --locale en-US --skill-id <skillid> --stage development"

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

Example dialog ("ask dialog" session):
--------------------------------------
============================================================================= Welcome to ASK Dialog ============================================================================
================================================= In interactive mode, type your utterance text onto the console and hit enter =================================================
=========================================================== Alexa will then evaluate your input and give a response! ===========================================================
===================================== Use ".record <fileName>" or ".record <fileName> --append-quit" to save list of utterances to a file. =====================================
===================================================== You can exit the interactive mode by entering ".quit" or "ctrl + c". =====================================================

User  > Alexa, open my watchman
Alexa > Welcome to Watchman. You can ask me where specific objects are. I can watch for people, a cat and a deer.
User  > help
Alexa > You can ask watchman where specific objects are, for example, if looking for people ask 'did you see people?'. For a single question, prefix it with 'Alexa, ask my watchman'. For multiple, say 'Alexa, open my watchman' to start the conversation, then ask all your questions directly without any prefix. To control the system you can ask watchman to enable or disable the alerts or the location services. You can also ask watchman to list the objects or channels it can monitor.
User  > list
Alexa > I can list channels or objects. What should I list?
User  > objects
Alexa > I can watch for people, a cat and a deer.
User  > did you see people
Alexa > Watchman did not see people recently.
User  > list channels
Alexa > I can monitor backyard, porch, driveway and frontyard.
User  > enable
Alexa >  I can enable alerts or location services, which one would you like me to enable?
User  > location
Alexa > What should I enable location for, people, a cat, a deer or everything
User  > people
Alexa > Which channel should I enable location on, backyard, porch, driveway, frontyard or all
User  > porch
Alexa > Done with enabling location for people on porch channel, no changes were necessary
User  > bye
Session ended
Alexa > Watchman says bye!
