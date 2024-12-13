# EmailSubmission

This Flask-based microservice application processes emails sent to a designated Gmail account and categorizes them based on issues such as damaged packages, defective products, or fraudulent transactions. Using the Gmail API, it reads incoming email data, extracts order IDs and image URLs, and stores this information in PostgreSQL tables for further review and processing.

## Technologies Used

- Python 3
- Flask: Web framework
- Google Gmail API: For retrieving emails
- PostgreSQL: Database for storing reports
- OAuth 2.0: For Gmail API authentication

## Prerequisites

- Python 3.7 or higher
- PostgreSQL database
- Google Cloud project with Gmail API enabled
- A Google account with credentials to access Gmail API

## Setup and Installation

- Clone the Repository:
  `git clone https://github.com/yourusername/issue-reporting-service.git`

- Install Dependencies:
  `pip install -r requirements.txt`

- Set Up Gmail API:

  1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials/)
  2. Enable the Gmail API.
  3. Create OAuth 2.0 credentials and download the credentials.json file.
  4. In the Authorized redirect uri specify `http://localhost:5001/`.
  5. While creating your OAuth consent screen, under scopes please add `https://www.googleapis.com/auth/gmail.modify`.
  6. Move credentials.json to the root directory of the project and add it to .gitignore for security.

- Configure Environment Variables:

  - Create a .env file in the root directory and add the following variables:
    ```
      DB_NAME=your_db_name
      DB_USER=your_db_user
      DB_PASSWORD=your_db_password
      DB_HOST=localhost
      DB_PORT=5432
    ```

- Make sure to run `ClothShop.sql` in your postgres.

- Run the application with `python3 app.py`.
