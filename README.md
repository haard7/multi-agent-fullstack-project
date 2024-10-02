## Branch: `feature/1-recommend-purchase-product`

### Description

- In this branch currently the development of product recommendation agent is going
- it should be able to write the data into the database if user wants to purchase the recommended product

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

## Next steps

1. should be able to get the context from previous chat because after the product being recommended the user might want to purchase that.
2. Also, create the table where the credit card info of the user including the product id should be saved into the database

   ....
