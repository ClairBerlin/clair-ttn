FROM python:3-slim
WORKDIR /opt/clairttn
COPY . .
RUN pip3 install .
# interval must be longer than the sleep period in clairttn.py
HEALTHCHECK --interval=5s --timeout=1s --retries=3 \
    CMD ./healthcheck.sh
CMD clair-ttn
