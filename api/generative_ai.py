import google.generativeai as genai
from langchain_community.utilities import SQLDatabase
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import sqlalchemy.orm as _orm
import models as _models
from nylas import Client
import os
import datetime
load_dotenv()

# Retrieve environment variables
API_URI = os.environ.get("API_URI")
gemini_api_key = os.environ.get("GEMINI_API_KEYY")

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


def delete_calendar_event(nylas_api_key:str,nylas_api_uri:str , nylas_grant_id:str, id:str , calendar_id:str , user_id:str ):
    """
    This endpoint is used to delete calendar events 
    """
    nylas = Client(nylas_api_key,nylas_api_uri)
    event_id = id
    db= _orm.Session
    # Perform the join between CalendarData and Grant based on the organizer's email
    result = (
        db.query(_models.CalendarData, _models.Grant.id.label('grant_id'))
        .join(_models.Grant, _models.Grant.email == _models.CalendarData.organizer_email)
        .filter(_models.CalendarData.user_id == user_id)
        .all()
    )

    # Extract the required data from the result
    calendar_data = [
        {
            "id": calendar_event.id,
            "calendar_id": calendar_event.calendar_id,
            "grant_id": grant_id
        }
        for calendar_event, grant_id in result
    ]

    event = nylas.events.destroy(
    calendar_data['grant_id'],
    calendar_data['id'],
    query_params={
      "calendar_id":  calendar_data['calendar_id']
    }
    )
    
    return event


class CalendarEventAgent:
    def __init__(self, user_id: str, db_uri: str, google_api_key: str, llm_model: str = "gemini-pro"):
        """
        Initialize the CalendarEventAgent with the database connection and LLM model.
        
        :param user_id: The ID of the user for whom the events are being fetched.
        :param db_uri: URI for the SQLite database.
        :param google_api_key: Google API key for the LLM.
        :param llm_model: Model name for the LLM (default: "gemini-pro").
        """
        self.user_id = user_id
        self.llm = ChatGoogleGenerativeAI(model=llm_model, google_api_key=google_api_key)
        self.db = SQLDatabase.from_uri(db_uri)
        self.tools = self._create_tools()
        self.agent = self._initialize_agent()

    def _create_tools(self):
        """Creates tools for listing and summarizing events."""
        list_events_tool = Tool.from_function(
            func=self.list_events,
            name="ListEvents",
            description="Retrieve all calendar events/meetings/call for the specified user."
        )

        # Tool to provide details for a specific event based on its title
        event_details_tool = Tool.from_function(
                            func=self.get_event_details,
                            name="GetEventDetails",
                            description="Retrieve details for a specific event, meeting, or call based on the title provided."
                        )


        return [list_events_tool,event_details_tool]

    def _initialize_agent(self): 
        """Initializes the AI agent with the available tools."""
        return initialize_agent(
            tools=self.tools,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            llm=self.llm,
            verbose=True
        )
    


    def list_events(self, *args, **kwargs):
        """Fetches all events for the user from the calendar_event table."""
        query_result = self.db.run(f"SELECT * FROM calendar_event WHERE user_id = {self.user_id};")
        return query_result
    
    
    

    def get_event_details(self, title: str):
        """Fetches details for a specific event based on its title."""
        query_result = self.db.run(f"SELECT * FROM calendar_event WHERE {title} AND user_id = {self.user_id};")
        if query_result:
            return query_result
        else:
            return "No event found with the provided title."

   
    def run(self, prompt: str):
        """Runs the agent with the provided prompt."""
        # # Define the prompt template and LLMChain inside the run method
        # prompt_template = f"""
        # Summarize the following content in calendar
        # """
        # llm_chain = LLMChain(
        #     llm=self.llm,
        #     prompt=PromptTemplate.from_template(prompt_template)
        # )
        
        # # Use LLMChain for processing the prompt
        # processed_prompt = llm_chain.run({"content": prompt})
        return self.agent.run(prompt)


