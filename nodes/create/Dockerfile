FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY create_viz.py .

CMD ["python", "-u","/app/create_viz.py"]