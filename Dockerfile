# Use the official Python image  
FROM python:3.9-slim  
 
# Set the working directory  
WORKDIR /app  
 
# Copy requirements and install them  
COPY requirements.txt .  
RUN pip install -r requirements.txt  
 
# Copy the rest of the application code  
COPY . .  
 
# Expose the port the app runs on  
EXPOSE 5000  
 
# Command to run your application  
CMD ["python", "app.py"]
