# # Base image
# FROM python:3.10-slim
# WORKDIR /app
# COPY . .
# RUN pip install --no-cache-dir -r requirement.txt
# COPY . /app/
# EXPOSE 8300
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8300"]
# Base image
FROM python:3.10-slim

WORKDIR /app

# Copy the project files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirement.txt

# Ensure the static directory exists
RUN mkdir -p /app/static

# Expose the port
EXPOSE 8300

# Run migrations and start Django properly
#CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8300"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8300"]
