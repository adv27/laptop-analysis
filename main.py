import io

from fastapi import BackgroundTasks, FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from xhtml2pdf import pisa

from laptop_analysis.external_resources.web_scraper import web_scraper_resource
from laptop_analysis.models import Base, Laptop

engine = create_engine(
    "sqlite:///laptops.db",
    echo=True,
)  # Create or connect to a SQLite database file
Base.metadata.create_all(engine)  # Create the table if it doesn't exist
session = Session(engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


class LaptopResponse(BaseModel):
    id: int
    title: str
    price: float
    review_count: int
    storage: str
    storage_in_gb: int


class LaptopAnalysisResponse(BaseModel):
    most_expensive_laptop: LaptopResponse
    most_reviews_laptop: LaptopResponse
    average_storage_capacity: float


async def get_analysis():
    most_expensive_laptop = session.query(Laptop).order_by(Laptop.price.desc()).first()
    most_reviews_laptop = (
        session.query(Laptop).order_by(Laptop.review_count.desc()).first()
    )
    average_storage_capacity = session.query(func.avg(Laptop.storage_in_gb)).all()[0][0]
    return {
        "most_expensive_laptop": most_expensive_laptop,
        "most_reviews_laptop": most_reviews_laptop,
        "average_storage_capacity": average_storage_capacity,
    }


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/laptops/fetch")
async def fetch_laptops():
    laptops = web_scraper_resource.get_laptops()

    insert_laptops = []
    existing_laptop_ids = session.scalars(select(Laptop.id)).all()
    for laptop in laptops:
        if laptop["id"] in existing_laptop_ids:
            continue
        new_laptop = Laptop(**laptop)
        insert_laptops.append(new_laptop)
    session.add_all(insert_laptops)
    session.commit()

    return {"message": f"Added {len(insert_laptops)} new laptops", "data": laptops}


@app.get("/laptops", response_model=list[LaptopResponse])
async def get_laptops():
    return session.query(Laptop).all()


@app.get("/laptops/analysis", response_model=LaptopAnalysisResponse)
async def get_laptops_analysis():
    return await get_analysis()


@app.get("/laptops/analysis/pdf", response_class=FileResponse)
async def get_laptops_analysis_pdf(request: Request, background_tasks: BackgroundTasks):
    analysis = await get_analysis()
    template = templates.TemplateResponse(
        request=request, name="analysis.html", context=analysis
    )
    buffer = io.BytesIO()
    pisa.CreatePDF(src=template.body, dest=buffer)
    background_tasks.add_task(buffer.close)
    headers = {"Content-Disposition": 'inline; filename="analysis.pdf"'}
    return Response(
        content=buffer.getvalue(), headers=headers, media_type="application/pdf"
    )
