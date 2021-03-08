FROM python:3.9.2-alpine

RUN pip install --upgrade pip

RUN adduser -D nonroot
RUN mkdir /home/app/ && chown -R nonroot:nonroot /home/app
WORKDIR /home/app
USER nonroot

COPY --chown=nonroot:nonroot . .

RUN pip install --user --no-warn-script-location -r requirements.txt 
RUN export PYTHONPATH="${PYTHONPATH}:/home/nonroot/.local/bin"

CMD ["python", "app.py"]