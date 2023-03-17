# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
FROM ubuntu:22.04

RUN apt update \
    && apt install -y --no-install-recommends python3.10-dev python3-pip git openssh-client gcc libc-dev curl
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update \
    && apt install -y --no-install-recommends gh
RUN mkdir /src /cache
VOLUME ["/src", "/cache"]
ENV PRE_COMMIT_HOME=/cache
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
WORKDIR /src
COPY --chmod="+x" tools.py /usr/local/bin/tools
COPY ssh_config /root/.ssh/config
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts
RUN ssh-keyscan ssh.github.com >> /root/.ssh/known_hosts
RUN git config --global user.email "113453776+leonidas73[bot]@users.noreply.github.com" && \
    git config --global user.name "leonidas73[bot]" && \
    git config --global safe.directory '*'
CMD ["/bin/bash"]
