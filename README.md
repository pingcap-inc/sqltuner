# SQLTuner

SQLTuner is a simple tool designed to tune SQL statements to run faster on TiDB. It utilizes ChatGPT to perform the actual work.

## Development
* The app requires some Python libraries, so make sure you have Python version >= 3.10 installed.
* There is a .env_template file. Please rename it to .env and update its content with the ChatGPT API Key and the TiDB server configuration.
* After making the necessary changes to the .env file, run the following commands to run the server. The server will listen on port 5001:
```code
pip install -r requirements.txt
python3 app.py
```

# Notes
Currently, the application is running using Flask, and it's not yet ready for production use. For production, consider using Gunicorn or uWSGI instead.
