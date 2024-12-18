from flask import Flask, request, jsonify, abort

# Define the list of objects that the Watchman can recognize
WATCHMAN_OBJECTS = ["cat", "car"]

# Secret token for simple authentication
SECRET_TOKEN = "your_secret_token_here"

app = Flask(__name__)

#@app.before_request
#def authenticate():
#    # Check for the secret token in the request headers
#    token = request.headers.get("Authorization")
#    if token != f"Bearer {SECRET_TOKEN}":
#        abort(403, description="Unauthorized request")

@app.route("/watchman", methods=["POST"])
def handle_alexa_request():
    data = request.json
    request_type = data.get("request", {}).get("type")

    if request_type == "LaunchRequest":
        return build_response("Welcome to Watchman. You can ask me where specific objects are.", is_end=False)

    elif request_type == "IntentRequest":
        intent_name = data["request"]["intent"]["name"]

        if intent_name == "WhereIsObjectIntent":
            object_name = data["request"]["intent"]["slots"].get("object", {}).get("value", "")

            if object_name in WATCHMAN_OBJECTS:
                speech_text = f"I did not see the {object_name}, ask anthony."
            else:
                speech_text = f"I'm not sure about {object_name}. Please ask about something I recognize."
            return build_response(speech_text)

        elif intent_name == "AMAZON.HelpIntent":
            return build_response("You can ask me where specific objects are by saying, 'ask Watchman where is my cat.'", is_end=False)

        elif intent_name in ["AMAZON.CancelIntent", "AMAZON.StopIntent"]:
            return build_response("Watchman says goodbye!", is_end=True)

    elif request_type == "SessionEndedRequest":
        return jsonify({})  # Respond with an empty JSON body for session end

    return build_response("Watchman not sure how to handle that. Please try again.", is_end=False)

def build_response(speech_text, is_end=True):
    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech_text
            },
            "shouldEndSession": is_end
        }
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
