# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install FastAPI and Uvicorn
RUN pip install fastapi uvicorn

# Make port 80 available to the world outside this container
EXPOSE 80

# Run the application:
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]