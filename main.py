#!/usr/bin/env python3.12

#%% ========================================
from pprint import pprint
from src.secrets_ import POSTGRES_CREDENTIALS, POSTGRES_URL

# sqlalchemy rawsql is preferred over psycopg2 because the API
# is more readable and it auto manages connection pools.


#%% ========================================
