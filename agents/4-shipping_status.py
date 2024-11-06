import os
import dotenv
import argparse
import autogen
import datetime
from agents.modules.db import PostgresManager
from agents.modules import llm
from typing import Annotated, Literal
import json
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

# import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from termcolor import colored
import io
import requests
from autogen import (
    Agent,
    AssistantAgent,
    ConversableAgent,
    UserProxyAgent,
    register_function,
)
from autogen.agentchat.contrib.capabilities.vision_capability import VisionCapability
from autogen.agentchat.contrib.img_utils import get_pil_image, pil_to_data_uri
from autogen.agentchat.contrib.multimodal_conversable_agent import (
    MultimodalConversableAgent,
)
from autogen.code_utils import content_str

# from autogen.code_utils import content_str

dotenv.load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
RESPONSE_FORMAT_CAP_REF = "RESPONSE_FORMAT"

SQL_DELIMITER = "---------"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", help="The prompt for the AI")
    arg = parser.parse_args()

    if not arg.prompt:
        print("Please provide a prompt")
        return

    prompt = f"Fulfill this request: {arg.prompt}. "

    db = PostgresManager()
    db.connect_with_url(DATABASE_URL)

    table_definitions = db.get_table_definitions_for_prompt()

    prompt = llm.add_cap_ref(
        prompt,
        f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query related to cloth retail and shipping status of defective product or damaged product.",
        POSTGRES_TABLE_DEFINITIONS_CAP_REF,
        table_definitions,
    )

    llm_config = {
        "model": "gpt-4o",
        "config_list": autogen.config_list_from_json(
            env_or_file="OAI_CONFIG_LIST",
            filter_dict={"model": {"gpt-4o-mini"}},
        ),
        "seed": 44,
        "temperature": 0,
        # "request_timeout": 120,
        "functions": [
            {
                "name": "run_sql",
                "description": "Using orderid, it use the table 'Product_defect' or 'Package_damaged' based on the whether the request is related to defective product or damaged package respectively. Then it return the image url corresponding to that orderid",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "The SQL query to run",
                        }
                    },
                    "required": ["sql"],
                },
            }
        ],
    }

    llm_config_groupchat = {
        "model": "gpt-4o-mini",
        "config_list": autogen.config_list_from_json(
            env_or_file="OAI_CONFIG_LIST",
            filter_dict={"model": {"gpt-4o-mini"}},
        ),
        "seed": 44,
        "temperature": 0,
    }

    function_map = {
        # "recommend_product": db.recommend_product,
        # "buy_product": db.buy_product,
        "run_sql": db.run_sql,
    }

    def my_description(
        image_url: str, image_data: Image = None, lmm_client: object = None
    ) -> str:
        """
        This function takes an image URL and returns the description.

        Parameters:
            - image_url (str): The URL of the image.
            - image_data (PIL.Image): The image data.
            - lmm_client (object): The LLM client object.

        Returns:
            - str: A description of the color of the image.
        """
        # Print the arguments for illustration purpose
        print("image_url", image_url)
        print("image_data", image_data)
        print("lmm_client", lmm_client)

        img_uri = pil_to_data_uri(
            image_data
        )  # cast data into URI (str) format for API call
        lmm_out = lmm_client.create(
            context=None,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe the image in detail regarding the customer service for product or package return",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": img_uri,
                            },
                        },
                    ],
                }
            ],
        )
        description = lmm_out.choices[0].message.content
        description = content_str(description)

        # Convert the image into an array of pixels.
        pixels = np.array(image_data)

        # Calculate the average color.
        avg_color_per_row = np.mean(pixels, axis=0)
        avg_color = np.mean(avg_color_per_row, axis=0)
        avg_color = avg_color.astype(int)  # Convert to integer for color values

        # Format the average color as a string description.
        caption = f"""The image is from {image_url}
        It is about: {description}
        The average color of the image is RGB:
            ({avg_color[0]}, {avg_color[1]}, {avg_color[2]})"""

        print(caption)  # For illustration purpose

        return caption

    def terminate_message(*args):
        return "TERMINATE"

        # Update the chat flow for better user interaction and termination logic

    def handle_termination(response):
        if response.lower() in ["no", "no thanks", "thank you"]:
            return terminate_message()

    # def process_image_url(image_url: str):
    #     return f'this is the image to analyze using vision capability <img {image_url}">'

    # Proxy agent handling the user's main request and interaction
    admin_user_proxy_agent = autogen.UserProxyAgent(
        name="User_Proxy_Agent",
        system_message="You are the admin overseeing the chat. continue interacting with the respective agent until request is fulfilled.",
        code_execution_config=False,
        human_input_mode="ALWAYS",
        # function_map=function_map,
        is_termination_msg=handle_termination,
    )

    damage_defective_status_agent = autogen.AssistantAgent(
        name="damage_defective_status_agent",
        system_message="""For the customer queries related to defective product or damaged package,if use have image url in the input then proceed to the next agent otherwise check if use have given the order id. if none of both are given in input then I will ask for the order id or image url. if user enters the order id then I will retrieve the image url corresponding to that orderid from database otherwise proceed with provided image url from input""",
        code_execution_config=False,
        llm_config=llm_config,
        function_map=function_map,
    )

    image_explainer = MultimodalConversableAgent(
        name="image-explainer",
        max_consecutive_auto_reply=10,
        llm_config=llm_config,
        system_message="I will use image url and set it as image_url and use <img {image_url}> to analyze and give the description of the image of product or package image using my vision capability. here image_url is the url of the image.",
    )

    shipping_status_agent = autogen.AssistantAgent(
        name="shipping_status_agent",
        max_consecutive_auto_reply=10,
        llm_config=llm_config,
        system_message=""" I will use the description of the image from image_explainer agent and give the final one decision out of below with respective description as well as the image url.
        1) Refund: if product or package seems defective of damaged then I will provide the refund to the customer.
        2) Replace: if package is wet then I will replace the package
        3) Escalate to human agent: if there is no defect or damage then I will escalate to human agent for further assistance.
        """,
    )

    # autogen.agentchat.register_function(
    #     process_image_url,
    #     caller=image_explainer,
    #     executor=damage_defective_status_agent,
    #     name="process_image_url",
    #     description="function to process image url and set it as image_url and use <img {image_url}> to analyze and give the description of the image of product or package image using my vision capability.",
    # )

    groupchat = autogen.GroupChat(
        agents=[
            image_explainer,
            damage_defective_status_agent,
            admin_user_proxy_agent,
            shipping_status_agent,
        ],
        messages=[],
        max_round=13,
    )

    vision_capability = VisionCapability(
        lmm_config={
            "config_list": autogen.config_list_from_json(
                env_or_file="OAI_CONFIG_LIST",
                filter_dict={"model": {"gpt-4o-mini"}},
            ),
            "temperature": 0,
            "max_tokens": 500,
        },
        # custom_caption_func=my_description,
    )

    groupchat_manager = autogen.GroupChatManager(
        groupchat=groupchat, llm_config=llm_config_groupchat
    )

    vision_capability.add_to_agent(groupchat_manager)

    # Initiate the chat with the adjusted flow
    admin_user_proxy_agent.initiate_chat(
        groupchat_manager, clear_history=True, message=prompt
    )


if __name__ == "__main__":
    main()
