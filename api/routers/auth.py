from fastapi import APIRouter ,  HTTPException , BackgroundTasks , status
import fastapi as _fastapi
from fastapi.responses import JSONResponse
import schemas as _schemas
import models as _models
import sqlalchemy.orm as _orm
import auth_services as _services
from auth_services import send_otp
from fastapi.security import OAuth2PasswordBearer
import database as _database
from jwt.exceptions import DecodeError
from logger import Logger
from .nylas_admin import check_nylas_api_key
import jwt
import os 
import requests
from datetime import datetime


# Create an instance of the Logger class
logger_instance = Logger()
# Get a logger for your module
logger = logger_instance.get_logger("stock market api")
router = APIRouter(
    tags=["authentication routes"],)


# Retrieve environment variables
JWT_SECRET = os.environ.get("JWT_SECRET")
AUTH_BASE_URL = os.environ.get("AUTH_BASE_URL")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT token validation
async def jwt_validation(token: str = _fastapi.Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except DecodeError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/api/users" )
async def create_user(
    user: _schemas.UserCreate, 
    db: _orm.Session = _fastapi.Depends(_services.get_db)):
    db_user = await _services.get_user_by_email(email=user.email, db=db)

    if db_user:
        logger.info('User with that email already exists')
        response = {
            "is_verified": False,
            "msg":"User with that email already exists"
        }
        
        raise _fastapi.HTTPException(
            status_code=200,
            detail=response)
    

    user = await _services.create_user(user=user, db=db)
    response = {
            "is_verified": False,
            "msg":"User Registered, Please verify email to activate account !"
        }

    return _fastapi.HTTPException(
            status_code=201,
            detail=response)



# Endpoint to check if the API is live
@router.get("/check_api")
async def check_api():
    return {"status": "Connected to API Successfully"}



@router.post("/api/token" )
async def generate_token(
    #form_data: _security.OAuth2PasswordRequestForm = _fastapi.Depends(), 
    user_data: _schemas.GenerateUserToken,
    db: _orm.Session = _fastapi.Depends(_services.get_db)):
    user = await _services.authenticate_user(email=user_data.username, password=user_data.password, db=db)

    if user == "is_verified_false":
        logger.info('Email verification is pending. Please verify your email to proceed. ')
        response = {
            "is_verified": False,
            "msg":"Email verification is pending. Please verify your email to proceed."
        }
        raise _fastapi.HTTPException(
            status_code=403, detail=response)

    if not user:
        logger.info('Invalid Credentials')
        raise _fastapi.HTTPException(
            status_code=401, detail="Invalid Credentials")
    
    logger.info('JWT Token Generated')
    response  = {'detail':await _services.create_token(user=user)}
    return  response


@router.get("/api/users/profile" , response_model=_schemas.User )
async def get_user(
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_database.get_db)
):
    logger.info(f"Fetching profile for user with email {user.email}")

    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "organisation": user.organisation,
        "Api_key":user.api_key,
        "date_created": str(user.date_created),
    }

    logger.info(f"User profile fetched successfully for {user.email}")
    
    return JSONResponse(
        content={
            "status": "success",
            "message": "User profile retrieved successfully",
            "data": user_data
        },
        status_code=status.HTTP_200_OK
    )


@router.post("/api/users/profile" , response_model=_schemas.User )
async def get_user(
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
):
    logger.info(f"Fetching profile for user with email {user.email}")

    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "organisation": user.organisation,
        "Api_key":user.api_key,
        "date_created": str(user.date_created),
    }

    logger.info(f"User profile fetched successfully for {user.email}")
    
    return JSONResponse(
        content={
            "status": "success",
            "message": "User profile retrieved successfully",
            "data": user_data
        },
        status_code=status.HTTP_200_OK
    )


@router.put("/api/users/profile_update", response_model=_schemas.profileUpdate)
async def update_profile(
    user_update: _schemas.profileUpdate,  # Use a schema for update data
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_database.get_db)
):
    
    logger.info(f"Updating profile for user with email {user.email}")

    # Update the user information
    db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    if user_update.name:
        db_user.name = user_update.name
    if user_update.organisation:
        db_user.organisation = user_update.organisation
    if user_update.api_key:
        try:
            verify_key = check_nylas_api_key(user_update.api_key)
            logger.info(f"API key verified with application ID: {verify_key}")
            db_user.api_key = user_update.api_key
        except HTTPException as e:
            logger.error(f"API key verification failed: {e.detail}")
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Invalid API key provided.",
                    "data": None
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    
    db.commit()
    db.refresh(db_user)

    user_data = {
        "id": db_user.id,
        "name": db_user.name,
        "email": db_user.email,
        "organisation": db_user.organisation,
        "Api_key": db_user.api_key,
        "date_created": str(db_user.date_created),
    }

    logger.info(f"User profile updated successfully for {user.email}")
    
    return JSONResponse(
        content={
            "status": "success",
            "message": "User profile updated successfully",
            "data": user_data
        },
        status_code=status.HTTP_200_OK
    )


@router.post("/api/users/generate_otp", response_model=str)
async def send_otp_mail( background_tasks: BackgroundTasks, userdata: _schemas.GenerateOtp, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    user = await _services.get_user_by_email(email=userdata.email, db=db)

    if not user:
        raise _fastapi.HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        response = {
            "is_verified": True,
            "msg":"User is already verified"
        }
        raise _fastapi.HTTPException(status_code=400, detail=response)

    # Generate and send OTP
    otp = _services.generate_otp()
    background_tasks.add_task(send_otp,userdata.email, otp)

    # Store the OTP in the database
    user.otp = otp
    db.add(user)
    db.commit()
    response = {
            "is_verified": False,
            "msg":"OTP send to email"
        }
    return JSONResponse(content=response, status_code=200)


@router.post("/api/users/verify_otp")
async def verify_otp(userdata: _schemas.VerifyOtp, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    user = await _services.get_user_by_email(email=userdata.email, db=db )

    if not user:
        raise _fastapi.HTTPException(status_code=404, detail="User not found")

    if not user.otp or user.otp != userdata.otp:
        response = {
            "is_verified": False,
            "msg":"Invalid OTP"
        }
        raise _fastapi.HTTPException(status_code=400, detail=response)

    # Update user's is_verified field
    user.is_verified = True
    user.otp = None  # Clear the OTP
    db.add(user)
    db.commit()
    response = {
            "detail":{
            "is_verified": True,
            "msg":"Account verified !"
            }
        }

    return JSONResponse(content=response, status_code=200)



@router.get("/api/users/sync_grants")
async def sync_grants(
    
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_database.get_db)
):
    logger.info(f"Grants in sync with Nylas API")

    # Retrieve the user information
    db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch the current user's API key from the database
    if not db_user.api_key:
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

    # Convert Unix timestamps to datetime
    def unix_to_datetime(timestamp):
        return datetime.fromtimestamp(timestamp)

    # Extract data for each grant
    extracted_data = [
        {
            "id": item["id"],
            "grant_status": item["grant_status"],
            "provider": item["provider"],
            "email": item["email"],
            "created_at": unix_to_datetime(item["created_at"]),
            "updated_at": unix_to_datetime(item["updated_at"])
        }
        for item in response_data["data"]
    ]

    # Update or create grants in the database
    for data in extracted_data:
        db_grant = db.query(_models.Grant).filter(_models.Grant.id == data["id"], _models.Grant.user_id == user.id).first()
        
        if db_grant:
            # Update existing grant
            db_grant.grant_status = data["grant_status"]
            db_grant.provider = data["provider"]
            db_grant.email = data["email"]
            db_grant.updated_at = data["updated_at"]
        else:
            # Create a new grant record
            new_grant = _models.Grant(
                id=data["id"],
                grant_status=data["grant_status"],
                provider=data["provider"],
                email=data["email"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                user_id=user.id  # Associate the grant with the current user
            )
            db.add(new_grant)
    
    db.commit()
    logger.info(f"Grants synced successfully for user with email {user.email}")

    return JSONResponse(
        content={
            "status": "success",
            "message": "Grants synced successfully",
            
        },
        status_code=status.HTTP_200_OK
    )


@router.get("/api/users/sync_calendars")
async def sync_calendars(
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_database.get_db)
):
 

    # Retrieve the user information
    db_user = db.query(_models.User).filter(_models.User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch the current user's API key from the database
    if not db_user.api_key:
        raise HTTPException(status_code=401, detail="API key not found for the current user")
    
    # Fetch the current user's grants from the database
    grants = db.query(_models.Grant).filter(_models.Grant.user_id == user.id).all()

    print(grants)
    
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

    extracted_data = []

    # Loop through each grant and sync calendars
    for grant in grants_data:
        grant_id = grant["id"]
        logger.info(f"Syncing calendars for grant ID {grant_id}")

        # Construct the URL with the grant ID
        url = f"https://api.us.nylas.com/v3/grants/{grant_id}/calendars"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {db_user.api_key}',
        }

        # Make the GET request to Nylas API
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to retrieve calendars from Nylas API for grant ID {grant_id}")

        # Parse the response JSON
        response_data = response.json()

        # Extract only the required fields
        filtered_data = [
            {
                "name": item.get("name"),
                "grant_id": grant_id,
                "id": item.get("id"),
                "object": item.get("object"),
                "is_primary": item.get("is_primary"),
                "read_only": item.get("read_only"),
                "is_owned_by_user": item.get("is_owned_by_user")
            }
            for item in response_data["data"]
        ]

        extracted_data.append(filtered_data)

        # Update or create calendars in the database
    for calendar_data in extracted_data:
        for calendar in calendar_data:
            # Check if the calendar already exists in the database
            db_calendar = db.query(_models.Calendar).filter(
                _models.Calendar.id == calendar["id"],
                _models.Calendar.grant_id == calendar["grant_id"],
                _models.Calendar.user_id == user.id
            ).first()

            if db_calendar:
                # Update existing calendar
                db_calendar.name = calendar["name"]
                db_calendar.object = calendar["object"]
                db_calendar.is_primary = calendar["is_primary"]
                db_calendar.read_only = calendar["read_only"]
                db_calendar.is_owned_by_user = calendar["is_owned_by_user"]
            else:
                # Create a new calendar record
                new_calendar = _models.Calendar(
                    id=calendar["id"],
                    name=calendar["name"],
                    grant_id=calendar["grant_id"],
                    object=calendar["object"],
                    is_primary=calendar["is_primary"],
                    read_only=calendar["read_only"],
                    is_owned_by_user=calendar["is_owned_by_user"],
                    user_id=user.id  # Associate the calendar with the current user
                )
                db.add(new_calendar)
        
        # Commit the changes to the database
        db.commit()

    logger.info(f"Calendars synced successfully for user with email {user.email}")

    return JSONResponse(
        content={
            "status": "success",
            "message": "Calendars synced successfully",
        },
        status_code=status.HTTP_200_OK
    )






