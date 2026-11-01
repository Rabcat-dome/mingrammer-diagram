FROM python:3.13-alpine3.22@sha256:e81548ac35b07a3bd4805f275107592ef458b1e893c0e04d45aedaa19416cca5

RUN apk add --no-cache graphviz=12.2.1-r0 fontconfig=2.15.0-r3 \
      font-noto=2025.05.01-r0 font-noto-thai=2025.05.01-r0
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
COPY render_fixture.py server.py ./
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp
USER 10001:10001
ENTRYPOINT ["python", "/app/render_fixture.py"]
