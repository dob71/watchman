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

When the LLAMA3.2 Vision Instuct model is served by OLLAMA, Watchman
has to be configured to use "ollama-simple" or "ollama-complex" model
interfaces (see model_interfaces.py for details). The only diffrence
between the interfaces is that the latter also asks the model to give
the location of the object on the image.

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
It also should be able to support batching (not supported for mllama in OLLAMA
and not yet levraged in Watchnam).

3. Fine-tuning

The generic model should not be expected to have a very good accuracy.
Fine-tuning is pretty much guaranteed to be necessary for any reasonable accuracy.
In order to support the fine tuning, Watchman system provides the hidden "dataset"
service. That servce helps to create a dataset of images where the model is likely
to make mistakes. Then corrct them manualy (using Watchman UI) or using a larger
model (still TBD), and fine-tune the local model. The service can be enabled
in the config, on the "System Status" UI page or by manually by deleting the
"<events_path>/<channel>/<object>/dataset.off" file for the desired channel object
combination.

When the dataset service is enable the images and the inference info are collected
under the "<data_path>/dataset/<channel>/<object>/" folder (the colection stops
when the hard limit of 1000 images is reached). The Watchman UI can be used to move
the working copy of the dataset folder to the queue for labeling (correcting the
inference errors), and from there to the training data archive (a pickle file
"<data_path>/dataset/train_data.pkl").

The fine_tune.ipynb notebook in this folder shows an example how to use that file
for fine-tuning the LLAMA 3.2 Vision Instruct with Unsloth, and then deploy the
updated model to be served by vLLM.

The process of collecting and labeling the data can also be performed manually,
using the notebooks. Below, there are some details on how the dataset service
works and how to use the notebooks provided here, in this folder.

The dataset images are stored in subfoders under the "dataset" path. The subfoder
structure is:
  <dataset_path>/<channel>/<object>/<1-...>/
The service captures (under the numbered subfolders) all the images where model
detects the object, as well as each image preceeding any sequence of such detection(s).
This increases the chances of capturing both, false positive and false negatives
while still keeping the dataset size relatively small.

After capturing, all the dataset images have to be classified manually (or with
the help of a better model). The images are assumed to be true positives unless
identified otherwise. This identification of negatives is done by placing the
file "no" in the image folder. The folders can also be labeled w/ the file "skip"
to be ignored. Again, all folders containing no such files are assumed to be true
positives.

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
