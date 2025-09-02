# This file is for classes defining model interfaces for intracting w/ ML models
# Note: the model interface here should be just that, the interface, the model shold be served elsewhere
import ollama
import openai
import time
import os
from google import genai
from google.api_core.exceptions import ResourceExhausted

# This interface is primarily for using in the UI auto-labeling of the collected images
# for fine tuning. The UI pulls the API key from the .env file GOOGLE_API_KEY variable
# if it is not in the config JSON.
class GeminiGenericInterface:
    def __init__(self, model_to_use='gemini-2.5-flash-lite', api_key='', api_base=None):
        self.api_base = api_base
        if model_to_use.startswith('models/'):
            self.model_to_use = model_to_use
        else:
            self.model_to_use = f"models/{model_to_use}"
        cur_api_key = api_key if api_key else os.getenv('GOOGLE_API_KEY')
        self.client = genai.Client(api_key=cur_api_key, http_options={"timeout": 30000})
        
        print(f"Using model: {self.model_to_use}")

    def __del__(self):
        print(f"Unloading model interface for: {self.model_to_use}")

    @staticmethod
    def model_name():
        return "google-genai"

    @staticmethod
    def model_parameters():
        return {
            "model_to_use": 'gemini-2.5-flash-lite',
            "api_key": '',
        }

    def gen_detect_prompt(self, obj_desc, image_desc):
        prompt = (
            f"Is there {obj_desc} absolutely certainly and clearly visible in this security camera image of {image_desc}? Answer strictly Yes or No."
        )
        return prompt

    def gen_locate_prompt(self, obj_desc, image_desc):
        prompt = (
            f"Describe the location of {obj_desc} in this security camera image of {image_desc}. Use 10 words or less. Focus on position relative to other objects."
        )
        return prompt

    def locate(self, image_data, obj_desc, image_desc, image_format='jpeg', do_location=True):
        ret = False
        msg = ""
        
        # Detection phase
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_to_use,
                    contents=[
                        {
                            'role': 'user',
                            'parts': [
                                {'text': self.gen_detect_prompt(obj_desc, image_desc)},
                                {
                                    'inline_data': {
                                        'mime_type': f'image/{image_format}',
                                        'data': image_data
                                    }
                                }
                            ]
                        }
                    ]
                )
                if 'yes' in response.text.lower():
                    ret = True
                    break
            except ResourceExhausted as e:
                print(f"Quota exceeded, retrying... ({attempt+1}/3)")
                time.sleep(2 ** attempt)
                continue
            except Exception as e:
                print(f"Gemini API error: {e}")
                return ret, None

        # Location phase
        if ret and do_location:
            try:
                response = self.client.models.generate_content(
                    model=self.model_to_use,
                    contents=[
                        {
                            'role': 'user',
                            'parts': [
                                {'text': self.gen_locate_prompt(obj_desc, image_desc)},
                                {
                                    'inline_data': {
                                        'mime_type': f'image/{image_format}',
                                        'data': image_data
                                    }
                                }
                            ]
                        }
                    ]
                )
                msg = response.text.strip('. \n\t').lower()
            except Exception as e:
                print(f"Error getting location: {e}")
                msg = ""

        return ret, msg

# This interface is primarily for using in the UI auto-labeling of the collected images
# for fine tuning. The UI pulls the OpenAI API key from the .env file OPENAI_API_KEY variable
# if it is not in the config JSON.
class OpenAiGenericInterface:
    def __init__(self, model_to_use='o4-mini', api_key='', api_base='https://api.openai.com/v1'):
        self.api_base = api_base
        self.model_to_use = model_to_use
        cur_api_key = api_key if len(api_key) > 0 else os.getenv('OPENAI_API_KEY', 'NONE')
        self.client = openai.OpenAI(api_key=cur_api_key, base_url=api_base)
        print(f"Using model: {self.model_to_use} with API base: {self.api_base}")

    def __del__(self):
        print(f"Unloading model interface for: {self.model_to_use}")

    @staticmethod
    def model_name():
        return "openai-generic"

    # What are the model parameters and their defaults
    @staticmethod
    def model_parameters():
        return {
            "model_to_use": 'o4-mini',
            "api_base": 'https://api.openai.com/v1',
            "api_key": '',
        }

    def gen_detect_prompt(self, obj_desc, image_desc):
        prompt = (
            f"Is there {obj_desc} clearly visible in this security camera image of {image_desc}? Answer strictly Yes or No."
        )
        return prompt

    def gen_locate_prompt(self, obj_desc, image_desc):
        prompt = (
            f"Describe the location of {obj_desc} in this security camera image of {image_desc}. Use 10 words or less. Focus on position relative to other objects."
        )
        return prompt

    def locate(self, image_data, obj_desc, image_desc, image_format='jpeg', do_location = True):
        prompt = self.gen_detect_prompt(obj_desc, image_desc)
        ret = False
        msg = None
        
        # Detection phase
        for attempt in range(3):  # Allow up to 3 retries
            try:
                rsp = self.client.chat.completions.create(
                    model=self.model_to_use,
                    temperature=1.0,
                    max_completion_tokens=2000,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/{image_format};base64,{image_data}"}},
                            ],
                        }
                    ],
                )
                ret = True if 'yes' in rsp.choices[0].message.content.lower() else False
                if not do_location or not ret:
                    msg = ""
                    return ret, msg
                break  # Success, exit retry loop
            except openai.OpenAIError as e:
                if e.code == 'rate_limit_exceeded':
                    retry_after = float(e.response.headers.get('retry-after', 1))  # Default to 1 second if not specified
                    print(f"Rate limit exceeded in detection phase. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"OpenAI {self.model_to_use} query error in the detection phase: {e}")
                    return ret, msg

        msg = ""
        prompt = self.gen_locate_prompt(obj_desc, image_desc)
        
        # Location phase
        for attempt in range(3):  # Allow up to 3 retries
            try:
                rsp = self.client.chat.completions.create(
                    model=self.model_to_use,
                    temperature=1.0,
                    max_completion_tokens=4000,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/{image_format};base64,{image_data}"}},
                            ]
                        }
                    ],
                )
                if rsp:
                    #print(f"Location:\n-----------\n{rsp}\n------------\n")
                    msg = rsp.choices[0].message.content.lower().strip('\r\n\t ')
                break  # Success, exit retry loop
            except openai.OpenAIError as e:
                if e.code == 'rate_limit_exceeded':
                    retry_after = float(e.response.headers.get('retry-after', 1))  # Default to 1 second if not specified
                    print(f"Rate limit exceeded in location phase. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"OpenAI {self.model_to_use} query error in location phase: {e}")
                    break  # Non-rate-limit error, exit retry loop

        return ret, msg

class VLLMLlama32Interface:
    def __init__(self, model_to_use='auto', api_key='', api_base='http://localhost:5050/v1'):
        self.api_base = api_base
        cur_api_key = api_key if len(api_key) > 0 else os.getenv('VLLM_API_KEY', 'NONE')
        self.client = openai.OpenAI(api_key=cur_api_key, base_url=api_base)
        try:
            if model_to_use is None or model_to_use == 'auto':
                models = self.client.models.list()
                for m in models:
                    model_to_use = m.id
                    break
        except:
            pass
        self.model_to_use = model_to_use
        print(f"Using model: {self.model_to_use} with API base: {self.api_base}")

    def __del__(self):
        print(f"Unloading model interface for: {self.model_to_use}")

    @staticmethod
    def model_name():
        return "vllm-complex"

    # What are the model parameters and their defaults
    @staticmethod
    def model_parameters():
        return {
            "model_to_use": 'auto',
            "api_base": 'http://localhost:5050/v1',
            "api_key": '',
        }

    def gen_detect_prompt(self, obj_desc, image_desc):
        prompt = (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
            "You are a helpful, concise assistant for locating objects in an image<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|><|image|>Is there {obj_desc} "
            f"in this image of the {image_desc}? Answer strictly Yes or No.<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>"
        )
        return prompt

    def gen_locate_prompt(self, obj_desc, image_desc):
        prompt = (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|>"
            "You are a helpful, concise assistant for locating objects in an image<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|><|image|>What's the **Location** "
            f"of {obj_desc} in this image of the {image_desc}? "
            "Answer in one sentence describing the **Location**.<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>"
        )
        return prompt

    def locate(self, image_data, obj_desc, image_desc, image_format='jpeg', do_location = True):
        prompt = self.gen_detect_prompt(obj_desc, image_desc)
        ret = False
        msg = None
        try:
            if self.model_to_use is None:
                models = self.client.models.list()
                for m in models:
                    self.model_to_use = m.id
                    break
            rsp = self.client.chat.completions.create(
                model=self.model_to_use,
                messages=[
                    {
                        "role": "watchman",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/{image_format};base64,{image_data}"}},
                        ]
                    }
                ],
                temperature=0.0,
                max_completion_tokens=8,
                stop='.',
            )
            ret = True if 'yes' in rsp.choices[0].message.content.lower() else False
            if not do_location or not ret:
                msg = ""
                return ret, msg
        except Exception as e:
            print(f"Exception querying VLLM {self.model_to_use}: {e}")
            return ret, msg

        msg = ""
        prompt = self.gen_locate_prompt(obj_desc, image_desc)
        try:
            rsp = self.client.chat.completions.create(
                model=self.model_to_use,
                messages=[
                    {
                        "role": "watchman",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/{image_format};base64,{image_data}"}},
                        ]
                    }
                ],
                temperature=0.0,
                max_completion_tokens=32,
                stop='.',
            )
            if rsp:
                msg = rsp.choices[0].message.content.lower().strip('\r\n\t ')
        except:
            pass
        return ret, msg

class OllamaLlama32Interface:
    def __init__(self, model_to_use='llama3.2-vision:11b-instruct-fp16', api_base='http://localhost:11434'):
        self.model_to_use = model_to_use
        self.client = None
        try:
            self.client = ollama.Client(host=api_base)
            rsp = self.client.chat(
                model = self.model_to_use,
                messages = [],
            )
            print(f"Model: {rsp.model}, result:{rsp.done_reason}")
        except Exception as e:
            print(f"Exception loading {self.model_to_use}: {e}")

    def __del__(self):
        try:
            if self.client is not None:
                rsp = self.client.chat(
                    model = self.model_to_use,
                    messages = [],
                    keep_alive = 0,
                )
                print(f"Model: {rsp.model}, result:{rsp.done_reason}")
        except Exception as e:
            print(f"Exception unloading {self.model_to_use}: {e}")
    
    # How this interface should be referred to in config
    @staticmethod
    def model_name():
        return "ollama-complex"

    # What are the model parameters and their defaults
    @staticmethod
    def model_parameters():
        return {
               "model_to_use": 'llama3.2-vision:11b-instruct-fp16',
               "api_base": 'http://localhost:11434',
        }

    # Detector prompt generator
    def gen_detect_prompt(self, obj_desc, image_desc):
        prompt = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful, concise assistant for locating objects in an image<|eot_id|>" + \
                f"<|start_header_id|>user<|end_header_id|><|image|>Is there {obj_desc} in this image of the {image_desc}? Answer strictly Yes or No.<|eot_id|>" + \
                "<|start_header_id|>assistant<|end_header_id|>"
        return prompt

    # Location prompt generator
    def gen_locate_prompt(self, obj_desc, image_desc):
        prompt = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful, concise assistant for locating objects in an image<|eot_id|>" + \
                f"<|start_header_id|>user<|end_header_id|><|image|>What's the **Location** of {obj_desc} in this image of the {image_desc}? Answer strictly with its **Location**.<|eot_id|>" + \
                "<|start_header_id|>assistant<|end_header_id|>"
        return prompt

    # Object locator interface
    # image_data: bas64 encoded image data
    # obj_desc: object description string (comes from config)
    # image_desc: image description (might be used to hint the model or generate message programmatically)
    # do_location: flag indicating to ask th emodel to provide verbal description of the object location
    # returns: tuple with the True/False for the detection result and a string with the verbal description of the location
    def locate(self, image_data, obj_desc, image_desc, do_location = True):
        prompt = self.gen_detect_prompt(obj_desc, image_desc)
        rsp = self.client.generate(
            model=self.model_to_use,
            prompt=prompt,
            images=[image_data],
            options={'temperature': 0.0, "template": None},
        )
        ret = False
        msg = None
        if not rsp.done:
            return ret, msg
        msg = ""
        ret = True if "yes" in rsp.response.lower() else False
        if not do_location or not ret:
            return ret, msg
        prompt = self.gen_locate_prompt(obj_desc, image_desc)
        rsp = self.client.generate(
            model=self.model_to_use,
            prompt=prompt,
            images=[image_data],
            options={'temperature': 0.0, "template": None},
        )
        if rsp.done:
            ret = True
            msg = rsp.response.lower().strip('\r\n\t ')
        return ret, msg

class OllamaSimpleInterface(OllamaLlama32Interface):
    @staticmethod
    def model_name():
        return "ollama-simple"

    def locate(self, image_data, obj_desc, image_desc, do_location=False):
        return super().locate(image_data, obj_desc, image_desc, do_location)

# add your class name and class object mappping here
MODELS = {
    OllamaSimpleInterface.model_name(): OllamaSimpleInterface,
    OllamaLlama32Interface.model_name(): OllamaLlama32Interface,
    VLLMLlama32Interface.model_name(): VLLMLlama32Interface,
    OpenAiGenericInterface.model_name(): OpenAiGenericInterface,
    GeminiGenericInterface.model_name(): GeminiGenericInterface,
}
