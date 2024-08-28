FROM python:3.12-slim

WORKDIR /code

COPY visualization-api/ /code/app

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

EXPOSE 80

CMD ["fastapi", "run", "app/main.py", "--port", "80"]