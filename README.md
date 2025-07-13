# Backend FastAPI APIs

This is a backend server built with [FastAPI](https://fastapi.tiangolo.com/).

It handles API endpoints for user authentication, file CRUD operations, and chatbot interactions for the frontend application.

## Deployment

You can deploy the app using Docker:

```bash
# Make sure you are inside the project folder
docker build -t backend-image .
```

followed by

```bash
docker run -d -p 6000:6000 --name backend backend-image
```

The API will be available at [http://localhost:6000](http://localhost:6000)

You can view the interactive API documentation at [http://localhost:6000/docs](http://localhost:6000/docs)

## Getting Started (Locally)

First, make sure you are familiar with **Python**.

### Install dependencies

First, make sure you are familiar with **Python** and have it installed.

You need to install the required dependencies:

```bash
pip install -r requirements.txt
```

### Run the FastAPI server

After installing the dependencies, run the FastAPI server using ```main.py```:

```
python main.py
```
