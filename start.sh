#!/bin/sh
set -eu
cd "$(dirname "$0")"
if ! command -v docker >/dev/null 2>&1; then
  if [ -x /Applications/Docker.app/Contents/Resources/bin/docker ]; then
    PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
    export PATH
  else
    echo 'Docker is required. Install and open Docker Desktop: https://www.docker.com/products/docker-desktop/'
    exit 1
  fi
fi
if ! docker info >/dev/null 2>&1; then
  echo 'Open Docker Desktop, wait for its engine to start, then run ./start.sh again.'
  exit 1
fi
if [ ! -f .env ]; then
  umask 077
  cp .env.example .env
  echo 'Created private .env. Set GRAFANA_ADMIN_USER and GRAFANA_ADMIN_PASSWORD, then run ./start.sh again.'
  exit 1
fi
docker compose config --quiet
docker compose up -d --build
address=$(docker compose port grafana 3000)
url="http://$address"
echo "Waiting for Grafana at $url ..."
attempt=0
until curl --fail --silent --max-time 3 "$url/api/health" >/dev/null; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    echo 'Grafana did not become ready. Service status and recent logs:'
    docker compose ps
    docker compose logs --tail=40 grafana prometheus weather
    exit 1
  fi
  sleep 2
done
echo "Grafana is ready: $url/d/three-city-weather"
echo 'Log in using the credentials you configured privately in .env.'
