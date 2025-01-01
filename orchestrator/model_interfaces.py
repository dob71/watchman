# This file is for classes defining model interfaces for intracting w/ ML models
# Note: the model interface here should be just that, the interface, the model should be served elsewhere
# But due to time constraints, we are invoking the models directly here.
from ollama import chat, generate
from ultralytics import YOLO
import torch
import os
import math

from dotenv import load_dotenv
from shared_settings import *

# Figure the path to the data folders depending on where we run
DATA_DIR = ''
if not os.path.exists('/.dockerenv'):
    load_dotenv('./.env')
    DATA_DIR = os.getenv('DATA_DIR')

# We'll need the images and config folders.
IMGDIR = f"{DATA_DIR}/{IMG_dir}"
CFGDIR = f"{DATA_DIR}/{CFG_dir}"

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
    # obj_id: class of object to detect
    # obj_desc: object description string (comes from config)
    # image_desc: image description (might be used to hint the model or generate message programmatically)
    # returns: tuple with the True/False for the detection result and a string with the verbal description of the location
    def locate(self, image_data, obj_id, obj_desc, image_desc):
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
    # obj_id: class of object to detect
    # obj_desc: object description string (comes from config)
    # image_desc: image description (might be used to hint the model or generate message programmatically)
    # returns: tuple with the True/False for the detection result and a string with the verbal description of the location
    def locate(self, image_data, obj_id, obj_desc, image_desc):
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

class YoloInterface:
    def __init__(self, model_to_use='yolo11s.pt'):
        self.model_to_use = model_to_use
        # Check if GPU is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Model: {model_to_use}, Using device: {self.device}")

    def __del__(self):
        print(f"Model: {self.model_to_use} deleted")
    
    # How this interface should be referred to in config
    @staticmethod
    def model_name():
        return "yolo"

    # Object locator interface
    # image_data: base64 encoded image data
    # obj_id: class of object to detect
    # obj_desc: object description string (comes from config)
    # image_desc: image description (might be used to hint the model or generate message programmatically)
    # returns: tuple with the True/False for the detection result and a string with the verbal description of the location
    def locate(self, image_data, obj_id, obj_desc, image_desc):
        model = YOLO(f"{self.model_to_use}") 
        results = model(image_data)
        result = results[0]

        class_list = list(model.names.values())
        class_id = class_list.index(obj_id)
        present = False
        index = 0
        list_of_detections = list()

        # Collect info on all dectections in the image
        for detected_id in result.boxes.cls:
            if class_id == detected_id:
                present = True
                notant = find_notant(result.boxes, index)
                nearby_obj_class = find_nearby_obj_class(result.boxes, index)
                list_of_detections.append((notant, nearby_obj_class))
                index += 1

        present = class_id in result.boxes.cls

        # Generate response message
        if present:
            msg = ""
            if len(list_of_detections) == 1:
                msg += f"A {obj_id} is near the {list_of_detections[0][0]} of the image. "
                if list_of_detections[0][1] is not None:
                    msg += f"It is next to a {class_list[int(list_of_detections[0][1].item())]}."
            else:
                msg += f"There are multiple {obj_id}s in the image. "
                for i in range(len(list_of_detections)):
                    msg += f"{obj_id} {i + 1} is near the {list_of_detections[i][0]} of the image. "
                    if list_of_detections[i][1] is not None:
                        if class_id == int(list_of_detections[i][1].item()):
                            msg += f"It is next to another {class_list[int(list_of_detections[i][1].item())]}. "
                        else:
                            msg += f"It is next to a {class_list[int(list_of_detections[i][1].item())]}. "
        else:
            msg = None

        return present, msg

    def __get_center_of_box(box):
        x = (box[0] + box[2]) / 2
        y = (box[1] + box[3]) / 2
        return {"x" : x, "y" : y}

    def __euclidean_distance(box1, box2):
        center1 = get_center_of_box(box1)
        center2 = get_center_of_box(box2)
        return ((center1["x"] - center2["x"])**2 + (center1["y"] - center2["y"])**2)**0.5
        
    def __find_notant(result_boxes, index):
        notant_list = ["top-left corner", "top", "top-right corner", "left-hand side", "center", "right-hand side", "bottom-left corner", "bottom", "bottom-right corner"]
        center = get_center_of_box((result_boxes.xyxyn[index]))
        notant_idx = math.floor(center["x"]/0.33) + (math.floor(center["y"]/0.33) * 3)
        return notant_list[notant_idx]

    def __find_nearby_obj_class(result_boxes, index, distance_threshold = 0.2):
        box_of_interest = result_boxes.xyxyn[index]
        min_dist = distance_threshold
        min_index = None
        for i in range(len(result_boxes)):
            if i != index:
                dist = euclidean_distance(box_of_interest, result_boxes.xyxyn[i])
                if dist <= min_dist:
                    min_dist = dist
                    min_index = i

        if min_index != None:
            return result_boxes.cls[min_index]
        else:
            return None

# add your class name and class object mappping here
MODELS = {
    OllamaSimpleInterface.model_name(): OllamaSimpleInterface,
    OllamaComplexInterface.model_name(): OllamaComplexInterface,
    YoloInterface.model_name(): YoloInterface
}
