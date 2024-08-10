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


@router.get("/api/users/profile" , response_model=_schemas.User )
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
            "is_verified": False,
            "msg":"Account verified !"
            }
        }

    return JSONResponse(content=response, status_code=200)

