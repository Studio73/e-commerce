FROM python:3.11-slim-buster
RUN apt update && apt install -y git
RUN useradd -md /home/runner -s /bin/bash runner
COPY requirements.txt /requirements.txt
RUN pip install "cpython<3.0.0" pyyaml==5.4.1 --no-build-isolation
RUN pip install -r /requirements.txt
USER runner
COPY --chown=runner ssh_config /home/runner/.ssh/config
RUN ssh-keyscan github.com >> $HOME/.ssh/known_hosts
RUN ssh-keyscan ssh.github.com >> $HOME/.ssh/known_hosts
RUN git config --global user.email "113453776+leonidas73[bot]@users.noreply.github.com" && \
    git config --global user.name "leonidas73[bot]" && \
    git config --global safe.directory '*'
COPY --chown=runner entrypoint.py /entrypoint.py
ENTRYPOINT ["python", "/entrypoint.py"]
