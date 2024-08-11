from fastapi import APIRouter ,  HTTPException  , status
import fastapi as _fastapi
from fastapi.responses import JSONResponse , RedirectResponse
import schemas as _schemas
import models as _models
import sqlalchemy.orm as _orm
import auth_services as _services
import database as _database
from logger import Logger
from typing import List
from nylas import Client
from .nylas_datatype import Grant , ListResponse
import os 
import requests
# Retrieve environment variables
API_URI = os.environ.get("API_URI")
REDIRECT_CLIENT_URI = 'https://api.us.nylas.com/connect/callback'

# Create an instance of the Logger class
logger_instance = Logger()
# Get a logger for your module
logger = logger_instance.get_logger("stock market api")
router = APIRouter(
    tags=["Nylas_Email"],)




def check_nylas_api_key(api_key: str):
    """validates nylas api key"""
    try:
        nylas = Client(
            api_key=api_key,
            api_uri=API_URI
        )

        application = nylas.applications.info()
        application_id = application[1]
        return application_id
    except Exception   as e:
        raise HTTPException(status_code=400, detail="Could not verify access credential.")


@router.get("/api/nylas/messages")
# NEEDTO UPDATE SCHEMA WORKING FOR SINGLE GRANT ID WE HAVE TO TAKES LIST OF GRANT ID
async def list_messages(
    get_email :_schemas.GetEmails,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),  # Fetch the current user
    db: _orm.Session =_fastapi.Depends(_database.get_db)  # Dependency for database session
):
    try:
        # Fetch the current user's API key and grant ID from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise HTTPException(status_code=401, detail="API key not found for the current user")
        
        # Retrieve the grant ID from environment variable or database
        grant_id = get_email.grant_id
        if not grant_id:
            raise HTTPException(status_code=400, detail="Grant ID not found")

        
        
        url = f"https://api.us.nylas.com/v3/grants/{grant_id}/messages?limit={get_email.limit}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {db_user.api_key}',
            'Content-Type': 'application/json',
        }

        response = requests.get(url, headers=headers)

       # Convert the response content to JSON
        response_data = response.json()

        extracted_messages = []

        for message in response_data['data']:
            extracted_data = {
                "unread": message.get('unread'),
                "subject": message.get("subject"),
                "thread_id": message.get("thread_id"),
                # "body": message.get("body"),
                "grant_id": message.get("grant_id"),
                "snippet": message.get("snippet"),
                "bcc": message.get("bcc", []),  # Assuming bcc and cc may be missing
                "cc": message.get("cc", []),
                "attachments": message.get("attachments", []),
                "from": message.get("from"),
                "to": message.get("to"),
                "reply_to": message.get("reply_to", [])
            }
            extracted_messages.append(extracted_data)

        # Return the response as a dictionary
        return JSONResponse(
            content={
                "status": "success",
                "message": "Messages retrieved successfully",
                "data": extracted_messages
            },
            status_code=200
        )
    
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve messages")