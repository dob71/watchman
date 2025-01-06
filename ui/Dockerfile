# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /

# Copy the current directory contents into the container at /ui
COPY ui /ui

# Copy the settings file
COPY shared_settings.py /

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /ui/requirements.txt

# Make port available to the world outside this container
EXPOSE 8501

# Run app when the container launches
CMD ["streamlit", "run", "/ui/main.py", "--server.address=0.0.0.0"]