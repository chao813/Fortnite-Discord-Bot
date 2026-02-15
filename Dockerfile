FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .

# Install prerequisite packages and dependencies
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir wheel bitstring pycryptodome \
    && pip install --no-cache-dir --no-build-isolation -r requirements.txt

COPY . .

EXPOSE 5100

CMD ["python3", "__main__.py"]
