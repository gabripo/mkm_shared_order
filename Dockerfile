FROM python:3.13.3

ENV DockerHOME=/home/mtgbillsplitter
RUN mkdir -p ${DockerHOME}
WORKDIR ${DockerHOME}
RUN git clone https://github.com/gabripo/mkm_shared_order.git ${DockerHOME}

RUN pip install -r requirements.txt
RUN git submodule update --init --recursive
RUN pip install gunicorn

ENV TargetPort=3000
EXPOSE ${TargetPort}/udp
EXPOSE ${TargetPort}/tcp

ENV APP_IN_DOCKER=Yes

# ensure Python prints are catched when created - and not buffered
ENV PYTHONUNBUFFERED=TRUE

# entrypoint with Flask only - no gunicorn
# ENTRYPOINT [ "python" ]
# CMD ["flask_app.py"]

# entrypoint with gunicorn
ENV NumWorkers=1
ENV NumThreads=1
ENV WorkerTimeoutSeconds=3600
ENTRYPOINT gunicorn --bind 0.0.0.0:${TargetPort} flask_app:app -w ${NumWorkers} --threads ${NumThreads} --timeout ${WorkerTimeoutSeconds}