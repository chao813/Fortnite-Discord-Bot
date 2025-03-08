FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt /app

# Install prerequisite packages and dependencies
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir wheel bitstring pycryptodome \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 5000

ENV FLASK_APP=fortnite_bot.py

CMD ["flask", "run", "--host=0.0.0.0"]
