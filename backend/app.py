from fastapi import FastAPI
import uvicorn
from starlette.requests import Request

app = FastAPI()

@app.post("/generate_data")
async def generate_segmentation_data(request: Request):
    return {}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)