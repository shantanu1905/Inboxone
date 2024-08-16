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
from logger import Logger
import os 
from .nylas_datatype import *
from generative_ai import improve_email , generate_email_reply, fetch_events_from_calendar
from dotenv import load_dotenv
import json
import requests

load_dotenv()



# Retrieve environment variables
API_URI = os.environ.get("API_URI")
gemini_api_key = os.environ.get("GEMINI_API_KEYY")


REDIRECT_CLIENT_URI = 'https://api.us.nylas.com/connect/callback'

# Create an instance of the Logger class
logger_instance = Logger()
# Get a logger for your module
logger = logger_instance.get_logger("stock market api")
router = APIRouter(
    tags=["Generative AI"],)


@router.post("/api/ai/generate_email")
async def generate_messages(
    get_email :_schemas.GenerateEmails,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),  # Fetch the current user
    db: _orm.Session =_fastapi.Depends(_database.get_db)  # Dependency for database session
):
    """
    This endpoint is used to fix grammar and structure email
    
    """
    try:
        # Fetch the current user's API key and grant ID from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.name:
            raise HTTPException(status_code=401, detail="UserName - Not Found")
        
        response = improve_email(get_email.email_content , gemini_api_key, db_user.name)

        response_data = json.loads(response)
        # Return the response as a dictionary
        return JSONResponse(
            content={
                "status": "success",
                "message": "Email Generated successfully",
                "data": response_data
            },
            status_code=200
        )
    
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not Generate email")
    
    
@router.post("/api/nylas/generate_autorelpy_messages")
# NEEDTO UPDATE SCHEMA WORKING FOR SINGLE GRANT ID WE HAVE TO TAKES LIST OF GRANT ID
async def generate_autorelpy_messages(
    generate_autoreply_email :_schemas.GenerateAutoReply,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),  # Fetch the current user
    db: _orm.Session =_fastapi.Depends(_database.get_db)  # Dependency for database session
):
    """
    This endpoint generates email for message(thread)
  
    """
    try:
        # Fetch the current user's API key and grant ID from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.name:
            raise HTTPException(status_code=401, detail="API key not found for the current user")
        
        # Retrieve the grant ID from environment variable or database
        grant_id = generate_autoreply_email.grant_id
        if not grant_id:
            raise HTTPException(status_code=400, detail="Grant ID not found")
        
        # Retrieve the grant ID from environment variable or database
        thread_id = generate_autoreply_email.thread_id
        if not thread_id:
            raise HTTPException(status_code=400, detail="Thread ID not found")
        

        url = f"https://api.us.nylas.com/v3/grants/{grant_id}/threads/{thread_id}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {db_user.api_key}',
            'Content-Type': 'application/json',
        }

        response = requests.get(url, headers=headers)
        responsedata = response.json()

        # extracting required data from json response 
        email_html_body = responsedata['data']["latest_draft_or_message"]["body"]

        email_subject = responsedata['data']["latest_draft_or_message"]['subject']
        email_reply_to = responsedata['data']["latest_draft_or_message"]['reply_to']
        email_to = responsedata['data']["latest_draft_or_message"]['to']
        email_thread_id = responsedata['data']["latest_draft_or_message"]['thread_id']
        email_grant_id = responsedata['data']["latest_draft_or_message"]['grant_id']
        email_msg_id = responsedata['data']["latest_draft_or_message"]['id']




        #Generating email reply for thread message
        email_reply = generate_email_reply(email_html_body ,gemini_api_key ,db_user.name, generate_autoreply_email.user_prompt)
        email_response_data = json.loads(email_reply)

        final_resposne = {
            "subject": email_response_data['subject'],
            "body": email_response_data['body'],
            "reply_to" : email_reply_to,
            "to": email_to,
            "thread_id": email_thread_id,
            "grant_id":email_grant_id,
            "id":email_msg_id

        }
        
       
        # Return the response as a dictionary
        return JSONResponse(
            content={
                "status": "success",
                "message": "Reply Generated Successfully",
                "data": final_resposne
            },
            status_code=200
        )
    
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not send autoreply messages")
    


  
    
@router.post("/api/nylas/calendar_chat")
# NEEDTO UPDATE SCHEMA WORKING FOR SINGLE GRANT ID WE HAVE TO TAKES LIST OF GRANT ID
async def chat_with_calendar(
    chat :_schemas.CalendarChat,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),  # Fetch the current user
    db: _orm.Session =_fastapi.Depends(_database.get_db)  # Dependency for database session
):
    """
    This endpoint generates email for message(thread)
  
    """
    try:
         # Fetch the current user's API key and grant IDs from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise HTTPException(status_code=401, detail="API key not found for the current user")

        # Fetch the current user's grants from the database
        grants = db.query(_models.Grant).filter(_models.Grant.user_id == user.id).all()
        
        if not grants:
            raise HTTPException(status_code=404, detail="No grants found for the current user")
        

        # Extract the required data from the grants
        grants_data = [
            {
                "id": grant.id,
                "email": grant.email
            }
            for grant in grants
        ]

        dat = fetch_events_from_calendar(grants_data ,db_user.api_key)
        print(dat)

        # Return the response as a dictionary
        return JSONResponse(
            content={
                "status": "success",
                "message": "Reply Generated Successfully",
                "data": dat
            },
            status_code=200
        )
    
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not send autoreply messages")
    


