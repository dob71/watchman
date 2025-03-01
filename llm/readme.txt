This folder contains information on how to run and fine-tune multi-modal LLM 
(LLAMA3.2 Vision Instuct for now) for use w/ the Watchman service.

Here are the main topics:
1. Serving with OLLAMA
2. Serving with vLLM
3. Fine-tuning

1. Serving with OLLAMA

OLLAMA can be used locally or in docker.
Under Linux it's esier to install locally: 
  curl -fsSL https://ollama.com/install.sh | sh
then use the below command to load and manually try the model
  ollama run llama3.2-vision:11b-instruct-fp16
(can try "llama3.2-vision:latest" for 4-bit quantized version)

For docker the compose will use the stock OLLAMA container.
You'd need to specify 
OLLAMA_MODELS_DIR=<path/where/to/store/model/files>
in .env file (in the project root).

When the LLAMA3.2 Vision Instuct modeal is served by OLLAMA, Watchman
has to be configured to use "ollama-simple" or "ollama-complex" model
interfaces (see model_interfaces.py for details). The only diffrence
between the interfaces is that the latter also ask the model to give
th elocation of the object on the image.

2. Serving with vLLM

vLLM version 0.7.0 has been used in the project so far.
It was set up under venv using Python 3.10.12.
CUDA environment: Driver Version: 545.29.06 CUDA Version: 12.3

Instructions: https://docs.vllm.ai/en/v0.7.0/getting_started/installation/gpu/index.html
Set up method: "Set up using Python-only build (without compilation)"

vLLM exposes the open AI APIs. The APIs make it difficult to query
LLAMA 3.2 Vision Instruct using custom prompt utilized by Watchman.
In order to work around that a custom role was added to the
chat template of the model. vLLM has to be run with that modified
template. Here's the example of the start command:

vllm serve /path/to/repo/llm/trained/watchman_sft_16bit \
     --chat-template /path/to/repo/llm/watchman_sft_16bit_chat_tpl.jinja \
     --tensor-parallel-size 2 --enforce-eager --gpu-memory-utilization 0.9 \
     --max_model_len 2048 --max-num-seqs 16 --port 5050

vLLM support was introduced to simplify deploying after fine-tuning using
Unsloth (Unsloth's exporting to GGUF is not supported for the vision models
at the moment). See the fine-tuning notebook for the details.
It also should be able to supports batching (not supported for mllama in OLLAMA).

3. Fine-tuning

The generic model should not be expected to have a very good accuracy.
Fine-tuning is almost guaranteed to be necessary for the reasonable performance.
In order to support fine tuning, the system allows to utilize the hidden "dataset"
service. That servce helps to create a manageable dataset of images where
model makes mistakes and then use them to fine-tune. The service can be enabled
in the config or by manually deleting "dataset.off" file under the folder
<events_path>/<channel>/<object>/ for the desired channel object combination.
The fine_tune.ipynb notebook in this folder shows an example of fine-tuning the
LLAMA 3.2 Vision Instruct with Unsloth and the Watchman "dataset" data, and then
deploying the updated model to be served by vLLM.

The dataset images are stored in subfoders under the "dataset" path.
The subfoder structure is:
  <dataset_path>/<channel>/<object>/<1-...>/
The service captures (under the numbered subfolders) all the images where model
detects the object, as well as each image preceeding any sequence of such detection(s).
This increases the chances of capturing both, false positive and false negatives
while still keeping the dataset size relatively small.

After capturing, all the dataset images have to be classified manually (or with
the help of a better model). The images are assumed to be true positives unless
identified otherwise. This identification of negatives is done by placing the
file "no" in the image folder. The folders can be also tagged w/ the file "skip"
to be ignored. Again, all folders having no tag file are assumed to be true positives.

The UI will be eventually extended to help with the work of tagging the "dataset"
service images.

All the notebooks in this folder are for experimenting w/ infernce and fine tuning.
Examine and/or experiment with them in the following oredr:
- llm/ollama-complex-iterface.ipynb - (test inference with OLLAMA)
- llm/hf-llama-vision-inference-4bit-vs-16.ipynb - (inference with HF in Python, 4-bit vs 16-bit)
- llm/dataset-to-pickle.ipynb - (prepare data for making fine-tuning dataset)
- llm/fine_tune.ipynb - (fine tune using Unsloth and serve in vLLM)
- llm/vllm-fine_tune-test.ipynb - (test fine-tuned model in vLLM)
The output for some of the notebook cells is preserved to demonstrate the results,
but the dataset collected and used here is not shared publically.
The fine-tuning has to be done for the specific use cases. The expectation
is that the iterested parties would enable the dataset service in Watchan and
collect their own data for the fine-tuning. 
