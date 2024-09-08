FROM python:3.11-slim

WORKDIR /app

# Set PYTHONPATH to include the root of the project
ENV PYTHONPATH=/app:$PYTHONPATH

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 8080

CMD ["python", "run.py"]
