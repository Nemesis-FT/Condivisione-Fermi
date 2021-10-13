import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta

from condivisione.database.crud.server import create_server
from condivisione.routers import users, server, subjects
from condivisione.database import schemas, models
from condivisione.database.crud.users import create_user
from condivisione.dependencies import get_db
from condivisione.database.db import engine, SessionLocal
from condivisione.authentication import Token, OAuth2PasswordRequestForm, authenticate_user, \
    ACCESS_TOKEN_EXPIRE_MINUTES, create_token, get_hash
from condivisione.enums import UserType

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router)
app.include_router(server.router)
app.include_router(subjects.router)

origins = [
    "https://frontend.address.com",
]

if os.getenv("DEBUG"):
    origins.append(
        "http://localhost:3000",
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory="Files"), name="files")


@app.get("/")
async def root():
    return {
        "message": "This is the backend of the webapp. If you see this page, it means that the server is alive and well."}


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    token = create_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


if __name__ == "__main__":
    with SessionLocal() as db:
        if not db.query(models.User).filter_by(type=UserType.ADMIN.value).first():
            create_user(db, schemas.UserCreate(email="admin@admin.com", hash=get_hash("password"), name="admin",
                                               surname="admin", parent_email="admin@admin.com",
                                               class_number="ADMIN", type=UserType.ADMIN.value))
            create_server(db)
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT")))
