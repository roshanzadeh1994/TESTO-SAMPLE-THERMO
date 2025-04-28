from fastapi import FastAPI, Depends, HTTPException, Request
from db.database import Base, get_db
from db.database import engine
from routers import user_router, router, router_ai
from auth import authentication
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize FastAPI app
app = FastAPI()

# Custom exception handler for HTTP errors
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("error.html", {"request": request, "detail": exc.detail},
                                      status_code=exc.status_code)

# Mount static files (e.g., images, CSS)
app.mount("/static", StaticFiles(directory="templates"), name="static")

# Include different routers for modular structure
app.include_router(user_router.router)
app.include_router(router.router)
app.include_router(authentication.router)
app.include_router(router_ai.router)

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)