# Use official Python runtime as base image
FROM python:3.10-slim

# Set working directory in container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files into container
COPY . .

# Expose port 8000
EXPOSE 8000

# Default command to run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]