# Use Playwright's official Docker image (includes required dependencies)
FROM mcr.microsoft.com/playwright/python:v1.40.0

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Change into 'breifly' directory
WORKDIR /app/breifly

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Fix missing dependencies issue)
RUN playwright install --with-deps

# Ensure the media directory exists
RUN mkdir -p /app/media && chmod -R 777 /app/media

# Expose port for Render (default Django port is 8000)
EXPOSE 8000

# Start Gunicorn server & run migrations at runtime instead of build time
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn breifly.wsgi:application --bind 0.0.0.0:8000"]