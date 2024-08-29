from fastapi import APIRouter ,  HTTPException  
import fastapi as _fastapi
from fastapi.responses import JSONResponse
import schemas as _schemas
import models as _models
import sqlalchemy.orm as _orm
import auth_services as _services
import database as _database
from logger import Logger
from typing import List
from logger import Logger
import os 
from .nylas_datatype import *
from generative_ai import improve_email , generate_email_reply , CalendarEventSQLRAGChain
from dotenv import load_dotenv
import json
import requests
from datetime import datetime
from database import DATABASE_URL
import pytz  # You'll need to install the pytz library for timezone handling

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
    

@router.get("/api/nylas/sync_calendar_events")
        
def sync_calendar_events(db: _orm.Session =_fastapi.Depends(_database.get_db) ,
                               user: _schemas.User = _fastapi.Depends(_services.get_current_user)):
    """
    Fetches event data from the Nylas API for multiple grants and emails, extracts specific fields,
    and saves the data to the database. Deletes old entries from the database if their start_time and
    end_time are in the past.

    Args:
    - grants_data (list): A list of dictionaries with 'id' and 'grant_id' for grants.
    - api_key (str): The API key for authorization.
    - db (Session): The SQLAlchemy database session.
    - user_id (int): The ID of the user to whom the calendar data belongs.

    Returns:
    - list: A list of dictionaries containing the extracted event data for each grant and email.
    """
    def convert_unix_to_datetime(timestamp, timezone_str):
        tz = pytz.timezone(timezone_str)
        return datetime.fromtimestamp(timestamp, tz)
    
    try:
        # Fetch the current user's API key from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise HTTPException(status_code=401, detail="API key not found for the current user")

                
        # Perform the join between Calendar and Grant tables
        result = (
                    db.query(_models.Calendar.id, _models.Grant.email, _models.Calendar.grant_id)
                    .join(_models.Grant, _models.Calendar.grant_id == _models.Grant.id)
                    .filter(_models.Calendar.user_id == user.id)
                    .all()
                )
        

        # Extract the required data from the grants
        calendar_data = [
            {
                "id":calendar_id,
                "grant_id": grant_id,
                "email":grant_email
            }
            for calendar_id,grant_email, grant_id  in result
        ]

        # Next part of code execution started
        
        all_extracted_data = []

        for events in calendar_data:
            grant_id = events.get("grant_id")
            calendar_id = events.get("id")
            
            if not grant_id or not calendar_id:
                continue  # Skip if either grant_id or calendar_id is missing
            
            # Construct the API URL
            url = f"https://api.us.nylas.com/v3/grants/{grant_id}/events?calendar_id={calendar_id}"

            # Set up the headers for the API request
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {db_user.api_key}',
                'Content-Type': 'application/json',
            }

            # Make the GET request to the API
            response = requests.get(url, headers=headers)

            # Check if the request was successful
            if response.status_code != 200:
                print(f"Failed to retrieve events for grant ID {grant_id} and calendar ID {calendar_id}")
                continue

            # Parse the JSON response
            data = response.json()

            # Extract the desired fields
            for event in data.get("data", []):
                when_data = event.get("when", {})
                start_time = when_data.get("start_time")
                end_time = when_data.get("end_time")
                start_timezone = when_data.get("start_timezone", "UTC")
                end_timezone = when_data.get("end_timezone", "UTC")

                creator_data = event.get("creator", {})
                creator_name = creator_data.get("name", "N/A")
                creator_email = creator_data.get("email", "N/A")

                conferencing_data = event.get("conferencing", {})
                conferencing_provider = conferencing_data.get("provider", "N/A")
                conferencing_details = conferencing_data.get("details", {})
                meeting_code = conferencing_details.get("meeting_code", "N/A")
                conferencing_url = conferencing_details.get("url", "N/A")

                organizer_data = event.get("organizer", {})
                organizer_name = organizer_data.get("name", "N/A")
                organizer_email = organizer_data.get("email", "N/A")

                start_time_readable = convert_unix_to_datetime(start_time, start_timezone) if start_time else None
                end_time_readable = convert_unix_to_datetime(end_time, end_timezone) if end_time else None

                extracted_info = {
                    "busy": event.get("busy"),
                    "calendar_id": event.get("calendar_id"),
                    "conferencing_provider": conferencing_provider,
                    "conferencing_meeting_code": meeting_code,
                    "conferencing_url": conferencing_url,
                    "organizer_name": organizer_name,
                    "organizer_email": organizer_email,
                    "title": event.get("title"),
                    "creator_name": creator_name,
                    "creator_email": creator_email,
                    "id": event.get("id"),
                    "object": event.get("object"),
                    "start_time": start_time_readable,
                    "end_time": end_time_readable,
                    "created_at": datetime.fromtimestamp(event.get("created_at"), tz=pytz.utc) if event.get("created_at") else None,
                    "updated_at": datetime.fromtimestamp(event.get("updated_at"), tz=pytz.utc) if event.get("updated_at") else None,
                    "user_id": db_user.id,  # Associate the event with the user
                }
                all_extracted_data.append(extracted_info)

                # Check if the event already exists in the database
                db_event = db.query(_models.CalendarData).filter(_models.CalendarData.id == extracted_info["id"]).first()
                
                if db_event:
                    # Update existing record
                    for key, value in extracted_info.items():
                        setattr(db_event, key, value)
                    db.commit()
                else:
                    # Insert new record
                    db_event = _models.CalendarData(**extracted_info)
                    db.add(db_event)
                    db.commit()

        # After fetching and inserting events, delete old events
        current_time = datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
        db.query(_models.CalendarData).filter(
            _models.CalendarData.user_id == db_user.id,
            (_models.CalendarData.start_time < current_time) & (_models.CalendarData.end_time < current_time)
        ).delete(synchronize_session=False)
        db.commit()

        return {
                "status": "success",
                "message": "Calendar events sync successfully",
                "data": all_extracted_data
            },
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="sync failed !")
    

@router.post("/api/calendar_chatbot")
def calendar_chatbot(
    prompt : _schemas.CalendarChat , 
    db: _orm.Session = _fastapi.Depends(_database.get_db),
    user: _schemas.User = _fastapi.Depends(_services.get_current_user)
):
    try:
        # Fetch the current user's API key from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise _fastapi.HTTPException(status_code=401, detail="API key not found for the current user")
    
        sql_rag_chain = CalendarEventSQLRAGChain(google_api_key=gemini_api_key , user_id=db_user.id)
    
        answer = sql_rag_chain.retrieve_answer(prompt.user_prompt)

        # Debugging information
        print(f"Retrieved Answer: {answer}")

        return {
                "status": "success",
                "message": "response generated successfully",
                "data": answer
            }
        

    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise _fastapi.HTTPException(status_code=500, detail="Failed to provide response, ask a different question")
    


