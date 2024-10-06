## Branch: `feature/1-recommend-purchase-product`

### Description

- In this branch currently the development of product recommendation agent is going
- it should be able to write the data into the database if user wants to purchase the recommended product
- you can run either main-copy.py or main.py. I am currently modifying main-copy.py for some results.
- First create the database using "ClothShop.sql" file in PostgreSQL. I have updated the schema in the next queries so please consider that in mind before running our code, As it is working with latest schema.
- Order stautus agent working perfectly. run `python -m postgres_da_ai_agent.main --prompt "give the order status of my order with ordeid 1003"`

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

   or

   `python -m postgres_da_ai_agent.main-copy --prompt "get all the products for gender Men"`

   I have main-copy.py file to playaround which should not affect minimum viable execution I have in main.py
   currently main-copy.py have improved code which is executable - 6:31 PM 10/06/2024

## Next steps

1. Sequential chat after getting recommendation from product recommend agent break, so we need to create proper workflow which can talk to user seamlessly until user not checkout

   ....
