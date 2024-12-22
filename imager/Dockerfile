# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /

# Copy the current directory contents into the container at /app
COPY . /imager
# Copy the settings file
COPY ../shared_settings.py /

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
# EXPOSE 8080

# Define environment variable
# ENV NAME val

# Run app.py when the container launches
CMD ["python", "/imager/imager.py"]
