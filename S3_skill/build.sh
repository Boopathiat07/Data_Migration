#!/bin/bash

# Build, tag, and push the Docker image for the user microservice
echo "Building S3 Upload Docker image..."
sudo docker build --no-cache -t s3-uploader .
echo "Tagging S3 Upload Docker image..."
sudo docker tag s3-uploader bhuvaneshj/divum-repo:skill_s3_uploader
echo "Pushing S3 Upload Docker image to repository..."
sudo docker push bhuvaneshj/divum-repo:skill_s3_uploader
