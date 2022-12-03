# sql_gpt

Use GPT-3 to query a PostgreSQL database.

To run:
- Set up environment variables for a PostsgreSQL database
- Open a terminal and run `python main.py`
- Ask it a question!

Areas for improvement:
- Clean/consolidate the data for specific dataset, address the quirks
- Update prompt with more database specifics
- Add more complicated query examples in prompt to get better results
- Tweak the model's parameters to see if better results can be obtained
- Add more steps in the "thinking process" for better problem tackling
- Get it to be able to retry again based on error messages

Various inspiration for this:
- https://github.com/bkane1/gpt3-instruct-sandbox
- https://github.com/nat/natbot
- https://replit.com/@SergeyKarayev/gpt-squaredpy