FROM python:3.12

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy application
COPY . .
ENTRYPOINT ["python3", "-u", "app.py"]