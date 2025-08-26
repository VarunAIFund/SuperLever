from typing import List
from pydantic import BaseModel


class Education(BaseModel):
    school: str
    degree: str
    field: str


class AIInferredProfile(BaseModel):
    current_title: str
    current_org: str
    seniority: str
    skills: List[str]  #includes programming languages
    years_experience: int #calculated from work history by GPT
    worked_at_startup: bool
    education: List[Education]