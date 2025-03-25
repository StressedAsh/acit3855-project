FROM python:3

LABEL maintainer="adhatwalia@my.bcit.ca"

RUN mkdir /app

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app


RUN chown -R nobody:nogroup /app
USER nobody

EXPOSE 8090

ENTRYPOINT ["python"]
CMD ["app.py"]
