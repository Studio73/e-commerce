# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
FROM ubuntu:22.04

RUN apt update \
    && apt install -y --no-install-recommends python3.10-dev python3-pip git openssh-client gcc libc-dev curl
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update \
    && apt install -y --no-install-recommends gh
RUN mkdir /src
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
WORKDIR /src
COPY entrypoint.py /entrypoint.py
COPY ssh_config /root/.ssh/config
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts
RUN ssh-keyscan ssh.github.com >> /root/.ssh/known_hosts
ENTRYPOINT ["python3", "/entrypoint.py"]
CMD ["/bin/bash"]
