import sys
import os
import dotenv
import sqlalchemy
from sqlalchemy import create_engine

# Add the 'src' directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import database as db

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)

metadata_obj = sqlalchemy.MetaData()
Jobs = sqlalchemy.Table("Jobs", metadata_obj, autoload_with= db.engine)