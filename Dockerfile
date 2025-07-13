FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY . /app/

EXPOSE 5671

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5671"]

# docker build -t backend-image . (in folder pls!)
# docker run -d -p 5671:5671 --name backend backend-image
