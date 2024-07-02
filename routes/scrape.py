from controllers.scrape import scrape_file, scrape_url
from fastapi import APIRouter


scrape_router = APIRouter()


scrape_router.include_router(scrape_url.router)

scrape_router.include_router(scrape_file.router)