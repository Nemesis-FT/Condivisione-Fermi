from fastapi import APIRouter, Depends, Request, HTTPException
from condivisione.dependencies import get_auth_token, get_db, get_planetarium_version
from condivisione.authentication import get_current_user, check_permissions
from condivisione.database.crud.server import get_server, update_server
from sqlalchemy.orm import Session
from condivisione.database import schemas, models
from condivisione.enums import UserType

router = APIRouter(
    prefix="/server",
    tags=["server"],
    responses={404: {"description": "Not found"}}
)


@router.get("/", tags=["server"], response_model=schemas.Server)
async def read_server(db: Session = Depends(get_db)):
    """
    Gets current state of server
    """
    s: models.Server = get_server(db)
    return s


@router.patch("/", tags=["server"], response_model=schemas.Server)
async def patch_server(server: schemas.Server, db: Session = Depends(get_db),
                       current_user: models.User = Depends(get_current_user)):
    """
    Updates the state of the server
    """
    if not check_permissions(current_user, level=UserType.ADMIN):
        raise HTTPException(403, "You are not authorized.")
    s: models.Server = update_server(db, server)
    if s:
        return s


@router.get("/planetarium", tags=["server"], response_model=schemas.Planetarium)
async def planetarium_retrieve(version=Depends(get_planetarium_version), db: Session = Depends(get_db)):
    """
    Responds to the planetarium master server
    """
    s = get_server(db)
    if s:
        return schemas.Planetarium(version=version, type="Condivisione",
                                   server=s)
