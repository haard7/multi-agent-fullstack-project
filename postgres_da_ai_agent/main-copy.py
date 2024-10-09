import os
import dotenv
import argparse
import autogen
import datetime
from postgres_da_ai_agent.modules.db import PostgresManager
from postgres_da_ai_agent.modules import llm

dotenv.load_dotenv()

assert os.environ.get("DATABASE_URL"), "POSTGRES_CONNECTION_URL not found in .env file"
assert os.environ.get("OPENAI_API_KEY"), "OPENAI_API_KEY not found in .env file"

DB_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
RESPONSE_FORMAT_CAP_REF = "RESPONSE_FORMAT"
SQL_DELIMITER = "---------"


# def is_termination_msg(content):
#     print("Checking termination: " + str(content.get("content")))
#     if not content.get("content"):
#         return False
#     message = content["content"].lower().strip()
#     termination_phrases = [
#         "terminate",
#         "end conversation",
#         "finish",
#         "goodbye",
#         "thank you, that's all",
#         "exit",
#         "quit",
#         "done",
#         "that's all i need",
#         "order confirmed",
#         "order completed",
#         "no, i don't want to purchase",
#     ]
#     return any(phrase in message for phrase in termination_phrases)


def is_termination_msg(content):
    have_content = content.get("content", None) is not None
    return have_content and "APPROVED" in content["content"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", help="The prompt for the AI")
    args = parser.parse_args()

    if not args.prompt:
        print("Please provide a prompt")
        return

    prompt = f"Fulfill this request: {args.prompt}. "

    with PostgresManager() as db:
        db.connect_with_url(DB_URL)
        table_definitions = db.get_table_definitions_for_prompt()
        prompt = llm.add_cap_ref(
            prompt,
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the request.",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions,
        )

        gpt4_config = {
            "model": "gpt-4o-mini",
            "use_cache": False,
            "temperature": 0,
            "config_list": autogen.config_list_from_models(["gpt-4o-mini"]),
            "request_timeout": 120,
            "functions": [
                {
                    "name": "run_sql",
                    "description": "Run a SQL query against the postgres database",
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
                },
                {
                    "name": "save_customer",
                    "description": "Save customer information to the database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "firstname": {"type": "string"},
                            "lastname": {"type": "string"},
                            "email": {"type": "string"},
                            "phonenumber": {"type": "string"},
                            "shippingaddress": {"type": "string"},
                            "creditcardnumber": {"type": "string"},
                        },
                        "required": [
                            "firstname",
                            "lastname",
                            "email",
                            "phonenumber",
                            "shippingaddress",
                            "creditcardnumber",
                        ],
                    },
                },
                {
                    "name": "create_order",
                    "description": "Create a new order in the database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customerid": {"type": "integer"},
                            "product_id": {"type": "integer"},
                            "order_date": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "total_price": {"type": "number"},
                            "order_status": {"type": "string"},
                        },
                        "required": [
                            "customerid",
                            "product_id",
                            "order_date",
                            "quantity",
                            "total_price",
                            "order_status",
                        ],
                    },
                },
            ],
        }

        function_map = {
            "run_sql": db.run_sql,
            "save_customer": db.save_customer,
            "create_order": db.create_order,
        }

        USER_PROXY_PROMPT = """
        You are the user proxy agent. Your task is to:
        1. Analyze the initial user request.
        2. If the request is about product recommendations or purchases, route it to the Product Recommendation Agent.
        3. If the request is about order status, route it to the Order Status Agent.
        4. After the initial routing, continue to facilitate communication between the user and the chosen agent until termination conditions are met.
        5. Do not allow switching between agents unless the user explicitly requests it.
        6. Any time you see any termination message, terminate the conversation.
        7. Ensure that when a customer wants to purchase a product, both customer information saving and order creation are completed in the same response.
        8. finally terminate the conversation with "APPROVED".
        """

        PRODUCT_RECOMMENDATION_PROMPT = """
        You are the Product Recommendation Agent. Your task is to:
        1. Provide product recommendations based on the user's request and available data in the database.
        2. Use the run_sql function to query the database for product information.
        3. Provide a clear and concise summary of the product recommendations to the user.
        4. If the user wants to purchase a product, ensure that both customer information saving and order creation are completed in the same response.
        5. After providing the product recommendations, indicate that the conversation can be terminated.
        6. finally terminate the conversation with "APPROVED".
        """

        ORDER_STATUS_PROMPT = """
        You are the Order Status Agent. Your task is to:
        1. Retrieve and provide the all the details of order for order status based on the user's request and available data in the database.
        2. Use the run_sql function to query the database for order information.
        3. Provide a clear and concise summary of the order status to the user.
        4. After providing the order status, indicate that the conversation can be terminated.
        5. finally terminate the conversation with "APPROVED".
        """

        user_proxy = autogen.UserProxyAgent(
            name="User_Proxy",
            system_message=USER_PROXY_PROMPT,
            code_execution_config=False,
            human_input_mode="TERMINATE",
            is_termination_msg=is_termination_msg,
        )

        product_recommendation = autogen.AssistantAgent(
            name="Product_Recommendation",
            llm_config=gpt4_config,
            system_message=PRODUCT_RECOMMENDATION_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            function_map=function_map,
        )

        order_status = autogen.AssistantAgent(
            name="Order_Status",
            llm_config=gpt4_config,
            system_message=ORDER_STATUS_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg,
            function_map=function_map,
        )

        groupchat = autogen.GroupChat(
            agents=[user_proxy, product_recommendation, order_status],
            messages=[],
            max_round=15,
        )

        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config=gpt4_config,
            system_message="""
            You are the group chat manager. Your role is to:
            - Monitor the conversation between the user and the agents.
            - Ensure that the conversation is progressing smoothly.
            - Make sure user input is taken for further response from the agents.
            """,
        )

        user_proxy.initiate_chat(manager, clear_history=True, message=prompt)


if __name__ == "__main__":
    main()
