from controllers.scrape import scrape_file, scrape_url, table
from fastapi import APIRouter


scrape_router = APIRouter()


scrape_router.include_router(scrape_url.router)

scrape_router.include_router(scrape_file.router)

scrape_router.include_router(table.router)

