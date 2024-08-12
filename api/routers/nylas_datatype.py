from typing import List
from nylas import Client
from logger import Logger
from typing import List
from fastapi import HTTPException 
import os 

# Create an instance of the Logger class
logger_instance = Logger()
# Get a logger for your module
logger = logger_instance.get_logger("stock market api")

# Retrieve environment variables
API_URI = os.environ.get("API_URI")

class Grant:
    def __init__(self, id, provider, scope, grant_status, email, user_agent, ip, state, created_at, updated_at, provider_user_id, settings):
        self.id = id
        self.provider = provider
        self.scope = scope
        self.grant_status = grant_status
        self.email = email
        self.user_agent = user_agent
        self.ip = ip
        self.state = state
        self.created_at = created_at
        self.updated_at = updated_at
        self.provider_user_id = provider_user_id
        self.settings = settings

class ListResponse:
    def __init__(self, grants: List[Grant]):
        self.grants = grants
        


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


