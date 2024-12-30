import os
from anthropic import Anthropic
from dotenv import load_dotenv
import sqlite3
from db import ProductDatabase
import chainlit as cl 

from pydantic.dataclasses import rebuild_dataclass
from chainlit.config import CodeSettings

# Force rebuild of CodeSettings for compatibility
rebuild_dataclass(CodeSettings)


load_dotenv('.env')

class UnsafeAI:
    def __init__(self):
        api_key=os.getenv('ANTHROPIC_API_KEY')
        self.client=Anthropic(api_key=api_key)
        self.db_name="product_store.db"
        self.conn= sqlite3.connect(self.db_name)
        self.cursor=self.conn.cursor()
        self.schema=self.get_db_schema()

    def get_db_schema(self):
        schema=[]
        self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")  
        tables=self.cursor.fetchall()  
        for table in tables:
            if table[0]:
                schema.append(table[0])
        return '\n'.join(schema)
    
    def execute_db_query(self, db_query):
        try:
            self.cursor.execute(db_query)
            result=self.cursor.fetchall()
            return result
        except Exception as e:
            return e
    
    def generate_sql_query(self, user_query):
        system_prompt = f"""
You are an AI assistant that converts natural language into SQL queries to fetch product details from an SQLite database.
1. The database schema is:
{self.schema}

Examples:
- User: "Show me all laptops under $1000"
  SQL: SELECT * FROM products WHERE category='Electronics' AND price < 1000;

- User: "Find smartphones"
  SQL: SELECT * FROM products WHERE category='Electronics' AND product_name LIKE '%smartphone%';

Always output **only the SQL query** without explanation.
"""
        messages=[{'role':'user','content':user_query}]
        response=self.client.messages.create(model="claude-3-5-haiku-20241022",
                                             max_tokens=1000,
                                             system=system_prompt,
                                             messages=messages)
        return response.content[0].text

    def generate_response(self,user_query, db_results):
        system_prompt = f"""
You are a helpful assistant that explains database query results in **natural language**.
1. Convert database output into a **friendly, conversational response**.
2. If no results are found, suggest related options based on query context.
3. Respond clearly, summarizing product names, categories, and prices.

Example:
Input: "Find smartphones under $800"
Database Result: [('Smartphone', 'https://example.com/phone', 699.99, 'Electronics', 'Latest smartphone')]
Output: "I found 1 smartphone under $800. It's priced at $699.99 and listed as the latest model. Would you like to know more details?"
"""
        messages=[{'role':'user', 'content':f"Query: {user_query} \n Results: {db_results}"}]
        response=self.client.messages.create(model="claude-3-5-haiku-20241022",
                                             max_tokens=1000,
                                             system=system_prompt,
                                             messages=messages)
        return response.content[0].text

    async def process_query(self, user_input):
        sql_query=self.generate_sql_query(user_input)
        db_results=self.execute_db_query(sql_query)
        final_response = self.generate_response(user_input, db_results)
        return final_response

ai = UnsafeAI()

@cl.on_message
async def main(message):
    """Handle user input through Chainlit."""
    user_query = message.content  # User's message
    response = await ai.process_query(user_query)  # Process query
    await cl.Message(response).send()  # Send response

