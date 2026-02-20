from fastapi import FastAPI
from routers import products
from data.database import engine
from data import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(products.router)

@app.get("/")
def home():
    return {"message": "API Rodando!"}