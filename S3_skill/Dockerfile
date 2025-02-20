# Use official Python base image
FROM python:3.12

# Set the working directory inside the container
WORKDIR /app

# Copy individual files (if needed)
COPY main.py /app/
COPY skill_files_to_s3.py /app/
COPY requirements.txt /app/
COPY .env /app/
COPY contenthash_filename.csv /app/
COPY missing_filenames.csv /app/
COPY s3_upload.log /app/
COPY output /app/
#COPY data /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Run the main script
CMD ["python", "/app/main.py"]
