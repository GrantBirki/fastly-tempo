FROM python:3.9.2-slim

WORKDIR /usr/src/app

RUN pip install requests

COPY . .

CMD ["python", "app.py"]