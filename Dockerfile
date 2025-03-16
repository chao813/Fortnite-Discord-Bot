FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt /app

# Install prerequisite packages and dependencies
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir wheel bitstring pycryptodome \
    && pip install --no-cache-dir -r requirements.txt

COPY __main__.py /app/
COPY api /app/api
COPY bot /app/bot
COPY core /app/core

EXPOSE 5100

CMD ["python3", "__main__.py"]
