import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from dotenv import load_dotenv
from datetime import datetime
import pytz  # You'll need to install the pytz library for timezone handling
#from langchain_google_genai import ChatGoogleGenerativeAI
import sqlalchemy.orm as _orm
import database as _database
import auth_services as _services
import schemas as _schemas
import auth_services as _services
import fastapi as _fastapi
import models as _models
from fastapi import APIRouter ,  HTTPException

import requests

load_dotenv()


# Function to improve email structure and grammar
def improve_email(email_content, gemini_api_key, user_name ):
    # Configure the API key
    genai.configure(api_key=gemini_api_key)
    
    # Initialize the generative model
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    
    # Generate the improved email content
    response = model.generate_content([
       f"""
        You are an expert in professional communication. Please review and improve the following email for grammar, clarity, and structure. Ensure that the tone is professional and that the message is concise and well-organized.

        Email text:
        {email_content}

        Provide the response in JSON format with "subject" and "body" as keys. Ensure the email body ends with the user's name from the {user_name} variable. The response should be formatted as a plain JSON object, without any code blocks, backslashes, or extra spaces/line breaks.

        Example format:
        {{
        "subject": "content here",
        "body": "content here"
        }}
        """
    ])

    
    # Parse the response and return the result
    return response.text



def generate_email_reply(email_content: str, api_key: str ,username: str , user_prompt: str) -> str:
    """
    Generate a professional and contextually appropriate email reply based on the email content.

    Args:
    email_content (str): The content of the email extracted from HTML.
    api_key (str): The API key for Google Gemini.
    username (str): name that should we used in email for replying 

    Returns:
    str: The generated email reply.
    """
    # Configure the Gemini API
    genai.configure(api_key=api_key)

    # Prepare the prompt for the generative model
    prompt= f"""
        You are an AI assistant designed to generate professional and contextually appropriate email replies. 
        Below is the content of an email that was extracted from HTML, along with a brief description provided by the user on how to respond. Please analyze both the email content and the user's instructions to generate a polite and concise reply.

        Consider the following when crafting your response:
        - Address the sender by their name if available.
        - Acknowledge the key points or requests made in the email.
        - Follow the user's instructions or provided guidance for the reply.
        - Provide a clear and courteous response or follow-up action.
        - Maintain a professional and respectful tone.
        - add name in ending in email {username}

        Email content:
        {email_content}

        User's instructions for reply:
        {user_prompt}
        Provide the response in JSON format with "subject" and "body" as keys. Ensure the email body ends with the user's name from the {username} variable. The response should be formatted as a plain JSON object, without any code blocks, backslashes, or extra spaces/line breaks.

        Example format:
        {{
        "subject": "content here",
        "body": "content here"
        }}
        """

  
    # Generate the email reply using the Gemini model
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content([prompt])


    # Return the generated reply
    return response.text



