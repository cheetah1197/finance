from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.routers import tariffs, economics
# Assuming app.core.config handles settings (or remove if unused)
# from app.core.config import settings 

# -------------------------------------------------------------
# 1. TEMPLATES CONFIGURATION
# Define the directory where your HTML templates live
templates = Jinja2Templates(directory="app/templates")
# -------------------------------------------------------------

# Use a hardcoded title for now
app = FastAPI(title="Tariffs & Economics API")

# Include the routers, with a common prefix for each module
app.include_router(tariffs.router, prefix="/api/v1/tariffs", tags=["Tariffs"])
app.include_router(economics.router, prefix="/api/v1/economics", tags=["Economics"])

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    # Pass the request object to the template, which is required by Jinja2
    return templates.TemplateResponse("index.html", {"request": request, "title": "Data Explorer"})