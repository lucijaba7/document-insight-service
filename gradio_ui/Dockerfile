FROM python:3.13.2-slim

WORKDIR /ui

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

WORKDIR /ui/app

EXPOSE 7860

CMD ["python", "app.py"]
