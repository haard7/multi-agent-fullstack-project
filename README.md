## Branch: `feature/1-recommend-purchase-product`

### Description

- Now, successfully able to save the customer and order data
- you can run either main.py.
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

   `python -m postgres_da_ai_agent.main --prompt "give me a product Pink colored shorts for Men"`


## Next steps

1. Chat has to terminate with proper termination condition which is not there
2. Agent ask for 7 details like first name, address etc.. are asked in one prompts so user have to give details in one chat only. that has to be improved
3. agent match the exact keyword in database like for pink item i always to give prompt word "Pink" with P capitalize as it is exactly same in the database
