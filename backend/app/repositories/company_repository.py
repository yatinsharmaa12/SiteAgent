from sqlalchemy.orm import Session

from app.models.company import Company


def get_company_for_user(
    db: Session,
    company_id: int,
    user_id: int,
):
    return (
        db.query(Company)
        .filter(
            Company.id == company_id,
            Company.owner_id == user_id,
        )
        .first()
    )


def list_companies_for_user(
    db: Session,
    user_id: int,
):
    return (
        db.query(Company)
        .filter(
            Company.owner_id == user_id,
        )
        .order_by(Company.id)
        .all()
    )

def get_company_by_website_for_user(
    db: Session,
    website_url: str,
    user_id: int,
):
    return (
        db.query(Company)
        .filter(
            Company.website_url == website_url,
            Company.owner_id == user_id,
        )
        .first()
    )