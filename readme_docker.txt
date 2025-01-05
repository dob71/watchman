This application has been containerized and can be launched using docker-compose.
To do this, the following steps need to be performed:
- Install docker and docker-compose
- Setup Alexa (refer to readme_vcs.txt)
- Setup and run ngrok to to expose your local responder service endpoint if necessary, as per readme_vcs.txt
- Create .env with DATA_DIR, ALEXA_SKILL_ID, NOTIFY_ME_ID and OLLAMA_MODELS_DIR. Here is an example:
    DATA_DIR=./.data
    ALEXA_SKILL_ID=amzn1.ask.skill.<your skill id>
    NOTIFY_ME_ID=nmac.<your nmac id>
    OLLAMA_MODELS_DIR=/llm
- Run 'docker-compose up --build' from the top-level directory of the repository.
- To stop the app, hit ctrl-c

