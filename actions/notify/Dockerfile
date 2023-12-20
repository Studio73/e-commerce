FROM python:3.11-slim-buster
RUN pip install requests
COPY entrypoint.py /entrypoint.py
ENTRYPOINT ["python", "/entrypoint.py"]
