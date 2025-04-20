FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ streamlit pandas plotly requests

COPY viz_app.py .

EXPOSE 8501

CMD ["streamlit", "run", "viz_app.py", "--server.port=8501", "--server.address=0.0.0.0"]