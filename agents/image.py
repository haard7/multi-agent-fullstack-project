import autogen
from autogen import Agent, AssistantAgent, ConversableAgent, UserProxyAgent
from autogen.agentchat.contrib.capabilities.vision_capability import VisionCapability
from autogen.agentchat.contrib.multimodal_conversable_agent import (
    MultimodalConversableAgent,
)
from agents.modules.db import PostgresManager
import os

# Database connection setup
db = PostgresManager()
db.connect_with_url(os.environ.get("DATABASE_URL"))

# Define function map for database operations
function_map = {
    "get_totalprice_from_db": db.get_totalprice,  # Retrieve total price for a given order ID
}

config_list_gpt4o_mini = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    filter_dict={
        "model": [
            "gpt-4o-mini",
        ]
    },
)


gpt4_llm_config = {"config_list": config_list_gpt4o_mini, "cache_seed": 42,
                   "functions": [
                       {
                            "name": "get_totalprice_from_db",
                            "description": "Retrieves totalprice for a particular orderid",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "order_id": {
                                        "type": "integer",
                                        "description": "The ID of the order to retrieve totalprice for",
                                    }
                                },
                                "required": ["order_id"],
                            },
                        }
                   ]}


# OCR Extraction Agent (for extracting order details from OCR image)
ocr_agent = AssistantAgent(
    name="OCRExtractionAgent",
    system_message="Extracts order details (e.g., Order ID, Quantity, Price, and Billed Price) from OCR image.",
    max_consecutive_auto_reply=10,
    code_execution_config={"use_docker": False},
    llm_config=gpt4_llm_config,
)

# Proxy Agent to manage communication and task assignment
user_proxy = UserProxyAgent(
    name="User_proxy",
    system_message="Your role is to coordinate the workflow by directing tasks to the appropriate agents to process the image, retrieve data, and classify the order.\n\n"
    "Workflow:\n"
    "1. **OCR Extraction**: First, direct the OCR Extraction Agent to analyze the provided image and extract key details, such as the Order ID and Billed Price.\n"
    "2. **Database Retrieval**: Once the Order ID is extracted, instruct the Database Retrieval Agent to fetch the Total Price associated with this Order ID from the database.\n"
    "3. **Order Verification**: After obtaining both the Billed Price from the OCR Extraction Agent and the Total Price from the Database Retrieval Agent, engage the Order Verification Agent to classify the order.\n\n"
    "Ensure each step is completed in sequence, and facilitate the workflow by gathering and passing along relevant details between agents.",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
    code_execution_config={"use_docker": False},
)

# Database Retrieval Agent (for fetching total price from DB)
db_retrieval_agent = AssistantAgent(
    name="DBRetrievalAgent",
    system_message="Retrieve the total price from the database for a given order ID.",
    llm_config=gpt4_llm_config,
    function_map=function_map,
    code_execution_config=False,
)

# Order Verification Agent to validate the order
order_verification_agent = AssistantAgent(
    name="OrderVerificationAgent",
    system_message=(
        "Verify the order details extracted from OCR by retrieving the total price from the database for the given order ID. "
        "Then, compare it with the billed price provided from the OCR data, and classify the order as follows:\n\n"
        "- Refund if the billed price does not match the total price in the database.\n"
        "- Decline if the billed price matches the total price in the database.\n"
        "- Escalate if the order ID is not found in the database.\n\n"
        "Provide a clear justification with your final classification."
    ),
    llm_config=gpt4_llm_config,
    code_execution_config=False,
)

# We set max_round to 5
groupchat = autogen.GroupChat(
    agents=[user_proxy, ocr_agent, db_retrieval_agent, order_verification_agent], messages=[], max_round=5
)

vision_capability = VisionCapability(
    lmm_config={
        "config_list": config_list_gpt4o_mini,
        "temperature": 0,
        "max_tokens": 300,
    }
)
group_chat_manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config={  # Use basic config without functions
        "model": "gpt-4o-mini",
        "config_list": config_list_gpt4o_mini,
        "seed": 42,
        "temperature": 0,
    },
)
vision_capability.add_to_agent(group_chat_manager)

# Refund Image url:
# 
# https://i.ibb.co/wsPHhH3/ocr-Refund.png

# Decline Image url:
# 
# https://i.ibb.co/LQsgf0F/ocr-Decline.png

# Escalate Image url:
# 
# https://i.ibb.co/T2V2NYY/ocr2.png

# Start the conversation  # Replace with actual image URL
initial_prompt = (
    f"Please analyze the following image for order details and verify the billed price "
    f"by comparing it to the totalprice in the database for order classification.\n"
    f"Image URL: <img https://i.ibb.co/wsPHhH3/ocr-Refund.png>"
)

rst = user_proxy.initiate_chat(
    group_chat_manager,
    message=initial_prompt,
)
