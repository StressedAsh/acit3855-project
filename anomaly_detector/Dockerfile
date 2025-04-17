FROM python:3

LABEL maintainer="adhatwalia@my.bcit.ca"

RUN mkdir /app /app/logs

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

RUN chmod -R 777 /app/logs

RUN chown -R nobody:nogroup /app
USER nobody

EXPOSE 8080

ENTRYPOINT ["python"]
CMD ["app.py"]
