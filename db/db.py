from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# DB_URL = 'mysql+pymysql://{USERNAME}:{PASSWORD}@{PORT}/{DBNAME}'
MYSQL_URL = 'mysql+pymysql://root:123456@localhost:3306/grade_manege?charset=utf8'
POOL_SIZE = 20
POOL_RECYCLE = 3600
POOL_TIMEOUT = 15
MAX_OVERFLOW = 2
CONNECT_TIMEOUT = 60


def get_db_session(engine):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        return session
    except Exception as e:
        print("Error getting DB session:", e)
        return None


class Database:

    def __init__(self) -> None:
        self.connection_is_active = False
        self.engine = None

    def get_db_connection(self):
        if not self.connection_is_active:
            connect_args = {"connect_timeout": CONNECT_TIMEOUT}
            try:
                self.engine = create_engine(MYSQL_URL,
                                            pool_size=POOL_SIZE,
                                            pool_recycle=POOL_RECYCLE,
                                            pool_timeout=POOL_TIMEOUT,
                                            max_overflow=MAX_OVERFLOW,
                                            connect_args=connect_args)
                return self.engine
            except Exception as e:
                print("Error connecting to MySQL DB:", e)
        return self.engine
