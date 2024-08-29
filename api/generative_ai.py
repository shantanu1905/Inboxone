import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI  
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
import os
from dotenv import load_dotenv
import sqlalchemy.orm as _orm
import models as _models
from nylas import Client
import os
import datetime
# Database URL for SQLite
DATABASE_URL = "sqlite:///./database.db"
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



class CalendarEventSQLRAGChain:
    def __init__(self, google_api_key, user_id):
        self.db_path = "sqlite:///./database.db"  # Adjust path as needed
        self.google_api_key = google_api_key
        self.user_id = user_id
        
        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            max_tokens=500,
            google_api_key=self.google_api_key
        )
        
        # Initialize the SQL database
        self.db = SQLDatabase.from_uri(self.db_path)
        
        # Create the SQL agent
        self.agent_executor = create_sql_agent(
            self.llm,
            db=self.db,
            agent_type="zero-shot-react-description",
            verbose=True
        )
        
        # Initialize the embeddings model
        self.embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.google_api_key
        )
        
        # Create the prompt and question-answer chain
        self.prompt = self._create_prompt()
        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt)
    
    def _create_prompt(self):
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            f"the question. If you don't know the answer, say that you "
            f"Extract data from the calendar_event table where user_id={self.user_id}. "
            "Use four sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
        return prompt

    def query_sql(self, question):
        query_result = self.agent_executor({"input": question})
        return query_result.get("output", "")

    def create_vectorstore(self, texts):
        return FAISS.from_texts(texts, self.embeddings_model)

    def retrieve_answer(self, question):
        query_result = self.query_sql(question)
        texts = [query_result]  # Assuming query_result is a string
        vectorstore = self.create_vectorstore(texts)
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})
        rag_chain = create_retrieval_chain(retriever, self.question_answer_chain)
        response = rag_chain.invoke({"input": question})
        return response.get("answer", "No answer available.")