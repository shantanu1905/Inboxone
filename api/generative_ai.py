import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from dotenv import load_dotenv
from datetime import datetime
import pytz  # You'll need to install the pytz library for timezone handling
#from langchain_google_genai import ChatGoogleGenerativeAI
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




def fetch_events_from_calendar(grants_data, api_key):
    """
    Fetches event data from the Nylas API for multiple grants and emails and extracts specific fields.

    Args:
    - grants_data (list): A list of dictionaries with 'id' and 'email' for grants.
    - api_key (str): The API key for authorization.

    Returns:
    - list: A list of dictionaries containing the extracted event data for each grant and email.
    """
    def convert_unix_to_readable(timestamp, timezone_str):
        tz = pytz.timezone(timezone_str)
        return datetime.fromtimestamp(timestamp, tz).strftime('%Y-%m-%d %H:%M:%S')
    
    all_extracted_data = []

    for grant in grants_data:
        grant_id = grant.get("id")
        calendar_id = grant.get("email")
        
        if not grant_id or not calendar_id:
            continue  # Skip if either grant_id or calendar_id is missing
        
        # Construct the API URL
        url = f"https://api.us.nylas.com/v3/grants/{grant_id}/events?calendar_id={calendar_id}"

        # Set up the headers for the API request
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}',
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
                "start_time": convert_unix_to_readable(start_time, start_timezone) if start_time else None,
                "end_time": convert_unix_to_readable(end_time, end_timezone) if end_time else None,
                "created_at": datetime.fromtimestamp(event.get("created_at"), tz=pytz.utc).strftime('%Y-%m-%d %H:%M:%S') if event.get("created_at") else None,
                "updated_at": datetime.fromtimestamp(event.get("updated_at"), tz=pytz.utc).strftime('%Y-%m-%d %H:%M:%S') if event.get("updated_at") else None,
            }
            all_extracted_data.append(extracted_info)

    return all_extracted_data