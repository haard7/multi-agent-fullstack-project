import streamlit as st
import os
import dotenv
import autogen
from postgres_da_ai_agent.modules.db import PostgresManager
from postgres_da_ai_agent.modules import llm

dotenv.load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
RESPONSE_FORMAT_CAP_REF = "RESPONSE_FORMAT"


def run_chatbot(user_input):
    db = PostgresManager()
    db.connect_with_url(DATABASE_URL)

    table_definitions = db.get_table_definitions_for_prompt()

    prompt = llm.add_cap_ref(
        f"Fulfill this request: {user_input}. ",
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

    # Define your agent logic from your code
    function_map = {
        "recommend_product": db.recommend_product,
        "buy_product": db.buy_product,
        "get_order_status": db.get_order_status,
    }

    admin_user_proxy_agent = autogen.UserProxyAgent(
        name="User_Proxy_Agent",
        system_message="You are the admin overseeing the chat...",
        code_execution_config=False,
        function_map=function_map,
    )

    product_recommendation_agent = autogen.AssistantAgent(
        name="Product_Recommendation_Agent",
        system_message="I recommend products based on customer preferences...",
        code_execution_config=False,
        function_map=function_map,
    )

    order_status_agent = autogen.AssistantAgent(
        name="Order_Status_Agent",
        system_message="I retrieve order details based on the order ID...",
        code_execution_config=False,
        function_map=function_map,
    )

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

    admin_user_proxy_agent.initiate_chat(
        groupchat_manager, clear_history=True, message=prompt
    )

    responses = []
    for message in groupchat.messages:
        responses.append(message["content"])  # assuming "content" stores the text output

    return responses


def main():
    st.title("Product Recommendation and Order Status Chatbot")

    st.write("Enter your request below:")
    user_input = st.text_input("Type here", "")

    if st.button("Submit"):
        if user_input:
            # Run the chatbot logic and get responses
            responses = run_chatbot(user_input)

            # Display the chat responses
            st.write("Chatbot Responses:")
            for response in responses:
                st.write(response)
        else:
            st.error("Please provide a prompt.")

if __name__ == "__main__":
    main()
