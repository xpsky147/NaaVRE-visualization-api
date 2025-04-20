FROM python:3.12-slim

WORKDIR /app

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip config set install.trusted-host mirrors.aliyun.com

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY compute.py .

RUN chmod +x compute.py

ENTRYPOINT ["python", "compute.py"]