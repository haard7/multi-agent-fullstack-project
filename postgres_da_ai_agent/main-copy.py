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


def is_termination_msg(content):
    print("Checking termination: " + str(content.get("content")))
    if not content.get("content"):
        return False
    message = content["content"].lower().strip()
    termination_phrases = [
        "terminate",
        "end conversation",
        "finish",
        "goodbye",
        "thank you, that's all",
        "exit",
        "quit",
        "done",
        "that's all i need",
        "order confirmed",
        "order completed",
        "no, i don't want to purchase",
    ]
    return any(phrase in message for phrase in termination_phrases)


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
                            "customer_id": {"type": "integer"},
                            "product_id": {"type": "integer"},
                            "order_date": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "total_price": {"type": "number"},
                            "order_status": {"type": "string"},
                        },
                        "required": [
                            "customer_id",
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
        """

        PRODUCT_RECOMMENDATION_PROMPT = """
        You are the Product Recommendation Agent. Your task is to:
        1. Analyze the user's preferences and provide a single product recommendation based on the available data in the database. Use the run_sql function directly for any database queries.
        2. After providing the recommendation, ask if the user would like to purchase the product.
        3. If the user agrees to purchase, gather the following information:
           - First name
           - Last name
           - Email
           - Phone number
           - Shipping address
           - Credit card number
        4. Use the save_customer function to save the customer information.
        5. Use the create_order function to create a new order with status "processing".
        6. Execute both the save_customer and create_order functions in the same response.
        7. Provide a summary of the order to the user. Include Order ID, Order Date, Product Name, Quantity, Total Price, and Order Status.
        8. After completing the order, indicate that the conversation can be terminated.
        """

        ORDER_STATUS_PROMPT = """
        You are the Order Status Agent. Your task is to:
        1. Retrieve and provide the order status based on the user's request and available data in the database.
        2. Use the run_sql function to query the database for order information.
        3. Provide a clear and concise summary of the order status to the user.
        4. After providing the order status, indicate that the conversation can be terminated.
        """

        user_proxy = autogen.UserProxyAgent(
            name="User_Proxy",
            system_message=USER_PROXY_PROMPT,
            code_execution_config=False,
            human_input_mode="ALWAYS",
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
            - Ensure one conversation stays continuous until a termination message is received for a particular agent.
            - Facilitate agent switching only if the user explicitly requests it.
            - Verify that both customer information saving and order creation are completed when a purchase is made.
            """,
        )

        user_proxy.initiate_chat(manager, clear_history=True, message=prompt)


if __name__ == "__main__":
    main()
