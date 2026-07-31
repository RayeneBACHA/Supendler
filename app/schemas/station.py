from pydantic import BaseModel

class Station(BaseModel):
    name: str
    city: str