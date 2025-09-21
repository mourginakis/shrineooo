import os
from dotenv import load_dotenv

load_dotenv()

##############################################
## Secrets

# Postgres DB (Digital Ocean)
POSTGRES_USERNAME      = os.environ.get('POSTGRES_USERNAME',   '')
POSTGRES_PASSWORD      = os.environ.get('POSTGRES_PASSWORD',   '')
POSTGRES_HOST          = os.environ.get('POSTGRES_HOST',       '')
POSTGRES_PORT          = os.environ.get('POSTGRES_PORT',       '')
POSTGRES_DATABASE      = os.environ.get('POSTGRES_DATABASE',   '')
POSTGRES_CREDENTIALS = {
    "user": POSTGRES_USERNAME,
    "password": POSTGRES_PASSWORD,
    "host": POSTGRES_HOST,
    "port": POSTGRES_PORT,
    "dbname": POSTGRES_DATABASE,
}
POSTGRES_URL = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
