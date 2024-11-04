import json
import os
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

# import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from termcolor import colored
import io
import requests

import autogen
from autogen import Agent, AssistantAgent, ConversableAgent, UserProxyAgent
from autogen.agentchat.contrib.capabilities.vision_capability import VisionCapability
from autogen.agentchat.contrib.img_utils import get_pil_image, pil_to_data_uri
from autogen.agentchat.contrib.multimodal_conversable_agent import (
    MultimodalConversableAgent,
)
from autogen.code_utils import content_str

config_list_gpt4o_mini = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    filter_dict={
        "model": [
            "gpt-4o-mini",
        ]
    },
)


gpt4_llm_config = {"config_list": config_list_gpt4o_mini, "cache_seed": 42}


agent1 = MultimodalConversableAgent(
    name="image-explainer-1",
    max_consecutive_auto_reply=10,
    llm_config={
        "config_list": config_list_gpt4o_mini,
        "temperature": 0,
        "max_tokens": 300,
    },
    system_message="from image you have to decide to refund, replace or escalate to human agent by analyzing the image. if product is defective or package is damaged then refund it. else if package is wet then replace it. else escalate to human agent if product or package looks good without any damage.",
)
agent2 = MultimodalConversableAgent(
    name="image-explainer-2",
    max_consecutive_auto_reply=10,
    llm_config={
        "config_list": config_list_gpt4o_mini,
        "temperature": 0,
        "max_tokens": 300,
    },
    system_message="Just describe the image",
)



user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    system_message="given image is either of product or package. interact with the agents for respective decision and description",
    human_input_mode="TERMINATE",  # Try between ALWAYS, NEVER, and TERMINATE
    max_consecutive_auto_reply=10,
    code_execution_config={
        "use_docker": False
    },  # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
)

# We set max_round to 5
groupchat = autogen.GroupChat(
    agents=[agent1, agent2, user_proxy], messages=[], max_round=5
)

vision_capability = VisionCapability(
    lmm_config={
        "config_list": config_list_gpt4o_mini,
        "temperature": 0,
        "max_tokens": 300,
    }
)
group_chat_manager = autogen.GroupChatManager(
    groupchat=groupchat, llm_config=gpt4_llm_config
)
vision_capability.add_to_agent(group_chat_manager)

# r = requests.get(
#     "https://i.imgur.com/ElLuHVN.png",
#     stream=True,
# )
# aux_im = Image.open(io.BytesIO(r.content))

rst = user_proxy.initiate_chat(
    group_chat_manager,
    message="""describe this image:
                        <img https://i.postimg.cc/wMqvrqPy/dam1.png>.""",
)
