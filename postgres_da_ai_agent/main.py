import os
import dotenv
import argparse
import autogen
import datetime
from postgres_da_ai_agent.modules.db import PostgresManager
from postgres_da_ai_agent.modules import llm

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
        f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query related to cloth retail.",
        POSTGRES_TABLE_DEFINITIONS_CAP_REF,
        table_definitions,
    )

    llm_config = {
        "model": "gpt-4o-mini",
        "config_list": autogen.config_list_from_json(
            env_or_file="OAI_CONFIG_LIST",
            filter_dict={"model": {"gpt-4o-mini"}},
        ),
        "seed": 44,
        "temperature": 0,
        "request_timeout": 120,
        "functions": [
            {
                "name": "recommend_product",
                "description": "Retrieves product recommendations based on the user's preferences by running SQL query against the postgres database",
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
                "name": "buy_product",
                "description": "Saves customer and order details when a product is purchased by running SQL query against the postgres database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "firstname": {
                            "type": "string",
                            "description": "First Name of the customer",
                        },
                        "lastname": {
                            "type": "string",
                            "description": "Last Name of the customer",
                        },
                        "email": {
                            "type": "string",
                            "description": "Email of the customer",
                        },
                        "phonenumber": {
                            "type": "string",
                            "description": "Phone Number of the customer",
                        },
                        "shippingaddress": {
                            "type": "string",
                            "description": "Shipping Address of the customer",
                        },
                        "creditcardnumber": {
                            "type": "string",
                            "description": "Credit Card Number of the customer",
                        },
                        "productid": {
                            "type": "integer",
                            "description": "The ID of the product being purchased",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity of the product",
                        },
                    },
                    "required": [
                        "firstname",
                        "lastname",
                        "email",
                        "phonenumber",
                        "shippingaddress",
                        "creditcardnumber",
                        "productid",
                        "quantity",
                    ],
                },
            },
            {
                "name": "get_order_status",
                "description": "Retrieves order status based on orderid",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "integer",
                            "description": "The ID of the order to retrieve status for",
                        }
                    },
                    "required": ["order_id"],
                },
            },
            # {
            #     "name": "product_recommendation_flow",
            #     "description": "Handles the flow for purchasing the product if user wants to buy the recommended product",
            #     "parameters": {
            #         "type": "object",
            #         "properties": {},
            #         "required": [],
            #     },
            # }
        ],
    }

    function_map = {
        "recommend_product": db.recommend_product,
        "buy_product": db.buy_product,
        "get_order_status": db.get_order_status,
        # "product_recommendation_flow": product_recommendation_flow,
    }

    def terminate_message(*args):
        return "TERMINATE"

        # Update the chat flow for better user interaction and termination logic

    def handle_termination(response):
        if response.lower() in ["no", "no thanks", "thank you"]:
            return terminate_message()

    # Proxy agent handling the user's main request and interaction
    admin_user_proxy_agent = autogen.UserProxyAgent(
        name="User_Proxy_Agent",
        system_message="You are the admin overseeing the chat. Continue interacting with the appropriate agent until the request is fulfilled. ask user for details if product is recommended and user wants to buy it. also make sure the order details are returned to the user after the purchase is made.",
        code_execution_config=False,
        human_input_mode="ALWAYS",
        function_map=function_map,
        is_termination_msg=handle_termination,
    )

    product_recommendation_agent = autogen.AssistantAgent(
        name="Product_Recommendation_Agent",
        system_message="I recommend products based on customer preferences. After recommendation, I will ask if the customer wants to purchase the product before saving the customer and order details.",
        code_execution_config=False,
        llm_config=llm_config,
        function_map=function_map,
    )

    order_status_agent = autogen.AssistantAgent(
        name="Order_Status_Agent",
        system_message="I retrieve order details based on the order ID provided by the customer.",
        code_execution_config=False,
        llm_config=llm_config,
        function_map=function_map,
    )

    # Modify interaction flow to handle purchase confirmation and termination
    def handle_purchase_flow(response):
        if response.lower() in ["yes", "i want to buy", "i will buy"]:
            # Proceed with collecting purchase details
            return (
                "Please provide the following details to complete your purchase:\n"
                "1. First Name:\n"
                "2. Last Name:\n"
                "3. Email:\n"
                "4. Phone Number:\n"
                "5. Shipping Address:\n"
                "6. Credit Card Number:\n"
                "7. Quantity (how many would you like to buy?):"
            )
        else:
            return "Okay! Let me know if you'd like help with something else."

    # Asking if the user needs further assistance after providing order status
    def ask_for_further_help():
        return "Do you need any other help? (You can say 'No, thanks' to end the chat)"

        return ask_for_further_help()

    # Agent triggers product recommendation and waits for user response
    def product_recommendation_flow():
        # Recommend a product here
        product = db.recommend_product(gender="Men")

        # Ask the user if they want to purchase after recommendation
        recommendation_message = (
            f"We recommend: {product['productname']} by {product['productbrand']}\n"
            f"Price: {product['price']}\n"
            f"Would you like to purchase this product? (Yes/No)"
        )

        # Wait for user response to decide whether to proceed with purchase
        user_response = input(
            recommendation_message
        )  # Assuming input is used for simplicity
        return handle_purchase_flow(user_response)

    groupchat = autogen.GroupChat(
        agents=[
            admin_user_proxy_agent,
            product_recommendation_agent,
            order_status_agent,
        ],
        messages=[],
        max_round=20,
    )

    groupchat_manager = autogen.GroupChatManager(
        groupchat=groupchat, llm_config=llm_config
    )

    # Initiate the chat with the adjusted flow
    admin_user_proxy_agent.initiate_chat(
        groupchat_manager, clear_history=True, message=prompt
    )


if __name__ == "__main__":
    main()
