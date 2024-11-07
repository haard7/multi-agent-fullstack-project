## Branch: `feature/shipping-status-agent`

### Description

- I am able to put the image url via UI and get the decision of the shipping status by analyzing that image (No DB involved)
- For phase-2 I am using `api2.py` file to run, as integrating with previous code was having some issue.
- Run `python -m agents.api2`

Please install below libraries in addition to previous one!

- Flask~=3.0.3
- flast_cors~=4.0.1
- autogen-agentchat~=0.2

## Conversation flow on UI

1. what is the stutatus of my damaged package
   ..
2. `<img https://i.postimg.cc/wMqvrqPy/dam1.png>`

3. what is the decision of this package

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

`python -m agents.api`

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

   `python -m agents.api2 --prompt "give me a product Pink colored shorts for Men"`

## Next steps

- integrate the fraud detection agent
