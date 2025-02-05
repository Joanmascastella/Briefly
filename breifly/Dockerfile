# Use Playwright's official image (includes required dependencies)
FROM mcr.microsoft.com/playwright/python:v1.40.0

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Fix missing dependencies issue)
RUN playwright install --with-deps

# Apply Django migrations & collect static files
RUN python manage.py migrate && python manage.py collectstatic --noinput

# Expose port for Render (default Django port is 8000)
EXPOSE 8000

# Start Gunicorn server
CMD ["gunicorn", "breifly.wsgi:application", "--bind", "0.0.0.0:8000"]