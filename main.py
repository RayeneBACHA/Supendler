from fastapi import FastAPI

from app.routers import (
    public_transport,
    route_options,
    stops,
    transport
)

app = FastAPI(
    title="Smart Transport API",
    version="0.1.0"
)

app.include_router(stops.router)
app.include_router(transport.router)
app.include_router(public_transport.router)
app.include_router(route_options.router)

@app.get("/")
def home():
    return {
        "message": "Smart Transport API is running",
        "version": "0.1.0"
    }