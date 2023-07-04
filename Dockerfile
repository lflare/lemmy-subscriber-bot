FROM python:alpine

# Upgrade packages
RUN apk update && \
    apk upgrade

# Install requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Set default lemmy database location
VOLUME [ "/data" ]
ENV LEMMY_DATABASE /data/database.db

# Set entrypoint and command
CMD [ "python3", "bot.py"]

# Add bot.py
COPY bot.py /bot.py
