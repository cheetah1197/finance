# main.py
from fastapi import FastAPI

# Create an instance of the FastAPI class
app = FastAPI()

# Define a "path operation" using a decorator
@app.get("/")
def read_root():
    """
    This function handles GET requests to the root URL (/).
    It returns a simple JSON message.
    """
    return {"message": "Hello World"}