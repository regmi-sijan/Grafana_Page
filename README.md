# Three City Weather — Grafana Dashboard

A local weather dashboard for **Round Rock, Texas**, **Athens, Ohio**, and **Towson, Maryland**, near Baltimore. It automatically downloads weather estimates from Open-Meteo, stores readings in Prometheus, and displays them in Grafana.

## What it does

- Displays temperature, feels-like temperature, relative humidity, wind speed, wind gusts, precipitation, cloud cover, and readable weather conditions.
- Compares cities in temperature, humidity, wind, and precipitation charts, with a city filter.
- Refreshes the dashboard every **10 seconds**, adjustable from Grafana.
- Downloads weather every **5 minutes**, adjustable through configuration.
- Shows collector availability, download success, time since download, and age of the weather estimate.
- Keeps up to **30 days** of collected readings in a persistent Prometheus volume.
- Provisions the dashboard and data source automatically, with no manual dashboard import.

## Usefulness

Quickly compare conditions across places you care about, spot weather trends, and learn how an API, a metrics database, and Grafana work together. Useful for everyday planning and a small observability portfolio project.

## How it works

```text
Open-Meteo HTTPS API → Python collector → Prometheus → Grafana → Browser
                       download: 5 min   scrape: 10s   refresh: 10s
```

Grafana displays the data; Prometheus stores it; the collector downloads and validates it. Opening the browser URL alone does not start these services.

## Dependencies

| Dependency | Purpose | Required on your computer? |
| --- | --- | --- |
| Git | Clone the project | Yes, unless downloading a ZIP |
| Docker Desktop with Docker Compose v2 or newer | Run all three services on macOS/Windows | Yes |
| Docker Engine with the Compose plugin | Alternative on Linux | Yes, if not using Docker Desktop |
| Internet access | Pull container images and download weather | Yes |
| Modern web browser | View Grafana | Yes |
| POSIX shell and curl | Run `start.sh` and its readiness check | For the helper script |
| Python 3.10+ | Run tests or the collector outside Docker | Optional; 3.13 is used in Docker and CI |

Containers install their own runtime dependencies. You do **not** need local Grafana, Prometheus, Python packages, Node.js, or a weather API key for this setup. The collector uses Python's standard library only.

Container versions are pinned to Grafana **12.1.0**, Prometheus **3.5.0**, and Python **3.13-slim**. The first run downloads these images. Docker handles the build for Apple Silicon and other supported platforms. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and wait for the engine to finish starting. Linux users can follow the [Docker Engine installation guide](https://docs.docker.com/engine/install/) and [Compose plugin guide](https://docs.docker.com/compose/install/linux/).

## Quick start: macOS or Linux

```sh
git clone https://github.com/regmi-sijan/Grafana_Page.git
cd Grafana_Page
cp .env.example .env
chmod 600 .env
```

Open `.env` in a text editor. Fill in `GRAFANA_ADMIN_USER` and `GRAFANA_ADMIN_PASSWORD` with your own chosen credentials. They are intentionally blank in the template. Use a strong password. Keep `.env` private; it is excluded from Git.

Then run:

```sh
./start.sh
```

The script checks Docker, validates configuration, builds and starts the services, and waits for Grafana's health endpoint before printing the dashboard link. If `.env` does not exist, it creates a private template and stops so you can fill it in.

Open [Three City Weather](http://localhost:3000/d/three-city-weather) and log in using the credentials you chose. Weather should appear within about a minute of startup, depending on network access. Charts begin with an empty history and fill while collection runs.

## Windows / manual startup

With Docker Desktop running in Linux-container mode, use PowerShell:

```powershell
git clone https://github.com/regmi-sijan/Grafana_Page.git
cd Grafana_Page
Copy-Item .env.example .env
notepad .env
# Fill in your chosen credentials, save, and close the editor.
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Open [Grafana](http://localhost:3000/d/three-city-weather) once the services have started. The same Compose commands also work on macOS and Linux; `start.sh` is a convenience helper. Windows users may also run it from WSL with Docker integration enabled.

## Configuration

| Setting | Default | How to change |
| --- | --- | --- |
| Initial Grafana username | No preset value | Fill in `GRAFANA_ADMIN_USER` in private `.env` |
| Initial Grafana password | No preset value | Fill in `GRAFANA_ADMIN_PASSWORD` in private `.env` |
| Grafana port | 3000 | Set `GRAFANA_PORT` in `.env` |
| External weather downloads | 300 seconds | Set `WEATHER_POLL_SECONDS` in `.env`; minimum 60 |
| Dashboard refresh | 10 seconds | Grafana's top-right refresh menu; choose another interval or Off |
| Prometheus scrape | 10 seconds | Edit `scrape_interval` in `prometheus/prometheus.yml` |
| History retention | 30 days | Edit `--storage.tsdb.retention.time` in `compose.yaml` |
| City coordinates | Three configured cities | Edit `collector/locations.json` |

After changing `.env` or Compose configuration, run `docker compose up -d`. After editing the scrape configuration, run `docker compose restart prometheus`. Restart `weather` after changing locations.

For a different saved dashboard refresh default, edit `refresh` in `grafana/dashboards/weather.json`. The allowed dropdown options are in `timepicker.refresh_intervals`. Grafana's minimum interval is set to 5 seconds in Compose.

The current dashboard has cards explicitly named for the three cities. Adding or renaming locations also requires updating those card titles and queries in the dashboard JSON. The comparison charts and city selector discover the collector's city labels automatically.

### Credentials and persistent accounts

There are no preset credentials in the repository. Docker Compose refuses to start if the required credential variables are empty. `.env` is private local configuration; never upload it, database exports, or Docker volume backups to GitHub.

Grafana uses these variables to initialize a **new** database. Editing `.env` does not rename an existing Grafana user or change an existing password. Change an existing account in Grafana's profile/account settings, then update your private `.env` to match. Avoid deleting the data volume to change credentials: that removes Grafana's saved settings.

The Compose file publishes only Grafana, bound to `127.0.0.1`, so it is accessible on the host computer. The collector and Prometheus remain inside Docker's network. This configuration is for local use. Hosting it for other users requires appropriate HTTPS, access controls, and deployment configuration. Publishing the source on GitHub does not publish a live dashboard or upload collected weather history.

## Refresh versus weather updates

Dashboard refresh, download frequency, and source updates are separate. Open-Meteo's current conditions are based on 15-minute weather model data. Refreshing Grafana every 10 seconds queries the latest stored readings; it does not produce new weather estimates every 10 seconds.

The default five-minute downloads for three cities make about 864 API requests per day. The collector enforces at least 60 seconds between collection cycles. Review [Open-Meteo pricing](https://open-meteo.com/en/pricing) and [terms](https://open-meteo.com/en/terms) before changing usage or using this commercially. Its free endpoint is intended for noncommercial use and has usage limits.

## Understanding the readings

- Temperature is Fahrenheit; wind is mph; precipitation is inches.
- Current conditions are model estimates, not measurements from a personal weather station.
- Precipitation is the provider's **current interval amount**, not a daily total. Do not sum repeated scrapes to calculate total rainfall.
- **Age of weather estimate** uses the provider timestamp. **Time since download** uses the last successful download time.
- When a provider request fails, the collector keeps the last successful readings and marks the city's latest download as failed. Those values may be stale; check freshness and availability indicators.
- Each city is collected independently. Failure for one city does not block the others.
- Collector health means its HTTP server is responding; upstream weather availability is shown separately.
- The collector's cache is in memory and clears on restart. Prometheus history and Grafana settings persist in named Docker volumes.
- This setup does not backfill historical weather. Gaps while the computer is asleep or services are stopped remain gaps.

## Running and stopping

```sh
# Start / apply configuration changes
docker compose up -d --build

# Status
docker compose ps

# Recent logs
docker compose logs --tail=100 weather prometheus grafana

# Stop, retaining weather history and Grafana settings
docker compose down

# Restart after opening Docker Desktop
./start.sh
```

Keep Docker running and your computer awake for collection. You may close Terminal and your browser tab. Services use `restart: unless-stopped` and should restart with Docker unless you explicitly stopped them. Always-on collection requires an always-on host.

The `grafana-data` and `prometheus-data` named volumes hold persistent settings and readings. Normal `docker compose down` preserves them. Do not add `--volumes` unless you intentionally want to delete that data.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `ERR_CONNECTION_REFUSED` at localhost | Start Docker, then run `./start.sh`; check `docker compose ps` |
| Docker command is unavailable | Finish Docker Desktop installation and reopen Terminal |
| Docker daemon cannot be reached | Open Docker Desktop and wait until the engine is running |
| macOS installer asks for administrator approval | Complete Docker Desktop's installation prompts on your computer |
| Required credential variable is missing | Fill both credential fields in private `.env` |
| Port 3000 is in use | Set `GRAFANA_PORT=3001`, rerun Compose, and use localhost:3001 |
| Login fails after editing `.env` | Existing accounts live in Grafana's database; environment changes only initialize new databases |
| Panels show no data | Allow a minute, inspect collector logs, and check its dashboard health indicators |
| Source values do not change every 10 seconds | Normal: provider estimates update less often than dashboard refresh |
| Collection stops overnight | The computer may have slept, Docker stopped, or network access failed |
| Editing a provisioned dashboard gets overwritten | Edit the source JSON, or use Grafana's Save as to create a separate dashboard |

## Project structure

```text
.github/workflows/checks.yml          Automated tests and configuration checks
.env.example                         Blank credential template, no secrets
compose.yaml                         Services, networking, and persistent volumes
start.sh                             Startup and readiness helper
collector/
  Dockerfile                         Python collector image
  .dockerignore                      Excludes local artifacts from image builds
  locations.json                     City names and coordinates
  weather.py                         API download, validation, and metrics server
grafana/
  dashboards/weather.json            Dashboard definition
  provisioning/dashboards/weather.yml Automatic dashboard provisioning
  provisioning/datasources/weather.yml Prometheus data source
prometheus/prometheus.yml            Metrics scrape configuration
tests/test_weather.py                Collector and dashboard tests
LICENSE                              Project source license
```

## Development and verification

No pip dependencies are needed. From the project root, with Python 3.10 or newer:

```sh
python3 -m unittest discover -s tests -v
sh -n start.sh
docker compose config --quiet
```

Compose validation requires your private credentials to be configured. Avoid publishing the output of plain `docker compose config`, which expands environment values; use `--quiet` to validate without displaying them.

Tests cover weather-field validation, provider timestamps, stale-data preservation on outages, independent city failures, the default refresh, and unique dashboard panel IDs. GitHub Actions runs tests, shell syntax checks, and Compose validation using disposable credentials generated during the job; no repository secrets are required. Tests use fixtures and do not call the weather provider.

To run only the collector outside Docker:

```sh
python3 collector/weather.py
```

It serves `/metrics` and `/health` on port 8000. This standalone mode binds all interfaces; use it on a trusted development machine. Stop it with Ctrl+C. Running the collector alone does not start Grafana or Prometheus.

## Attribution and licenses

[Weather data by Open-Meteo](https://open-meteo.com/) — see the [API documentation](https://open-meteo.com/en/docs). Weather data is provided under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); retain source attribution when sharing derived dashboards. Provider API service terms are separate from the data license.

This project's original source is MIT licensed; see [LICENSE](LICENSE). Grafana, Prometheus, Python, Docker, and other third-party components retain their own licenses and terms.
