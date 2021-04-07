FROM python:3.9.4-alpine3.13

# upgrade pip
RUN pip install --upgrade pip

# create nonroot user
RUN adduser -D nonroot
RUN mkdir /home/app/ && chown -R nonroot:nonroot /home/app
WORKDIR /home/app
USER nonroot

# requirements.txt
COPY --chown=nonroot:nonroot requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt 
RUN export PYTHONPATH="${PYTHONPATH}:/home/nonroot/.local/bin"

# app.py
COPY --chown=nonroot:nonroot app.py .

CMD ["python", "app.py"]