FROM python:3-slim
WORKDIR /opt/clairttn
COPY . .
RUN pip3 install .
HEALTHCHECK --interval=5s --timeout=1s --retries=3 \
    CMD test -s "/tmp/clair-alive"
CMD clair-ttn
