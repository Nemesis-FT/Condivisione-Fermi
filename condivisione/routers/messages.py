from fastapi import APIRouter, Depends, HTTPException

from condivisione.dependencies import get_auth_token, get_db
from condivisione.authentication import get_current_user, check_permissions
from condivisione.database.crud.messages import get_message, get_messages, update_message, create_message, \
    remove_message
from sqlalchemy.orm import Session
from condivisione.database import schemas, models
from condivisione.enums import UserType

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    responses={404: {"description": "Not found"}, 403: {"description": "Access Denied"},
               401: {"description": "Unauthorized"}}
)


@router.get("/", response_model=schemas.MessageList)
async def read_subjects(db: Session = Depends(get_db)):
    """
    Returns data about the messages.
    """
    return get_messages(db)


@router.get("/{_id}", response_model=schemas.Message)
async def read_message(_id: int, db: Session = Depends(get_db)):
    """
    Returns data about the selected message.
    """
    return get_message(db, _id)


@router.post("/", response_model=schemas.Message)
async def forge_message(message: schemas.Message, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    """
    Creates a new message.
    """
    if not check_permissions(current_user, level=UserType.ADMIN):
        raise HTTPException(403)
    return create_message(db, message)


@router.patch("/{_id}", response_model=schemas.Subject)
async def update_message(_id: int, message: schemas.Message, db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    """
    Updates the selected message.
    """
    if not check_permissions(current_user, level=UserType.ADMIN):
        raise HTTPException(403)
    return update_message(db, message, _id)


@router.delete("/{_id}")
async def remove_message(_id: int, db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    """
    Removes the selected message.
    """
    if not check_permissions(current_user, level=UserType.ADMIN):
        raise HTTPException(403)
    remove_message(db, _id)
    return HTTPException(204, "Removed")
