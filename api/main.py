from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from starlette.requests import Request
from database import Base , engine
from routers import auth , stock , nylas_admin


app = FastAPI()

Base.metadata.create_all(engine)
app.include_router(auth.router)
app.include_router(stock.router)
app.include_router(nylas_admin.router)





if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0")
