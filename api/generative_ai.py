import google.generativeai as genai
from langchain_community.document_loaders import UnstructuredHTMLLoader
import os
from dotenv import load_dotenv
#from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


# Function to improve email structure and grammar
def improve_email(email_content, gemini_api_key ):
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

       
        """
    ])
    
    # Parse the response and return the result
    return response.text



def generate_email_reply(email_content: str, api_key: str) -> str:
    """
    Generate a professional and contextually appropriate email reply based on the email content.

    Args:
    email_content (str): The content of the email extracted from HTML.
    api_key (str): The API key for Google Gemini.

    Returns:
    str: The generated email reply.
    """
    # Configure the Gemini API
    genai.configure(api_key=api_key)

    # Prepare the prompt for the generative model
    prompt = f"""
    You are an AI assistant designed to generate professional and contextually appropriate email replies. 
    Below is the content of an email that was extracted from HTML. Please analyze the content and generate 
    a polite and concise reply.

    Consider the following when crafting your response:
    - Address the sender by their name if available.
    - Acknowledge the key points or requests made in the email.
    - Provide a clear and courteous response or follow-up action.
    - Maintain a professional and respectful tone.

    Email content:
    {email_content}

    Generate the reply with the following format:
    - greeting: A polite greeting to start the email.
    - body: The main body of the reply, addressing the key points or requests.
    - closing: A courteous closing statement.
    - signature: A professional email signature.

    
    provide resonse in json format subject and body only ,  Format the JSON object without any extra spaces or line breaks.
    """

    # Generate the email reply using the Gemini model
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content([prompt])

    # Return the generated reply
    return response.text