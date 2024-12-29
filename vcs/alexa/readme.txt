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

After a successful deplyment ask will generate a new "skillId" and update the ask-states.json.
Don't forget to add that skill ID to your project .env file (it is used by the responder to
verify the requests are coming from your Alexa skill).

Example dialog:

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
