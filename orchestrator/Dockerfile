# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /

# Copy the current directory contents into the container at /orchestrator
COPY orchestrator /orchestrator

# Copy the settings file
COPY shared_settings.py /

COPY requirements.txt /

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Run orchestrator.py when the container launches
CMD ["python3", "/orchestrator/orchestrator.py"]