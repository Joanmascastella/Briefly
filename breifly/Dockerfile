# Use a lightweight official Python image instead of Playwright
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Change into 'breifly' directory
WORKDIR /app/breifly

# Install system dependencies required for feedparser & lxml
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Ensure the media directory exists
RUN mkdir -p /app/media && chmod -R 777 /app/media

# Expose port for Render (default Django port is 8000)
EXPOSE 8000

# Start Gunicorn server & run migrations at runtime instead of build time
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn breifly.wsgi:application --bind 0.0.0.0:8000"]