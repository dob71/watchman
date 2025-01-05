# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /

# Copy the current directory contents into the container at /orchestrator
COPY orchestrator /orchestrator
COPY llm /llm

# Copy the settings file
COPY shared_settings.py /

COPY requirements.txt /

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Install necessary tools (curl, bash)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

#RUN ollama pull llama3.2-vision:11b-instruct-q4_K_M

# Run orchestrator.py when the container launches
CMD ["python3", "-u", "/orchestrator/orchestrator.py"]