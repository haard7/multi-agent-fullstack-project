## Brach: `postgres_da_multi_agent`

### Description

- This branch contains the example of multi agent framework using autogen and openai api
- It contains three agents Data Engineer, Sr. Data Analyst and Product manager. above these three we have user-proxy agent which get the user input and send the request to these agents in sequence, for writting sql query send to data engineer agent, for reviewing the query send to sr. data analyst agent and finally for validation send to product manager agent
- Note: This is just for example and learning that how any agent can interact with the database but actually we will have different architecture and agents for our use case
- Here we are using the postgresql database. For ease I have used the clothShop database which is more aligning with our usecase.
  - Basically this will get the input from user in simple language like "get all the products for gender male and color black" and respond back the json with required output.

## How to Run

1. clone the repo including this branch
2. use python 3.10 and create venv (virtualenv)
3. install the packages using `pip install -r requirements.txt`
4. create a file in root directory called `.env`
5. put below in the env file

```
	DATABASE_URL=postgresql://<username>:<password>@localhost:5432/<database>
	OPENAI_API_KEY=<your openai api key>
	BASE_DIR=./agent_results

```

6. run using below command
   `python -m postgres_da_ai_agent.main --prompt "get all the products for gender Men"`

### Note ⚠️ (Important!):Here this project is using GPT-4 model which is very expensive.

## Next steps

1. make the code works for `gpt-4o-mini` or `gpt-3.5-turbo`
2. change the agents to the actual agents like product recommendation, order status etc..
3. modify the agentic workflow to enable user-proxy agent to decide which agent to give the task for output
   ....
