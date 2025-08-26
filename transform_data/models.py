from typing import List, Optional
from pydantic import BaseModel


class Education(BaseModel):
    degree: str
    field: str
    school: str


class JobVector(BaseModel):
    org: str
    title: str
    summary: str
    vector_id: str


class PersonProfile(BaseModel):
    id: str
    name: str
    location: str
    current_title: str
    current_org: str
    past_orgs: List[str]
    titles: List[str]
    skills: List[str]
    programming_languages: List[str]
    education: List[Education]
    years_experience: int
    worked_at_startup: bool
    job_vectors: List[JobVector]
    tags: List[str]
    confidentiality: str