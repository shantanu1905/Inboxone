from fastapi import APIRouter ,  HTTPException 
import fastapi as _fastapi
import schemas as _schemas
import models as _models
import sqlalchemy.orm as _orm
import auth_services as _services
import database as _database
from logger import Logger
import os 
import requests
from .nylas_datatype import *
from datetime import datetime
import pytz
# Retrieve environment variables
API_URI = os.environ.get("API_URI")
REDIRECT_CLIENT_URI = 'https://api.us.nylas.com/connect/callback'

# Create an instance of the Logger class
logger_instance = Logger()
# Get a logger for your module
logger = logger_instance.get_logger("stock market api")
router = APIRouter(
    tags=["Nylas_calendar"],)



@router.get("/api/nylas/get_calendar_events")
def get_calendar_events(db: _orm.Session = _fastapi.Depends(_database.get_db),
                        user: _schemas.User = _fastapi.Depends(_services.get_current_user)):
    """
    Fetches event data from the Nylas API for multiple grants and emails, extracts specific fields,
    
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
                "id": calendar_id,
                "grant_id": grant_id,
                "email": grant_email
            }
            for calendar_id, grant_email, grant_id in result
        ]

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

                attendees_data = event.get("attendees", [])
                attendees = [{"name": att.get("name", "N/A"), "email": att.get("email", "N/A"), "status": att.get("status", "N/A")} for att in attendees_data]

                # Extract participants
                participants_data = event.get("participants", [])
                participants = [{"email": part.get("email", "N/A"), "status": part.get("status", "N/A")} for part in participants_data]

                reminders_data = event.get("reminders", {})
                use_default_reminder = reminders_data.get("use_default", True)
                reminder_overrides = reminders_data.get("overrides", [])

                start_time_readable = convert_unix_to_datetime(start_time, start_timezone) if start_time else None
                end_time_readable = convert_unix_to_datetime(end_time, end_timezone) if end_time else None

                extracted_info = {
                    "id": event.get("id"),
                    "object": event.get("object"),
                    "status": event.get("status", "N/A"),
                    "calendar_id": event.get("calendar_id"),
                    "grant_id": grant_id,
                    "title": event.get("title"),
                    "creator_name": creator_name,
                    "creator_email": creator_email,
                    "organizer_name": organizer_name,
                    "organizer_email": organizer_email,
                    "attendees": attendees,
                    "participants": participants,
                    "conferencing_provider": conferencing_provider,
                    "conferencing_meeting_code": meeting_code,
                    "conferencing_url": conferencing_url,
                    "start_time": start_time_readable,
                    "end_time": end_time_readable,
                    "start_timezone": start_timezone,
                    "end_timezone": end_timezone,
                    "reminders": {
                        "use_default": use_default_reminder,
                        "overrides": reminder_overrides
                    },
                    "html_link": event.get("html_link", "N/A"),
                    "visibility": event.get("visibility", "N/A"),
                    "created_at": datetime.fromtimestamp(event.get("created_at"), tz=pytz.utc) if event.get("created_at") else None,
                    "updated_at": datetime.fromtimestamp(event.get("updated_at"), tz=pytz.utc) if event.get("updated_at") else None,
                    "user_id": db_user.id,  # Associate the event with the user
                }
                all_extracted_data.append(extracted_info)

        return {
            "status": "success",
            "message": "Calendar events retrieved successfully",
            "data": all_extracted_data
        }
    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve calendar events")
