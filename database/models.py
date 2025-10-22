from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Job(Base):
    """Main job listings table with historical tracking."""
    
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String(255), unique=True, nullable=False)  # Seek job ID
    title = Column(String(500), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    salary_range = Column(String(100))
    job_type = Column(String(50))  # Full-time, Part-time, Contract, etc.
    description = Column(Text)
    url = Column(String(1000))
    category = Column(String(100))  # Classified by LLM
    skills = Column(JSON)  # Extracted skills as JSON array
    first_seen_date = Column(DateTime, default=datetime.utcnow)
    last_seen_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    snapshots = relationship("JobSnapshot", back_populates="job")
    
    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.title}', company='{self.company}')>"

class JobSnapshot(Base):
    """Historical snapshots for tracking job changes."""
    
    __tablename__ = 'job_snapshots'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    snapshot_date = Column(DateTime, default=datetime.utcnow)
    field_changes = Column(JSON)  # Track what fields changed
    snapshot_data = Column(JSON)  # Full job data at this point
    
    # Relationships
    job = relationship("Job", back_populates="snapshots")
    
    def __repr__(self):
        return f"<JobSnapshot(id={self.id}, job_id={self.job_id}, date={self.snapshot_date})>"

class ScrapeLog(Base):
    """Track scraping runs and statistics."""
    
    __tablename__ = 'scrape_logs'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)  # 'seek', 'linkedin', etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    jobs_found = Column(Integer, default=0)
    jobs_new = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    jobs_removed = Column(Integer, default=0)
    status = Column(String(20), default='success')  # 'success', 'error', 'partial'
    error_message = Column(Text)
    duration_seconds = Column(Numeric(10, 2))
    
    def __repr__(self):
        return f"<ScrapeLog(id={self.id}, source='{self.source}', status='{self.status}')>"
