FROM python:3

LABEL maintainer="adhatwalia@my.bcit.ca"

RUN mkdir -p /app/logs/anomaly_detector /app/data/anomaly_detector

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN chmod -R 777 /app/logs /app/data && \
    chown -R nobody:nogroup /app

USER nobody

EXPOSE 8120

ENTRYPOINT ["python"]
CMD ["app.py"]
