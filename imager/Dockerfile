# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /

# Copy the current directory contents into the container at /imager
COPY imager /imager

# Copy the settings file
COPY shared_settings.py /

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /imager/requirements.txt

# Run imager.py when the container launches
CMD ["python3", "/imager/imager.py"]
