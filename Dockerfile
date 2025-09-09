#System Image, using python 3.11, keep it like this, change only if conflicts occur
FROM python:3.11-slim

#Author is Subhanshu Dwivedi
LABEL authors="Kami"

WORKDIR /app
#Copying all project files
COPY . .

#System Dependencies if needed, add more
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/* \

#Running command to install all requirements
RUN pip install --no-cache-dir -r requirements.txt

#Exposed to port 5500
EXPOSE 5000

# Run your app.py
CMD ["python", "app.py"]