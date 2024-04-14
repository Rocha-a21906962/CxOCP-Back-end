FROM python:3.11-slim

WORKDIR /app

COPY pizza_bussiness_process.csv /app/

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY . /app/

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]

# docker build -t backend-image . (in folder pls!)
# docker run -d -p 5000:5000 --name backend backend-image