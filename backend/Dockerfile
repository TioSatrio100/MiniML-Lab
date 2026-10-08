FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    SANDBOX=subprocess

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend/ backend/
RUN mkdir -p storage

EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]

# Docker-mode sandbox inside this container needs the docker CLI + socket mount:
#   build stage: curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.5.1.tgz | tar -xz -C /usr/local/bin --strip-components=1 docker/docker
#   compose:     volumes: [/var/run/docker.sock:/var/run/docker.sock]
#   and host must resolve the same tmp paths — see SETUP.md (Linux only).
