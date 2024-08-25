from langchain.utilities import SQLDatabase
from langchain.llms import OpenAI
from langchain_experimental.sql import SQLDatabaseChain
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os 
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Initialize the LLM using Google Generative AI
llm_1 = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key="AIzaSyBdQyoRkPk3NqVAIN2iWMKmUB_0Ee6AWq8"
)

DATABASE_URL = (
    "postgresql://{username}:{password}@{host}:{port}/{database_name}".format(
        username=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database_name=os.getenv("POSTGRES_DB"),
    )
)

db = SQLDatabase.from_uri(DATABASE_URL, include_tables=['products'],sample_rows_in_table_info=2)

db_chain = SQLDatabaseChain.from_llm(llm_1, db, verbose=True)



def retrieve_from_db(query: str) -> str:
    db_context = db_chain(query)
    # Clean up the SQL query by removing any code block formatting
    cleaned_context = db_context['result'].strip().replace("```sql", "").replace("```", "")
    return cleaned_context


def generate(query: str) -> str:
    db_context = retrieve_from_db(query)
    
    system_message = """You are a professional representative of an employment agency.
        You have to answer user's queries and provide relevant information to help in their job search. 
        Example:
        
        Input:
        Where are the most number of jobs for an English Teacher in Canada?
        
        Context:
        The most number of jobs for an English Teacher in Canada is in the following cities:
        1. Ontario
        2. British Columbia
        
        Output:
        The most number of jobs for an English Teacher in Canada is in Toronto and British Columbia
        """
    
    human_qry_template = HumanMessagePromptTemplate.from_template(
        """Input:
        {human_input}
        
        Context:
        {db_context}
        
        Output:
        """
    )
    messages = [
      SystemMessage(content=system_message),
      human_qry_template.format(human_input=query, db_context=db_context)
    ]
    response = llm_1(messages).content
    return response


# Example usage
print(generate("show me product"))