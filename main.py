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
        database_info += f'{table_name}\n'
        for column in inspector.get_columns(table_name):
            database_info += f"\t {column['name']} ({column['type']})\n"
    return f"""
    Given an input question, respond with syntactically correct PostgreSQL. Be creative but the SQL must be correct.

    You can use the following tables with the associated columns:
    {database_info}

    Here are some examples:
    Example 1:
    ===========================================
    Input:
    how many new cases in the united states in the past week
    Output:
    SELECT SUM(new_cases) FROM data WHERE iso_code = 'USA' AND date > NOW() - INTERVAL '7 days';

    Example 2:
    ===========================================
    Input:
    which country had the most new cases in the past week
    Output:
    SELECT location, SUM(new_cases) FROM data WHERE (date > NOW() - INTERVAL '7 days') and new_cases is not NULL GROUP BY location ORDER BY SUM(new_cases) DESC LIMIT 1;

    Example 3:
    ===========================================
    Input:
    which continent had the least new deaths in January of 2022
    Output:
    SELECT continent, sum(new_deaths)
    FROM data
    WHERE date BETWEEN '2022-01-01' AND '2022-01-31' and new_deaths is not NULL and continent is not NULL
    GROUP BY continent
    ORDER BY 2 ASC;

    Example 4:
    ===========================================
    Input:
    which continent had the most new deaths 2 weeks ago
    Output:
    SELECT continent, SUM(new_deaths) FROM data
    WHERE date = (current_date - INTERVAL '2 weeks') AND new_deaths IS NOT NULL AND continent IS NOT NULL
    GROUP BY 1 ORDER BY 2 DESC;

    Begin.
    """

def ask_gpt3(prompt: str, stop: str = None, max_tokens: int = 256):
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


def read_query_results(question, query, results):
    """Read the results from gpt-3 query."""
    new_prompt = f"""
    Given a question, a SQL query, and a table of the results, respond with a human readable response to the question.

    Example 1:
    ===========================================
    Question:
    how many new cases in the USA in the past week

    Query:
    SELECT SUM(new_cases) FROM data WHERE iso_code = 'USA' AND date > NOW() - INTERVAL '7 days';

    Results:
            sum
    0  105599.0

    Response: There have been 105,599 new cases in the USA in the past week.
    ===========================================

    Example 2:
    ===========================================
    Question:
    how many deaths in the USA in the last week

    Query:
    SELECT SUM(new_deaths) FROM data WHERE iso_code = 'USA' AND date > NOW() - INTERVAL '1 week';

    Results:
        sum
    0  548.0

    Response: 548 deaths in the last week
    ===========================================

    Begin.

    Question:
    {question}

    Query:
    {query}

    Results:
    {results}

    Response:
    ```
    """
    return ask_gpt3(new_prompt, stop="```")

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
            code = ask_gpt3(prompt, stop='```', max_tokens=512)
            print_generated_code(code)
            result = execute_code(code, connection)
            print_results(result)
            answer = read_query_results(task, code, result)
            print(f"\nANSWER: {answer}")
        except Exception as e:
            print(f"ERROR: {e}")
    clean_up_db_connection(connection)
