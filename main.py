from fastapi import FastAPI, Depends, HTTPException, Request
from db.database import Base, get_db
from db.database import engine
from routers import user_router, router, router_ai
from auth import authentication
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

app = FastAPI()


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("error.html", {"request": request, "detail": exc.detail},
                                      status_code=exc.status_code)


app.mount("/static", StaticFiles(directory="templates"), name="static")

app.include_router(user_router.router)
app.include_router(router.router)
app.include_router(authentication.router)
app.include_router(router_ai.router)

Base.metadata.create_all(bind=engine)
