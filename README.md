## Branch: `feature/ui-integration`

### Description

- Now it works with Python based Flask API. now we will run the `api.py` file to run flask app
- you can run either main.py.
- First create the database using "ClothShop.sql" file in PostgreSQL. I have updated the schema in the next queries so please consider that in mind before running our code, As it is working with latest schema.
- we can also check the order status, Order stautus agent working perfectly. run `python -m postgres_da_ai_agent.main --prompt "give the order status of my order with ordeid 1003"`

Please install below libraries in addition to previous one! - Flask~=3.0.3 - flast_cors~=4.0.1 - autogen-agentchat~=0.2

## How to Run

1. clone the repo including this branch
2. use python 3.10 and create venv (virtualenv): `py -3.10 -m pip install virtualenv` and `py -3.10 -m virtualenv venv`
3. install the packages using `pip install -r requirements.txt`
4. create a file in root directory called `.env`
5. put below in the env file

```
	DATABASE_URL=postgresql://<username>:<password>@localhost:5432/<database>
	OPENAI_API_KEY=<your openai api key>
	BASE_DIR=./agent_results

```

6. run using below command - for API response

`python -m postgres_da_ai_agent.api`

- Then use run below api in the Postman

```
POST: /api/start_chat
	- http://127.0.0.1:5008/api/start_chat
	- Handles the initial chat to invoke our agent
	- start chat commands
```

{
"message": "recommend any product of color Pink"
// "message": "recommend a product from brand Parx for gender Men"
// "message": ""
}

```
GET: /api/get_message
	- http://127.0.0.1:5008/api/get_message
	- Getting the response from agents to the ui
```

- Note here there will be no json body input

```
POST: /api/send_message
	- http://127.0.0.1:5008/api/send_message
    - Get the inputs from the user
```

{
// "message": "'Jane', 'Moore', 'jane.moore@outlook.com', '140096131', '573 Lakeview Dr', '7287801875695022', 3"
// "message": "I want to buy this product"
"message": "I want to buy the first product you recommended"
// "message": "thank you"
}

6. run using below command - For command line output

   `python -m postgres_da_ai_agent.main --prompt "give me a product Pink colored shorts for Men"`

## Next steps

1. Chat has to terminate with proper termination condition which is not there
2. get_message api response is not proper.
3. Agent ask for 7 details like first name, address etc.. are asked in one prompts so user have to give details in one chat only. that has to be improved
4. agent match the exact keyword in database like for pink item i always to give prompt word "Pink" with P capitalize as it is exactly same in the database
