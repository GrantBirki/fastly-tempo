FROM python:3.9.0

WORKDIR /usr/src/app

RUN pip install requests

COPY . .

CMD ["python", "app.py"]