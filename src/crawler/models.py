from sqlalchemy import Column,String,DateTime,Integer,Boolean,Text,UniqueConstraint,ARRAY,func
from datetime import datetime, timezone
from shared.db.base import Base



class JobRecord(Base):
    __tablename__="jobs"
    __table_args__ = (
    UniqueConstraint("external_id", "company", "source_feed", name="uq_job_key"),
)

    id=Column(Integer,primary_key=True,autoincrement=True)
    external_id=Column(String,nullable=False)
    department=Column(String,nullable=True)
    team=Column(String,nullable=True)
    company=Column(String,nullable=False)
    title=Column(String,nullable=False)
    employment_type=Column(String,nullable=True)
    countries=Column(ARRAY(String),nullable=True)
    cities=Column(ARRAY(String),nullable=True)
    is_remote=Column(Boolean,default=False)
    job_url = Column(String, nullable=False)
    apply_url = Column(String, nullable=True)
    source_feed = Column(String, nullable=False)
    is_active=Column(Boolean,default=True)
    description=Column(Text,nullable=True)
    posted_at = Column(DateTime(timezone=True), server_default=func.now())  
    job_updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at =  Column(DateTime(timezone=True), server_default=func.now(),nullable=False)
    updated_at =  Column(DateTime(timezone=True), server_default=func.now(),onupdate=func.now(), nullable=False)
    
    


    