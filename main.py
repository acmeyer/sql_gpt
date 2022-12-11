import os
import pandas as pd
import openai
from sqlalchemy import create_engine, inspect, types
from dotenv import load_dotenv
load_dotenv()

def seed_data(connection):
    """Pulls the latest data from Our World in Data and seeds it into the database."""
    df = pd.read_csv('https://covid.ourworldindata.org/data/owid-covid-data.csv')
    # Specify the data type for the date column since it is not being inferred correctly
    df.to_sql('data', connection, if_exists='replace', index=False, dtype={'date': types.DateTime})

def setup_prompt(engine):
    """Setup the main SQL prompt for GPT-3."""
    inspector = inspect(engine)
    database_info = ""
    for table_name in inspector.get_table_names():
        column_names = [col['name'] for col in inspector.get_columns(table_name)]
        columns = ", ".join(column_names)
        database_info += f'* {table_name}: ({columns})\n'

    with open('sql_prompt.md') as f:
        prompt = f.read()
        prompt = prompt.replace("$database_info", database_info)
        with open('sql_prompt_examples.md') as e:
            examples = e.read()
            prompt = prompt.replace("$examples", examples)
    return prompt

def ask_gpt3_code(prompt: str, stop: str = None, max_tokens: int = 256):
    """Returns Codex GPT-3's response to the given prompt."""
    response = openai.Completion.create(model="code-davinci-002",
                                        prompt=prompt,
                                        temperature=0.7,
                                        max_tokens=max_tokens,
                                        stop=stop)
    print(f"\n[DEBUG] GPT response:\n{response}\n")
    return response.choices[0].text.strip()

def ask_gpt3_text(prompt: str, stop: str = None, max_tokens: int = 256):
    """Returns GPT-3's response to the given prompt."""
    response = openai.Completion.create(model="text-davinci-003",
                                        prompt=prompt,
                                        temperature=0.7,
                                        max_tokens=max_tokens,
                                        stop=stop)
    return response.choices[0].text.strip()


def execute_code(code: str, connection) -> str:
    """Executes the given code and returns the result."""
    df = pd.read_sql_query(code, connection)
    return df


def print_generated_code(code: str) -> None:
    """Prints the generated code from GPT-3 for debugging."""
    indented_code = '\n'.join([f'\t{line}' for line in code.splitlines()])
    print(f"\n[DEBUG] Generated SQL:\n{indented_code}\n")

def print_results(result: str) -> None:
    """Prints the results of the query."""
    print(f"\n[DEBUG] Result:\n{result}\n")


def read_query_results(question, results):
    """Read the results from gpt-3 query."""
    with open('results_prompt.md') as f:
        new_prompt = f.read()
        new_prompt = new_prompt.replace("$question", question)
        new_prompt = new_prompt.replace("$results", results.to_string())
    return ask_gpt3_text(new_prompt, stop="```")

def create_db_connection():
    """Creates a connection to the database."""
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
    return engine.connect()

def clean_up_db_connection(connection):
    """Close the connection to the database."""
    connection.close()

if __name__ == "__main__":
    openai.api_key = os.getenv("OPENAI_API_KEY")
    connection = create_db_connection()
    # seed_data(connection)
    while (task := input('QUESTION: ').strip()) != "":
        try:
            prompt = setup_prompt(connection.engine)
            prompt = f'{prompt}\nInput:\n{task}\nOutput:\n```sql'
            code = ask_gpt3_code(prompt, stop='```', max_tokens=512)
            print_generated_code(code)
            result = execute_code(code, connection)
            print_results(result)
            answer = read_query_results(task, result)
            print(f"\nANSWER: {answer}")
        except Exception as e:
            print(f"ERROR: {e}")
    clean_up_db_connection(connection)
