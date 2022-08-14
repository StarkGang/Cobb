FROM python:3.10
WORKDIR .
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install -r requirements.txt >/dev/null
COPY . .
CMD ["python3", "-m", "Cobb"]
