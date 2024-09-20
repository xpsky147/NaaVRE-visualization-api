# FROM python:3.12-slim

# WORKDIR /code

# COPY visualization-api/ /code/app

# RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# EXPOSE 80

# CMD ["fastapi", "run", "app/main.py", "--port", "80"]

FROM python:3.12-slim

WORKDIR /code

COPY ./requirements.txt /code/
COPY ./visualization-api/app /code/app

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]