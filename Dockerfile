# syntax=docker/dockerfile:1.3
FROM python:3.12-bookworm
WORKDIR $USER_HOME
# See https://github.com/pypa/setuptools/issues/3301
# ARG PIP_REQ=>=22 SETUPTOOLS_REQ=<60 \
ARG PIP_REQ=>=22 SETUPTOOLS_REQ=>=75 \
    REQUIREMENTS=requirements/requirements.txt requirements/requirements-dev.txt
ENV REQUIREMENTS=$REQUIREMENTS PIP_REQ=$PIP_REQ SETUPTOOLS_REQ=$SETUPTOOLS_REQ
ADD --chown=app:app lib/ lib/
ADD --chown=app:app src/ src/
ADD --chown=app:app *.py *txt *md *in ./
RUN mkdir requirements
ADD --chown=app:app requirements/requirement* requirements/
RUN #bash -c 'set -ex \
#  && python -m pip install --break-system-packages --no-cache -r <( cat $REQUIREMENTS ) \
#  && chown -Rf $USER_NAME .'

#RUN pip install -r .
#
# final cleanup
RUN \
  set -ex \
  && sed -i -re "s/(python-?)[0-9]\.[0-9]+/\1$PY_VER/g" apt.txt \
  && apt install $(dpkg -l|awk '{print $2}'|grep -v -- -dev|egrep python.?-) \
  && if $(egrep -q "${DEV_DEPENDENCIES_PATTERN}" apt.txt);then \
    apt-get remove --auto-remove --purge \
  $(sed "1,/${DEV_DEPENDENCIES_PATTERN}/ d" apt.txt|grep -v '^#'|tr "\n" " ");\
  fi \
  && rm -rf /var/lib/apt/lists/* /tmp/install
# run settings
ADD --chown=app:app .git/ .git/
ADD --chown=app:app bin/  bin/
#ENTRYPOINT ["/bin/bash"]
