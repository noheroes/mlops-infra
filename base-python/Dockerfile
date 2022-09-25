ARG PY_VERSION="3.8.10"
FROM python:${PY_VERSION}

ENV NB_USER jovyan
ENV NB_UID 1000
ENV NB_PREFIX /
ENV HOME /home/$NB_USER
ENV SHELL /bin/bash

# set shell to bash
SHELL ["/bin/bash", "-c"]

# create user and set required ownership
RUN useradd -M -s /bin/bash -N -u ${NB_UID} ${NB_USER} \
 && mkdir -p ${HOME} \
 && chown -R ${NB_USER}:users ${HOME} \
 && chown -R ${NB_USER}:users /usr/local/bin

# add directory to path
ENV PATH="$PATH:$HOME/.local/bin"

# change to default user
USER ${NB_USER}

# install requirements.txt
COPY --chown=jovyan:users requirements.txt /tmp
RUN python3 -m pip install -r /tmp/requirements.txt --quiet --no-cache-dir \
 && rm -f /tmp/requirements.txt

# change to home directory
WORKDIR $HOME
