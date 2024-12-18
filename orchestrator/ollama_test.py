from ollama import chat, generate
from pathlib import Path
import base64
import time

# Prompt construction for LLAMA 3.2 Vision model
# https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/vision_prompt_format.md

# which model to use
#MODEL='llama3.2-vision:11b-instruct-fp16'
MODEL='llama3.2-vision:latest'
OBJECT='a plant'

# Pass in the path to the image
path = "/work/ik_capstone/images/captured_image.jpg"
img1 = base64.b64encode(Path(path).read_bytes()).decode()
img2 = Path(path).read_bytes()

# Arrays of paths and image data for an experiment
paths = []
images = []
for ii in range(4):
    paths.append(f"/work/ik_capstone/images/captured_image{ii}.jpg")
    images.append(base64.b64encode(Path(paths[ii]).read_bytes()).decode())

print(f"\nLoading the model")
response = chat(
  model=MODEL,
  messages=[],
)
print(f"Model: {response.model}, result:{response.done_reason}")

PROMPT = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful, concise assistant for locating objects in an image<|eot_id|>" + \
         f"<|start_header_id|>user<|end_header_id|><|image|>Is there {OBJECT} on the image? Answer strictly Yes or No<|eot_id|>" + \
         "<|start_header_id|>assistant<|end_header_id|>"

#PROMPT = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful, concise assistant for locating objects in an image<|eot_id|>" + \
#         f"<|start_header_id|>user<|end_header_id|><|image|>Is there {OBJECT} on the image? Answer strictly No if not. Answer Yes and where is it located otherwise. Answer in one sentence.<|eot_id|>" + \
#         "<|start_header_id|>assistant<|end_header_id|>"

#print(f"\nTrying raw prompt")
#response = generate(
#  model=MODEL,
#  prompt=PROMPT,
#  images=[images[1]],
#  options={'temperature': 0.0},
#)
#print(response.response)

start_time_ms = int(time.time() * 1000)

for ii in range(4):
    response = generate(
        model=MODEL,
        prompt=PROMPT,
        images=[images[ii]],
        options={'temperature': 0.0},
    )
    print(f"\nimage {ii}:\n{response.response}")

end_time_ms = int(time.time() * 1000)

print(f"That took {((end_time_ms - start_time_ms) / 1000):.2f}")

"""
# Not supported:
print(f"\nTrying raw prompt for image comparison")
response = generate(
  model=MODEL,
  prompt=
  "<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful, concise assistant for finding changes in images<|eot_id|>" +
  "<|start_header_id|>user<|end_header_id|><|image|><|image|>what are the differences<|eot_id|>" +
  "<|start_header_id|>assistant<|end_header_id|>",
  images=[img1, images[0]],
  options={'temperature': 0.0},
)
print(response.response)
"""

"""
print(f"\nTrying passing image by path: {path}")
response = chat(
  model=MODEL,
  options={
    'temperature': 0.0
  },
  messages=[
    {
      'role': 'user',
      'content': 'What is in this image? Be concise.',
      'images': [path],
    },
  ],
)

print(response.message.content)
print(f"\nTrying passing base64 encoded image: {path}")
# You can also pass in base64 encoded image data
response = chat(
  model=MODEL,
  options={
    'temperature': 0.0
  },
  messages=[
    {
      'role': 'user',
      'content': 'What is in this image? Be concise.',
      'images': [img1],
    }
  ],
)
print(response.message.content)

print(f"\nTrying passing by raw bytes: {path}")
# the raw bytes
response = chat(
  model=MODEL,
  options={
    'temperature': 0.0
  },
  messages=[
    {
      'role': 'user',
      'content': 'What is in this image? Be concise.',
      'images': [img2],
    }
  ],
)
print(response.message.content)
"""

print(f"\nUnloading the model")
response = chat(
  model=MODEL,
  messages=[],
  keep_alive=0,
)
print(f"Model: {response.model}, result:{response.done_reason}")
