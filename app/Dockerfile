FROM python:3.11-alpine

RUN python -m pip install --upgrade pip

RUN apk add --no-cache tzdata
RUN cp /usr/share/zoneinfo/Europe/Belgrade /etc/localtime && echo "Europe/Belgrade" > /etc/timezone

RUN mkdir -p /usr/src/app/src

WORKDIR /usr/src/app/src

COPY ./src/ .

RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
