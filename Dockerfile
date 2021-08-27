FROM python:3-slim
WORKDIR /opt/clairttn
COPY . .
RUN pip3 install .
CMD clair-ttn
