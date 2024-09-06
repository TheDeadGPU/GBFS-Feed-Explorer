FROM python:3.12.5

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /code/requirements.txt

COPY ./GBFS-Dashboard.py /code/GBFS-Dashboard.py

CMD ["python","GBFS-Dashboard.py"]