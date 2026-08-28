from app.db.database import Base, engine

from app.models.company import Company
from app.models.url_db import URL
from app.models.page_db import Page


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully.")