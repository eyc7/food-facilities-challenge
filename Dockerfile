# Use official Python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Expose port Flask runs on
ENV PORT 8080

# Run the app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]