import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_google_genai import ChatGoogleGenerativeAI
import re

def read_sql_query(sql, db):
    # Connect to the SQLite database
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # Execute the SQL query
    cur.execute(sql)
    rows = cur.fetchall()

    # Print each row in the result
    for row in rows:
        print(row)

    # Close the connection
    conn.close()

# Load the SQL database from a URI
input_db = SQLDatabase.from_uri("sqlite:///./database.db")

# Initialize the LLM using Google Generative AI
llm_1 = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key="AIzaSyBdQyoRkPk3NqthrhffhfjVAIN2iWMKmUB_0Ee6AWq8"
)

# Create an SQLDatabaseChain instance for interacting with the database using LLM
db_agent = SQLDatabaseChain(
    llm=llm_1,
    database=input_db,
    verbose=True
)

# Run a query to fetch upcoming events using the LLM
raw_query = db_agent.run("show me upcoming events")
print(raw_query)



# Execute the cleaned SQL query
read_sql_query(raw_query, "./database.db")
