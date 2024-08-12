from fastapi import APIRouter ,  HTTPException
import fastapi as _fastapi
from fastapi.responses import JSONResponse , RedirectResponse
import schemas as _schemas
import models as _models
import sqlalchemy.orm as _orm
import auth_services as _services
import database as _database
from logger import Logger
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
    tags=["Nylas_Admin"],)



@router.get("/api/nylas/grants")
async def list_grants(
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),  # Fetch the current user
    db: _orm.Session =_fastapi.Depends(_database.get_db)  # Dependency for database session
):
    try:
        # Fetch the current user's API key from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise HTTPException(status_code=401, detail="API key not found for the current user")

        # Construct the URL with query parameters
        url = f"https://api.us.nylas.com/v3/grants?limit=5"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {db_user.api_key}',
        }

        # Make the GET request to Nylas API
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to retrieve grants from Nylas API")

        # Parse the response JSON
        response_data = response.json()

        extracted_data = [
                            {
                                "id": item["id"],
                                "grant_status": item["grant_status"],
                                "provider": item["provider"],
                                "email": item["email"],
                                "created_at": item["created_at"],
                                "updated_at": item["updated_at"]
                            }
                            for item in response_data["data"]
                        ]

        # Return the response as a JSONResponse
        return JSONResponse(
            content={
                "status": "success",
                "message": "Grants retrieved successfully",
                "data": extracted_data  # Directly returning the data
            },
            status_code=200
        )

    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve grants")



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
    

@router.post("/api/nylas/delete_grants/{grant_id}")
async def delete_grant(
    grant_id: str,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),  # Fetch the current user
    db: _orm.Session = _fastapi.Depends(_database.get_db)  # Dependency for database session
):
    try:
        # Fetch the current user's API key from the database
        db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
        if not db_user or not db_user.api_key:
            raise HTTPException(status_code=401, detail="API key not found for the current user")
        
        nylas = get_nylas_client(db_user.api_key)
        
        response = nylas.grants.destroy(grant_id)

        return {"status":"success", "message":"grant deleted successfully" , "data":response}


    except Exception as e:
        # Log the error and return a proper HTTP exception
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail={"status":"failed", "message":"Could not delete the grant" , "data":None})


