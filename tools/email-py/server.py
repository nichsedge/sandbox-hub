from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Database setup ---
DATABASE_URL = "sqlite:///./tickets.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(String)
    reporter_email = Column(String)
    status = Column(String, default="OPEN")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# --- FastAPI app ---
app = FastAPI()


class TicketCreate(BaseModel):
    title: str
    description: str
    priority: str
    reporter_email: str
    source_email_uid: Optional[int] = None


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: str
    reporter_email: str
    status: str
    created_at: datetime
    updated_at: datetime


@app.post("/api/tickets", response_model=TicketResponse)
def create_ticket(ticket: TicketCreate):
    db = SessionLocal()
    db_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        reporter_email=ticket.reporter_email,
        status="OPEN",
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    db.close()
    return db_ticket


@app.get("/api/tickets", response_model=List[TicketResponse])
def list_tickets():
    db = SessionLocal()
    tickets = db.query(Ticket).all()
    db.close()
    return tickets


class StatusUpdate(BaseModel):
    status: str


@app.patch("/api/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: int, status_update: StatusUpdate):
    db = SessionLocal()
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        db.close()
        return {"error": "Ticket not found"}
    ticket.status = status_update.status.upper()
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    db.close()
    return {"message": f"Ticket {ticket_id} updated to {status_update.status}"}


@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(ticket_id: int):
    db = SessionLocal()
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        db.close()
        return {"error": "Ticket not found"}

    db.delete(ticket)
    db.commit()
    db.close()
    return {"message": f"Ticket {ticket_id} deleted successfully"}


@app.delete("/api/tickets")
def delete_all_tickets():
    db = SessionLocal()
    try:
        # Get count of tickets before deletion
        ticket_count = db.query(Ticket).count()

        # Delete all tickets
        db.query(Ticket).delete()
        db.commit()

        return {"message": f"Successfully deleted all {ticket_count} tickets"}
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to delete tickets: {str(e)}"}
    finally:
        db.close()
