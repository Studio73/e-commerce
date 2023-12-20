FROM r.studio73.es/cache/python:3.11-slim-buster
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
COPY entrypoint.py /entrypoint.py
ENTRYPOINT ["python", "/entrypoint.py"]
