# get python
FROM python:latest

# set working directory in the container
WORKDIR /app

# install dependencies
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the scripts
COPY . /app

# start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]