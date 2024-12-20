Ollama can be used locally or in docker
Under Linux it's esier to install locally: 
  curl -fsSL https://ollama.com/install.sh | sh
then use the below command to load and manually try the model
  ollama run llama3.2-vision:11b-instruct-fp16
(can try "llama3.2-vision:latest" for 4-bit quantized version)

For docker the compose will use the stock OLLAMA container.
You'd need to specify 
OLLAMA_MODELS_DIR=<path/where/to/store/model/files>
in .env file (in the project root).
