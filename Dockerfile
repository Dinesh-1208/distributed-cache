FROM python:3.11-slim

WORKDIR /app

# Copy all source files
COPY *.py ./

# No extra pip dependencies needed — stdlib only (sqlite3 is built-in)

# Default command (overridden by docker-compose per service)
CMD ["python", "coordinator.py"]
