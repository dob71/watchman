# This file is for classes defining model interfaces for intracting w/ ML models
# Note: the model interface here should be just that, the interface, the model shold be served elsewhere
from ollama import chat, generate

class OllamaSimpleInterface:
    def __init__(self, model_to_use='llama3.2-vision:11b-instruct-fp16'):
        self.model_to_use = model_to_use
        rsp = chat(
            model = self.model_to_use,
            messages = [],
        )
        print(f"Model: {rsp.model}, result:{rsp.done_reason}")

    def __del__(self):
        rsp = chat(
            model = self.model_to_use,
            messages = [],
            keep_alive = 0,
        )
        print(f"Model: {rsp.model}, result:{rsp.done_reason}")
    
    # How this interface should be referred to in config
    @staticmethod
    def model_name():
        return "ollama-simple"

    # Object locator interface
    # image_data: bas64 encoded image data
    # obj_desc: object description string (comes from config)
    # image_desc: image description (might be used to hint the model or generate message programmatically)
    # returns: tuple with the True/False for the detection result and a string with the verbal description of the location
    def locate(self, image_data, obj_desc, image_desc):
        prompt = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful, concise assistant for locating objects in an image<|eot_id|>" + \
                f"<|start_header_id|>user<|end_header_id|><|image|>Is there {obj_desc} on the image? Answer strictly Yes or No<|eot_id|>" + \
                "<|start_header_id|>assistant<|end_header_id|>"
        rsp = generate(
            model=self.model_to_use,
            prompt=prompt,
            images=[image_data],
            options={'temperature': 0.0},
        )
        ret = False
        msg = None
        if rsp.done and "yes" in rsp.response.lower():
            ret = True
            msg = f""
        return ret, msg

class OllamaComplexInterface:
    def __init__(self, model_to_use='llama3.2-vision:11b-instruct-fp16'):
        self.model_to_use = model_to_use
        rsp = chat(
            model = self.model_to_use,
            messages = [],
        )
        print(f"Model: {rsp.model}, result:{rsp.done_reason}")

    def __del__(self):
        rsp = chat(
            model = self.model_to_use,
            messages = [],
            keep_alive = 0,
        )
        print(f"Model: {rsp.model}, result:{rsp.done_reason}")
    
    # How this interface should be referred to in config
    @staticmethod
    def model_name():
        return "ollama-complex"

    # Object locator interface
    # image_data: bas64 encoded image data
    # obj_desc: object description string (comes from config)
    # image_desc: image description (might be used to hint the model or generate message programmatically)
    # returns: tuple with the True/False for the detection result and a string with the verbal description of the location
    def locate(self, image_data, obj_desc, image_desc):
        prompt = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful, concise assistant for locating objects in an image<|eot_id|>" + \
                f"<|start_header_id|>user<|end_header_id|><|image|>Is there {obj_desc} on this image of the {image_desc}? Answer strictly Yes or No.<|eot_id|>" + \
                "<|start_header_id|>assistant<|end_header_id|>"
        rsp = generate(
            model=self.model_to_use,
            prompt=prompt,
            images=[image_data],
            options={'temperature': 0.0},
        )
        ret = False
        msg = None
        if rsp.done and not "yes" in rsp.response.lower():
            return ret, msg
        prompt = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful, concise assistant for locating objects in an image<|eot_id|>" + \
                f"<|start_header_id|>user<|end_header_id|><|image|>Where is the {obj_desc} in the image? Answer strictly with its **Location**<|eot_id|>" + \
                "<|start_header_id|>assistant<|end_header_id|>"
        rsp = generate(
            model=self.model_to_use,
            prompt=prompt,
            images=[image_data],
            options={'temperature': 0.0},
        )
        if rsp.done:
            ret = True
            msg = rsp.response.lower()
        return ret, msg

# add your class name and class object mappping here
MODELS = {
    OllamaSimpleInterface.model_name(): OllamaSimpleInterface,
    OllamaComplexInterface.model_name(): OllamaComplexInterface,
}
