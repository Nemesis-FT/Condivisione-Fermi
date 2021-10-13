from sqlalchemy.orm import Session


def commit(db: Session, data):
    db.add(data)
    db.commit()
    db.refresh(data)
    return data
