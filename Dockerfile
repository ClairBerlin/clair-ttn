FROM python:3
WORKDIR /opt/clairttn
COPY . .
RUN pip3 install .
CMD clair-ttn
