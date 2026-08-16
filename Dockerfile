FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY headless.py .
COPY gui.py .
COPY . .

CMD ["sh", "-c", "python headless.py && python web_app.py"]