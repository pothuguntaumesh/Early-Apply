from sqlalchemy import Column,Integer,DateTime,func,BigInteger,ARRAY,Text,String,Boolean
from shared.db.base import Base

class UserJobPref(Base):
    __tablename__="user_job_prefs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    email = Column(String,nullable=False)
    user_id = Column(BigInteger, nullable=False)
    roles= Column(ARRAY(Text),nullable=False)
    levels= Column(ARRAY(Text),nullable=False)
    countries= Column(ARRAY(Text),nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)



class JobAlertQueue(Base):

    __tablename__="job_alert_queue"

    id=Column(BigInteger, primary_key=True, autoincrement=True)
    job_id=Column(BigInteger,nullable=False)
    processed=Column(Boolean,nullable=False,default=False,index=True)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at=Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)


class JobAlert(Base):
    __tablename__="job_alerts"
    
    id=Column(BigInteger, primary_key=True, autoincrement=True)
    user_id=Column(BigInteger,nullable=False)
    job_id=Column(BigInteger,nullable=False)
    sent_at=Column(DateTime(timezone=True),nullable=True)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
   





