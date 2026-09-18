FROM python:3.11-slim

WORKDIR /app

# pyzbar needs libzbar0 installed at the system level to actually decode
# qr codes - without this, qr-based check-in would fail silently
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# folders the app writes generated files into - created here so they
# exist even on a completely fresh container
RUN mkdir -p generated_files/certificates generated_files/tickets generated_files/qr_codes logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]