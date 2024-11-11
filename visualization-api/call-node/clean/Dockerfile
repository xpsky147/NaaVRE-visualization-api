FROM python:slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY cleaner.py /app/

CMD ["python", "-u", "/app/cleaner.py"]