from typing import List
from pydantic import BaseModel, Field


class Education(BaseModel):
    school: str
    degree: str
    field: str


class JobVector(BaseModel):
    org: str
    title: str
    summary: str


class AIInferredProfile(BaseModel):
    name: str
    headline: str
    location: str
    current_title: str
    current_org: str
    seniority: str
    skills: List[str]
    years_experience: int
    worked_at_startup: bool
    education: List[Education]
    job_vectors: List[JobVector]