from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    retries: int
    status: str

class IngestURLRequest(BaseModel):
    urls: list[HttpUrl] = Field(..., min_length=1, max_length=10)

class FeedbackRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    answer: str = Field(..., min_length=1)
    rating: str = Field(..., pattern="^(up|down)$")
    comment: Optional[str] = Field(default=None, max_length=2000)
