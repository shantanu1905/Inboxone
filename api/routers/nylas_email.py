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
import os 
import requests
from .nylas_datatype import *
# Retrieve environment variables
API_URI = os.environ.get("API_URI")
REDIRECT_CLIENT_URI = 'https://api.us.nylas.com/connect/callback'

# Create an instance of the Logger class
logger_instance = Logger()
# Get a logger for your module
logger = logger_instance.get_logger("stock market api")
router = APIRouter(
    tags=["Nylas_Email"],)


@router.post("/api/nylas/messages")
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
        grant_ids = get_email.grant_id
        if not grant_ids:
            raise HTTPException(status_code=400, detail="Grant ID not found")
        
        extracted_messages = []
        # Iterate over each grant ID
        for grant_id in grant_ids:
            url = f"https://api.us.nylas.com/v3/grants/{grant_id}/messages?limit={get_email.limit}"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {db_user.api_key}',
                'Content-Type': 'application/json',
            }

            response = requests.get(url, headers=headers)


            # Convert the response content to JSON
            response_data = response.json()



            for message in response_data['data']:
                extracted_data = {
                    "starred":message.get('starred'),
                    "unread": message.get('unread'),
                    "folders": message.get('folders'),
                    "subject": message.get("subject"),
                    "thread_id": message.get("thread_id"),
                    # "body": message.get("body"),
                    "grant_id": message.get("grant_id"),
                    "id":message.get("id"),
                    "snippet": message.get("snippet"),
                    #"bcc": message.get("bcc", []),  # Assuming bcc and cc may be missing
                    #"cc": message.get("cc", []),
                    #"attachments": message.get("attachments", []),
                    "from": message.get("from"),
                    "to": message.get("to"),
                    #"reply_to": message.get("reply_to", [])
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
    


@router.post("/api/nylas/delete_messages")
async def delete_messages(
    del_email :_schemas.DeleteEmails,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),  # Fetch the current user
    db: _orm.Session =_fastapi.Depends(_database.get_db)  # Dependency for database session
):
    try:
        # Fetch the current user's API key and grant ID from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise HTTPException(status_code=401, detail="API key not found for the current user")
        
        # Retrieve the grant ID from environment variable or database
        grant_id = del_email.grant_id
        if not grant_id:
            raise HTTPException(status_code=400, detail="Grant ID not found")
        
        # Retrieve the message ID from environment variable or database
        id = del_email.id
        if not id:
            raise HTTPException(status_code=400, detail="thread_id  not found")
        
        nylas = get_nylas_client(db_user.api_key)
        
        response = nylas.messages.destroy(grant_id,id)


        return {"status":"success", "message":"Email deleted successfully" , "data":response}

    
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not delete messages, please check thread_id or message_id")
    

@router.post("/api/nylas/read_messages")
# NEEDTO UPDATE SCHEMA WORKING FOR SINGLE GRANT ID WE HAVE TO TAKES LIST OF GRANT ID
async def list_messages(
    read_email :_schemas.ReadEmails,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),  # Fetch the current user
    db: _orm.Session =_fastapi.Depends(_database.get_db)  # Dependency for database session
):
    try:
        # Fetch the current user's API key and grant ID from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise HTTPException(status_code=401, detail="API key not found for the current user")
        
        # Retrieve the grant ID from environment variable or database
        grant_ids = read_email.grant_id
        if not grant_ids:
            raise HTTPException(status_code=400, detail="Grant ID not found")
        
        # Retrieve the message ID from environment variable or database
        id = read_email.id
        if not id:
            raise HTTPException(status_code=400, detail="thread_id ID not found")
        
        
        extracted_messages = []
   
        url = f"https://api.us.nylas.com/v3/grants/{grant_ids}/messages/{id}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {db_user.api_key}',
            'Content-Type': 'application/json',
        }

        response = requests.get(url, headers=headers)


        # Convert the response content to JSON
        response_data = response.json()



        # Return the response as a dictionary
        return JSONResponse(
            content={
                "status": "success",
                "message": "Messages retrieved successfully",
                "data": response_data                   # work in progress...........................
            },
            status_code=200
        ) 
    
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve messages")
    



    
@router.post("/api/nylas/send_messages")
# NEEDTO UPDATE SCHEMA WORKING FOR SINGLE GRANT ID WE HAVE TO TAKES LIST OF GRANT ID
async def send_messages(
    send_email :_schemas.SendEmails,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),  # Fetch the current user
    db: _orm.Session =_fastapi.Depends(_database.get_db)  # Dependency for database session
):
    """
    {
    "grant_id": "dacccswce2425534535"
  "subject": "From Nylas",
  "to": [
    {
      "email": "dorothy@example.com",
      "name": "Dorothy Vaughan"
    }
  ],
  "cc": [
    {
      "email": "George Washington Carver",
      "name": "carver@example.com"
    }
  ],
  "bcc": [
    {
      "email": "Albert Einstein",
      "name": "al@example.com"
    }
  ],
  "reply_to": [
    {
      "email": "skwolek@example.com",
      "name": "Stephanie Kwolek"
    }
  ],
  "body": "This email was sent using the Nylas email API. Visit https://nylas.com for details.",
} 
    
    """
    try:
        # Fetch the current user's API key and grant ID from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise HTTPException(status_code=401, detail="API key not found for the current user")
        
         # Retrieve the grant ID from environment variable or database
        grant_id = send_email.grant_id
        if not grant_id:
            raise HTTPException(status_code=400, detail="Grant ID not found")
        

        nylas = get_nylas_client(db_user.api_key)

        draft = nylas.drafts.create(
            grant_id,
            request_body={
            "to": send_email.to,
            "cc": send_email.cc,
            "bcc": send_email.bcc,
            "reply_to":send_email.reply_to ,
            "subject": send_email.subject ,
            "body": send_email.body,
            }
        )

        draftSent = nylas.drafts.send(
            grant_id,
            draft[0].id,
            )
    
        # Return the response as a dictionary
        return JSONResponse(
            content={
                "status": "success",
                "message": "Messages Send successfully",
                "data": None
            },
            status_code=200
        )
    
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not Send messages")
    


