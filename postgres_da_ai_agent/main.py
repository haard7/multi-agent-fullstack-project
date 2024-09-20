import os
from postgres_da_ai_agent.modules.db import PostgresManager
from postgres_da_ai_agent.modules import llm
import dotenv
import argparse
import autogen

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
        USER_PROXY_PROMPT = (
            "You are the user proxy agent. Based on the user's request, route the task to the appropriate agent (either Product Recommendation Agent or Order Status Agent)."
        )
        PRODUCT_RECOMMENDATION_PROMPT = (
            "You are the Product Recommendation Agent. Your task is to analyze the user's preferences and provide product recommendations based on the available data in the database."
        )
        ORDER_STATUS_PROMPT = (
            "You are the Order Status Agent. Your task is to retrieve and provide the order status based on the user's request and available data in the database."
        )

        # Create the agents
        user_proxy = autogen.UserProxyAgent(
            name="User_Proxy",
            system_message=USER_PROXY_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
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
        )

        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)

        # Routing logic for the user proxy agent
        def route_request(prompt_text):
            if "recommend" in prompt_text.lower():
                user_proxy.forward_request_to(product_recommendation)
            elif "order status" in prompt_text.lower():
                user_proxy.forward_request_to(order_status)
            else:
                print("No matching agent found for the request.")

        # Initiate chat with routing
        user_proxy.initiate_chat(manager, clear_history=True, message=prompt)
        route_request(args.prompt)


if __name__ == "__main__":
    main()
