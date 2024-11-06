import os
import time
import asyncio
import threading
import dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import queue
import autogen
import json

from agents.modules.db import PostgresManager
from agents.modules import llm
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent
from autogen.agentchat import AssistantAgent, UserProxyAgent

# import numpy as np
from PIL import Image
from termcolor import colored
import io
import requests
from autogen import Agent, ConversableAgent
from autogen.agentchat.contrib.capabilities.vision_capability import VisionCapability
from autogen.agentchat.contrib.img_utils import get_pil_image, pil_to_data_uri
from autogen.agentchat.contrib.multimodal_conversable_agent import (
    MultimodalConversableAgent,
)
from autogen.code_utils import content_str


dotenv.load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
RESPONSE_FORMAT_CAP_REF = "RESPONSE_FORMAT"

SQL_DELIMITER = "---------"

app = Flask(__name__)
cors = CORS(app)

# Using queues to store messages for frontend
print_queue = queue.Queue()  # stores messages to send to frontend
user_queue = queue.Queue()  # stores user inputs

chat_status = "ended"

db = PostgresManager()
db.connect_with_url(DATABASE_URL)


# Define the ConversableAgent to handle user input asynchronously
class MyConversableAgent(autogen.ConversableAgent):
    async def a_get_human_input(self, prompt: str) -> str:
        input_prompt = "Please input your further direction, or type 'approved' to proceed, or type 'exit' to end the conversation"
        print_queue.put({"user": "System", "message": input_prompt})

        start_time = time.time()
        global chat_status
        chat_status = "inputting"
        while True:
            if not user_queue.empty():
                input_value = user_queue.get()
                chat_status = "Chat ongoing"
                return input_value
            if time.time() - start_time > 600:
                chat_status = "ended"
                return "exit"
            await asyncio.sleep(1)


# Print messages function for agent communication
# acts as message hub within conversation flow
def print_messages(recipient, messages, sender, config):
    print(
        f"Messages from: {sender.name} sent to: {recipient.name} | num messages: {len(messages)} | message: {messages[-1]}"
    )

    content = messages[-1]["content"]

    if all(key in messages[-1] for key in ["name"]):
        print_queue.put({"user": messages[-1]["name"], "message": content})
    elif messages[-1]["role"] == "user":
        print_queue.put({"user": sender.name, "message": content})
    else:
        print_queue.put({"user": recipient.name, "message": content})

    return False, None  # conversation continued


async def initiate_chat(agent, recipient, message):
    result = await agent.a_initiate_chat(
        recipient, message=message, clear_history=False
    )
    print(result)
    return result


# Define function to initialize agents and initiate chat
def run_chat(request_json):
    global chat_status

    function_map = {
        # "recommend_product": db.recommend_product,
        # "buy_product": db.buy_product,
        # "get_order_status": db.get_order_status,
        "run_sql": db.run_sql
    }
    try:
        user_input = request_json.get("message")
        agent_info = [
            {
                "name": "damage_defective_status_agent",
                "type": "AssistantAgent",
                "llm": {"model": "gpt-4o-mini"},
                "system_message": """For the customer queries related to defective product or damaged package, if user have not given the image url or order id then I will ask for the order id or image url. if user enters the order id then I will retrieve the image url corresponding to that orderid from database otherwise proceed with provided image url from input and give the image url in the format of "<img {image_url}>". here image_url is the url of the image.""",
                "description": "This is a assistant agent for getting image url and orderid for further analysis",
                # "function_map": function_map,
                "human_input_mode": "NEVER",
            },
            {
                "name": "image_explainer",
                "type": "MultimodalConversableAgent",
                "llm": {"model": "gpt-4o-mini"},
                "system_message": """I will use image url and set it as image_url and use <img {image_url}> to analyze and give the description of the image of product or package image using my vision capability. here image_url is the url of the image.""",
                "description": "it analyze the image using vision capability",
                # "function_map": function_map,
                "human_input_mode": "NEVER",
            },
            {
                "name": "package_shipping_status_agent",
                "type": "AssistantAgent",
                "llm": {"model": "gpt-4o-mini"},
                "system_message": """if the image is of product then I will use the description of the image from image_explainer agent and give the final one decision out of below with respective description as well as the image url.
                1) Refund: if product seems defective then I will provide the refund to the customer.
                2) Escalate to human agent: if there is no defect observed then I will escalate to human agent for further assistance.""",
                "description": " it gives the decision based on the image description",
                # "function_map": function_map,
                "human_input_mode": "NEVER",
            },
            {
                "name": "product_shipping_status_agent",
                "type": "AssistantAgent",
                "llm": {"model": "gpt-4o-mini"},
                "system_message": """if the image is of package then I will use the description of the image from image_explainer agent and give the final one decision out of below with respective description as well as the image url.
                1) Refund: if package seems seriously damaged then I will provide the refund to the customer.
                2) Replace: if package is wet then I will replace the package
                3) Escalate to human agent: if there is no defect or damage then I will escalate to human agent for further assistance.""",
                "description": " it gives the decision based on the image description",
                # "function_map": function_map,
                "human_input_mode": "NEVER",
            },
        ]
        task_info = {
            "id": 0,
            "name": "Personal Assistant",
            "description": "This is a powerful personal assistant.",
            "maxMessages": 30,
            "speakSelMode": "auto",
        }

        # Setup DB manager and connect
        # db = PostgresManager()
        # db.connect_with_url(DATABASE_URL)

        table_definitions = db.get_table_definitions_for_prompt()

        # AutoGen-related agents configuration
        prompt = f"Fulfill this request: {user_input}. "
        prompt = llm.add_cap_ref(
            prompt,
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query related to cloth retail and shipping status of defective product or damaged package.",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions,
        )

        # print("prompt: ", prompt)
        userproxy = create_userproxy()

        manager, assistants = create_groupchat(agent_info, task_info, userproxy)

        asyncio.run(initiate_chat(userproxy, manager, prompt))
        chat_status = "ended"

    except Exception as e:
        chat_status = "error"
        print_queue.put({"user": "System", "message": f"An error occurred: {str(e)}"})


def create_userproxy():
    db = PostgresManager()
    db.connect_with_url(DATABASE_URL)

    function_map = {
        # "recommend_product": db.recommend_product,
        # "buy_product": db.buy_product,
        # "get_order_status": db.get_order_status,
        "run_sql": db.run_sql
    }
    user_proxy = MyConversableAgent(
        name="User_Proxy",
        system_message="You are the admin overseeing the chat. continue interacting with the respective agent until request is fulfilled.",
        code_execution_config=False,
        is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
        human_input_mode="ALWAYS",
        # function_map=function_map,
    )
    user_proxy.register_reply(
        [autogen.Agent, None],
        reply_func=print_messages,
        config={"callback": None},
    )
    return user_proxy


agent_classes = {
    "GPTAssistantAgent": GPTAssistantAgent,
    "AssistantAgent": AssistantAgent,
    "MultimodalConversableAgent": MultimodalConversableAgent,
    "VisionCapability": VisionCapability,
    # add more type of agents...
}


def create_groupchat(agents_info, task_info, user_proxy):
    assistants = []

    db = PostgresManager()
    db.connect_with_url(DATABASE_URL)

    for agent_info in agents_info:
        if agent_info["type"] == "UserProxyAgent":
            continue

        llm_config = {
            "config_list": [agent_info["llm"]],
            "temperature": 0,
            "seed": 44,
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

        llm_config_manager = {
            "config_list": [agent_info["llm"]],
            "temperature": 0,
            "seed": 44,
        }

        AgentClass = agent_classes[agent_info["type"]]
        assistant = AgentClass(
            name=agent_info["name"],
            llm_config=llm_config,
            system_message=agent_info["system_message"],
            description=agent_info["description"],
            # function_map=agent_info["function_map"],
            human_input_mode=agent_info["human_input_mode"],
        )

        assistant.register_reply(
            [autogen.Agent, None],
            reply_func=print_messages,
            config={"callback": None},
        )
        assistants.append(assistant)

    if len(assistants) == 1:
        manager = assistants[0]

    elif len(assistants) > 1:
        groupchat = autogen.GroupChat(
            agents=[user_proxy] + assistants,
            messages=[],
            max_round=task_info["maxMessages"],
            speaker_selection_method=task_info["speakSelMode"],
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
        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config=llm_config_manager,
            system_message="",
        )
        vision_capability.add_to_agent(manager)

    return manager, assistants


# Flask routes
@app.route("/api/start_chat", methods=["POST", "OPTIONS"])
def start_chat():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    elif request.method == "POST":
        global chat_status
        try:
            if chat_status == "error":
                chat_status = "ended"

            with print_queue.mutex:
                print_queue.queue.clear()
            with user_queue.mutex:
                user_queue.queue.clear()

            chat_status = "Chat ongoing"

            thread = threading.Thread(target=run_chat, args=(request.json,))
            thread.start()

            return jsonify({"status": chat_status})
        except Exception as e:
            return jsonify({"status": "Error occurred", "error": str(e)})


@app.route("/api/send_message", methods=["POST"])
def send_message():
    user_input = request.json["message"]
    user_queue.put(user_input)
    return jsonify({"status": "Message Received"})


@app.route("/api/get_message", methods=["GET"])
def get_messages():
    global chat_status

    if not print_queue.empty():
        msg = print_queue.get()

        # If msg is already a dict, skip json.loads
        if isinstance(msg, str):  # Only attempt to load if it's a string
            try:
                msg = json.loads(msg)
            except json.JSONDecodeError:
                pass  # If `msg` is not a JSON string, keep it as is

        # Ensure the 'message' part is also parsed if it's a JSON string
        if isinstance(msg, dict) and isinstance(msg.get("message"), str):
            try:
                msg["message"] = json.loads(msg["message"])
            except json.JSONDecodeError:
                pass  # If the 'message' is not a JSON string, keep it as is

        return jsonify({"message": msg, "chat_status": chat_status}), 200
    else:
        return jsonify({"message": None, "chat_status": chat_status}), 200


# def get_messages():
#     global chat_status

#     if not print_queue.empty():
#         msg = print_queue.get()
#         try:
#             msg = json.loads(msg)
#         except json.JSONDecodeError:
#             pass  # If `msg` is not a JSON string, keep it as is

#         return jsonify({"message": msg, "chat_status": chat_status}), 200
#     else:
#         return jsonify({"message": None, "chat_status": chat_status}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=True)
