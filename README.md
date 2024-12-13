## Project Domain: Retail Industry (Clothing)

# Description

This project is a Flask-based chat application using multiple agents to interact with users, particularly designed for handling customer service requests related to product conditions and transactions. This project was developed in academic setting as a part of the coursework of CSP-584: Enterprise Web Application. The project leverages the `autogen` library to create, manage, and orchestrate different agents that work together to provide detailed assistance to users. Below is a summary of each agent and their roles. Below are the major functionalitie of the project:

1. Let User ask for the product recommendation based on various criteria and interest, chatbot will respond with product recommendations

2. Let user ask for order status against order id, also give the status of defective product and damaged package by analyzing the submitted image

3. Let user upload the image of bill for fraud detection, chatbot will analyze the OCR and give the decision based on the order id and billed price.

# Demo

## [Phase-1](https://youtu.be/5gD1kuKxsYE)

## [Phase-2](https://youtu.be/kMJhXsEgpmg)

## Overview

# Main Components

- **Flask Backend**: Serves as the interface to handle HTTP requests, manage chat sessions, and provide interactions between the agents and users.
- **Queue System**: Utilized for message handling between the system, user, and agents.
- **AutoGen Agents**: Multiple agents are defined using `autogen` to solve different user queries and provide a collaborative experience.
- **User Interface**: The user interacts with the chat agents through a UI built using `React`.
- **Database Integration**: PostgreSQL is used to store and retrieve product and order information for processing user requests. It is important to note that here we have not created any embeddings or any Vectorization of the data, agent is generating the SQL queries for read operation and for write we are having custom functions executing the sql.

## Setup and Running

# Setup Instructions

To set up and run the project, follow these steps:

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables by creating a `.env` file with:

   ```
   DATABASE_URL=<Your_Postgres_DB_URL>
   OPENAI_API_KEY=<Your_OpenAI_API_Key>
   ```

3. Run the Flask server:

   ```bash
   python api2.py
   ```

   or

   ```bash
   python -m api1.py
   ```

4. Access the APIs through the provided endpoints to start, send, or get messages.

## Agents Workflow

# Workflow Overview

- We are using GroupChat manager which manages the chat between different agents. I have also included the userproxy agent with its own responsibilities in managing the workflow.

## Technologies Used

# Technology Stack

- **Flask**: For creating the backend REST API service.
- **AutoGen Library**: To create and manage intelligent agents.
- **PostgreSQL**: Database management for product and order information.
- **OpenAI API**: Leveraged for natural language understanding and processing capabilities.

## Future Enhancements

# Planned Enhancements

- Improve error handling and stability for edge cases.
- Add a user interface for interacting with the chat agents.
- IMP: Currently there are two separate files for separate bunch of agents. It is still left to integrate all the agents into single backend which is expected functionality.

Feel free to clone, modify, and use the code for building intelligent conversational applications! If you encounter any issues, please open an issue on the repository.

Please install below libraries in addition to below mentioned !

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

`python -m agents.api2`
