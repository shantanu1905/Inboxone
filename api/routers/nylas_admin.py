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

# Retrieve environment variables
API_URI = os.environ.get("API_URI")
REDIRECT_CLIENT_URI = 'https://api.us.nylas.com/connect/callback'

# Create an instance of the Logger class
logger_instance = Logger()
# Get a logger for your module
logger = logger_instance.get_logger("stock market api")
router = APIRouter(
    tags=["Nylas_admin"],)



def get_nylas_client(api_key: str) -> Client:
    """Create and return a Nylas client with the given API key."""
    try:
        return Client(
            api_key=api_key,
            api_uri=API_URI
        )
    except Exception as e:
        logger.error(f"Error creating Nylas client: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create Nylas client.")


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
import json
@router.get("/api/nylas/grants")
async def list_grants(
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),  # Fetch the current user
    db: _orm.Session = _fastapi.Depends(_database.get_db)  # Dependency for database session

):
    try:
        # Fetch the current user's API key from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise HTTPException(status_code=401, detail="API key not found for the current user")

        # Initialize Nylas client with the user's API key
        nylas = get_nylas_client(db_user.api_key)
    
        grantss = nylas.grants.list()
        list_response = ListResponse(grants=grantss)

        content={
                    "status": "success",
                    "message": "Grants retrieved successfully",
                    "data": list_response
                }
        
        return content
    
    except Exception as e:
        # Log the error
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve grants")
    

# Delete grants api route 

# update grantsapi routes 




@router.get("/api/nylas/generate-auth-url")
async def build_auth_url(
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_database.get_db)
):
    try:
        # Fetch the current user's API key from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise HTTPException(status_code=401, detail="API key not found for the current user")
        

        nylas = get_nylas_client(db_user.api_key)
        auth_url = nylas.auth.url_for_oauth2(
            config={
                "client_id":db_user.api_key,
                "provider": 'google',
                "redirect_uri": REDIRECT_CLIENT_URI,
                "login_hint": "shantanunimkar19@gmai.com"
            }
        )
        return RedirectResponse(url=auth_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate auth URL: {str(e)}")