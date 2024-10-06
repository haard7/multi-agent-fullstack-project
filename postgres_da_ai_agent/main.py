import os
from postgres_da_ai_agent.modules.db import PostgresManager
from postgres_da_ai_agent.modules import llm
import dotenv
import argparse
import autogen
import datetime
from autogen import Agent

dotenv.load_dotenv()

assert os.environ.get("DATABASE_URL"), "POSTGRES_CONNECTION_URL not found in .env file"
assert os.environ.get("OPENAI_API_KEY"), "OPENAI_API_KEY not found in .env file"

DB_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
RESPONSE_FORMAT_CAP_REF = "RESPONSE_FORMAT"
SQL_DELIMITER = "---------"


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

        # GPT configuration
        gpt4_config = {
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
                }
            ],
        }

        # SQL function map
        function_map = {
            "run_sql": db.run_sql,
        }

        # Termination message function
        def is_termination_msg(content):
            have_content = content.get("content", None) is not None
            return have_content and "APPROVED" in content["content"]

        # Prompts for each agent
        USER_PROXY_PROMPT = "You are the user proxy agent. Based on the user's request, route the task to the appropriate agent (either Product Recommendation Agent or Order Status Agent)."
        PRODUCT_RECOMMENDATION_PROMPT = (
            # "You are the Product Recommendation Agent. Your task is to analyze the user's preferences and provide a single product recommendation based on the available data in the database, if there are multiple products eligible for recommendation then only return the first product,"
            # "handle order processing if the user chooses to purchase the product."
            "You are the Product Recommendation Agent. Your task is to analyze the user's preferences and provide a single product recommendation based on the available data in the database. After providing the recommendation, include a message asking if the user would like to purchase the product. if user says yes to buy the product then collect user information and save it in the database in its appropriate place. also save the order informaiton in the database."
        )
        ORDER_STATUS_PROMPT = "You are the Order Status Agent. Your task is to retrieve and provide the order status based on the user's request and available data in the database."

        # Create the agents
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
            is_termination_msg=is_termination_msg,
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

        # Create a group chat
        groupchat = autogen.GroupChat(
            agents=[user_proxy, product_recommendation, order_status],
            messages=[],
            max_round=10,
            # speaker_selection_method = custom_speaker_selection_method,
        )

        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)

        # Routing logic for the user proxy agent
        # old routing logic
        #   def route_request(prompt_text):
        #     if "recommend" in prompt_text.lower():
        #         print(prompt_text + " - Routing to Product Recommendation Agent")
        #         user_proxy.forward_request_to(product_recommendation)
        #     elif "order status" in prompt_text.lower():
        #         user_proxy.forward_request_to(order_status)
        #     else:
        #         print("No matching agent found for the request.")

        # Handle Purchase confirmation flow

        # def custom_speaker_selection_method(
        #     last_speaker: Agent, groupchat: autogen.GroupChat
        # ):
        #     if last_speaker is user_proxy:
        #         return product_recommendation

        def get_response_from_agent(manager, agent):
            print("Haard: it is calling me")
            # I want to get the last response from the agent for further processing

        def handle_purchase_and_payment_flow(manager, db, first_recommended_product):
            purchase_confirmation = input("Do you want to buy this product? (yes/no): ")
            if purchase_confirmation.lower() == "yes":
                # collect user information
                firstname = input("Enter your first name: ")
                lastname = input("Enter your last name: ")
                email = input("Enter your email: ")
                phonenumber = input("Enter your phone number: ")
                shippingaddress = input("Enter your shipping address: ")
                creditcardnumber = input("Enter your credit card number: ")

                # save customer information into customer table
                customer_id = db.save_customer(
                    firstname,
                    lastname,
                    email,
                    phonenumber,
                    shippingaddress,
                    creditcardnumber,
                )

                quantity = 1  # Assuming the quantity is 1 for simplicity
                order_date = (
                    datetime.date.today()
                )  # Assuming today's date for the order date
                total_price = first_recommended_product[
                    "price"
                ]  # Assuming the price is fetched from the recommended product

                order_id = db.create_order(
                    customer_id=customer_id,
                    product_id=first_recommended_product["productid"],
                    order_date=order_date,
                    quantity=quantity,
                    total_price=total_price,
                    order_status="Pending",  # Set the initial status to 'Pending'
                )

                print(f"Order placed successfully! Your order ID is {order_id}.")

            else:
                print("Purchase cancelled.")

        # Initiate chat with routing
        user_proxy.initiate_chat(manager, clear_history=True, message=prompt)
        # route_request(args.prompt)

        # route_request(args.prompt, manager, groupchat)

        # After recommendation prompt for purchase

        # product_recommendation_response = manager.get_response_from_agent(
        #     product_recommendation
        # )

        product_recommendation_response = get_response_from_agent(
            manager, product_recommendation
        )

        if product_recommendation_response:
            recommended_products = llm.safe_get(
                product_recommendation_response, "choices.0.message.content"
            )

            if recommended_products:
                first_recommended_product = recommended_products[0]

                # extract required information from the product recommendation
                product_id = first_recommended_product.get("productid")
                product_name = first_recommended_product.get("productname")

                import json

                print(json.dumps(first_recommended_product, indent=4))

                # handle purchase confirmation
                handle_purchase_and_payment_flow(manager, db, first_recommended_product)
            else:
                print(
                    json.dumps({"message": "No product recommendation found"}, indent=4)
                )
        else:
            print(
                json.dumps(
                    {"message": "No response from Product Recommendation Agent"},
                    indent=4,
                )
            )

        # print(product_recommendation_response)
        # purchase_confirmation = input("Do you want to buy this product? (yes/no): ")
        # handle_purchase_and_payment_flow(purchase_confirmation)


if __name__ == "__main__":
    main()
