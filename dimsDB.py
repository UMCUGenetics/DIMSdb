import uvicorn

from DIMSdb.main import app

if __name__ == "__main__":
    uvicorn.run("dimsDB:app", reload=True)