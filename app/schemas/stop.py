from pydantic import BaseModel

class Stop(BaseModel):
    name: str
    city: str

class StopResponse(Stop):
    id: int