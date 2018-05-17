FROM makinacorpus/geodjango:bionic-py2

ENV DJANGO_SETTINGS_MODULE geotrek.settings.prod
# SET LOCAL_UID, help to use in dev
ARG LOCAL_UID=1000
# Add default SECRET KEY / used for compilemessages
ENV SECRET_KEY temp
# Add default path for log / used for compilemessages
RUN mkdir -p /app/src/var/log

RUN wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py && rm get-pip.py
RUN pip install pip==10.0.1 setuptools==39.1.0 wheel==0.31.0 virtualenv --upgrade
RUN useradd -ms /bin/bash django --uid $LOCAL_UID
RUN mkdir -p /app/src/var/static /app/src/var/extra_static /app/src/var/media /app/src/var/data /app/src/var/cache /app/src/var/log /app/src/var/extra_templates /app/src/var/extra_locale
ADD geotrek /app/src/geotrek
ADD manage.py /app/src/manage.py
ADD bulkimport /app/src/bulkimport
ADD VERSION /app/src/VERSION
ADD .coveragerc /app/src/.coveragerc
RUN chown django:django -R /app
COPY docker/* /usr/local/bin/

USER django

RUN virtualenv /app/venv
ADD requirements.txt /app/src/requirements.txt
RUN /app/venv/bin/pip install --no-cache-dir -r /app/src/requirements.txt

WORKDIR /app/src
# persists compiled locales
RUN ./manage.py compilemessages

EXPOSE 8000

USER root

ENTRYPOINT ["/bin/sh", "-e", "/usr/local/bin/entrypoint.sh"]

CMD ["/bin/sh", "-e", "/usr/local/bin/run.sh"]