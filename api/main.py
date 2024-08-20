from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from scheduler_task import scheduler
from starlette.requests import Request
from database import Base , engine
from routers import auth , stock , nylas_admin , nylas_email , gen_ai


app = FastAPI()

Base.metadata.create_all(engine)
app.include_router(auth.router)
# app.include_router(stock.router)
app.include_router(nylas_admin.router)
app.include_router(nylas_email.router)
app.include_router(gen_ai.router)



@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0")
