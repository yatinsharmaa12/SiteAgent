from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.company_repository import get_company_for_user
from app.repositories.crawl_job_repository import (
    create_crawl_job,
    get_crawl_job_for_company,
    list_crawl_jobs_for_company,
)
from app.services.crawl_service import run_crawl_job


router = APIRouter(
    prefix="/companies",
    tags=["Company Crawler"],
)


class CrawlCompanyRequest(BaseModel):
    max_pages: int = Field(
        default=5,
        ge=1,
        le=100,
    )

    max_depth: int = Field(
        default=1,
        ge=0,
        le=10,
    )


@router.post("/{company_id}/crawl")
async def crawl_company(
    company_id: int,
    request: CrawlCompanyRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    job = create_crawl_job(
        db=db,
        company_id=company.id,
        max_pages=request.max_pages,
        max_depth=request.max_depth,
    )

    background_tasks.add_task(
        run_crawl_job,
        job.id,
        company.id,
    )

    return {
        "job_id": job.id,
        "company_id": company.id,
        "company_name": company.name,
        "start_url": company.website_url,
        "status": job.status,
    }


@router.get("/{company_id}/crawl-jobs/{job_id}")
def get_crawl_job(
    company_id: int,
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    job = get_crawl_job_for_company(
        db=db,
        job_id=job_id,
        company_id=company.id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Crawl job not found",
        )

    return {
        "job_id": job.id,
        "company_id": job.company_id,
        "status": job.status,
        "max_pages": job.max_pages,
        "max_depth": job.max_depth,
        "pages_crawled": job.pages_crawled,
        "error": job.error,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
    }


@router.get("/{company_id}/crawl-jobs")
def list_crawl_jobs(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    jobs = list_crawl_jobs_for_company(
        db=db,
        company_id=company.id,
    )

    return [
        {
            "job_id": job.id,
            "company_id": job.company_id,
            "status": job.status,
            "max_pages": job.max_pages,
            "max_depth": job.max_depth,
            "pages_crawled": job.pages_crawled,
            "error": job.error,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }
        for job in jobs
    ]