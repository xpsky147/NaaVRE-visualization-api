FROM python:3.12-slim
WORKDIR /app
COPY data-prep.py .
RUN pip install ucimlrepo pandas
CMD ["python", "data-prep.py", "/workdir/iris.csv"]