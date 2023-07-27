# SQLTuner

It is a simple tool designed to tune sql statement to run fast on TiDB. It uses chatgpt to do the real work.

## Development
* The app uses some python libraries need Python version >= 3.10
* There is a .env_template file. Rename it to .env and change its content like the ChatGPT API Key and the TiDB server configuration.
* Run this command after that
```code
pip install -r requirements.txt
python3 app.py
```

# Notes
Now the appliction is running using Flask, it's not ready for production use. You may use Gunicorn or uWSGI instead.
