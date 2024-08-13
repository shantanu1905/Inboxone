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
from generative_ai import improve_email , generate_email_reply
from dotenv import load_dotenv
import json


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
    get_email :_schemas.GenerateEmails
):
    """
    This endpoint is used to fix grammar and structure email
    
    """
    try:
        response = improve_email(get_email.email_content , gemini_api_key)
        # Return the response as a dictionary
        return JSONResponse(
            content={
                "status": "success",
                "message": "Email Generated successfully",
                "data": response
            },
            status_code=200
        )
    
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not Generate email")
    



    
@router.post("/api/nylas/autoreply_messages")
# NEEDTO UPDATE SCHEMA WORKING FOR SINGLE GRANT ID WE HAVE TO TAKES LIST OF GRANT ID
async def send_autorelpy_messages(
    autoreply_email :_schemas.AutoReply,
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
        grant_id = autoreply_email.grant_id
        if not grant_id:
            raise HTTPException(status_code=400, detail="Grant ID not found")
        
        auto_reply = generate_email_reply(autoreply_email.body , gemini_api_key)
        data = json.loads(auto_reply)
      
      
        nylas = get_nylas_client(db_user.api_key)

        draft = nylas.drafts.create(
            grant_id,
            request_body={
            "to": autoreply_email.to,
            "cc": autoreply_email.cc,
            "bcc": autoreply_email.bcc,
            "reply_to":autoreply_email.reply_to ,
            "subject": data['subject'] ,
            "body": data['body'],
            "thread_id":autoreply_email.thread_id
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
                "message": "Auto reply send successfully",
                "data": None
            },
            status_code=200
        )
    
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not send autoreply messages")
    


