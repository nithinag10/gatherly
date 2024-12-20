FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libmariadb-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
EXPOSE 8080

# Use shell form so $PORT is expanded
CMD sh -c "gunicorn --bind 0.0.0.0:$PORT app:app --log-level debug --access-logfile - --error-logfile -"

