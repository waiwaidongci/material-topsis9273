from datetime import datetime
from sqlalchemy import String,ForeignKey,UniqueConstraint,DateTime,JSON
from sqlalchemy.dialects.mysql import DOUBLE
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class RetestRecord(Base):
    __tablename__='retest_records'
    id:Mapped[int]=mapped_column(primary_key=True)
    note_id:Mapped[int]=mapped_column(ForeignKey('trial_notes.id'))
    metric:Mapped[str]=mapped_column(String(30))
    sample_code:Mapped[str]=mapped_column(String(40))
    value:Mapped[float|None]=mapped_column(DOUBLE(asdecimal=False),nullable=True)
    unit:Mapped[str]=mapped_column(String(50))
    batch:Mapped[str]=mapped_column(String(100),default='')
    submitted_by:Mapped[str]=mapped_column(String(140),default='')
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    __table_args__=(UniqueConstraint('note_id','metric','sample_code'),)
class RetestAnalysis(Base):
    __tablename__='retest_analyses'
    id:Mapped[int]=mapped_column(primary_key=True)
    note_id:Mapped[int]=mapped_column(ForeignKey('trial_notes.id'))
    version:Mapped[int]=mapped_column()
    created_by:Mapped[str]=mapped_column(String(140),default='')
    detail:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    __table_args__=(UniqueConstraint('note_id','version'),)
