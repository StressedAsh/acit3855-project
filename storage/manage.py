from models import Base
from app import engine

def create_tables():
    Base.metadata.create_all(engine)
    return "Tables created successfully."


def drop_tables():
    Base.metadata.drop_all(engine)
    return "Tables dropped successfully."


if __name__ == "__main__":
    create_tables()