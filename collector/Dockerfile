FROM python:3.13-slim
WORKDIR /app
COPY weather.py locations.json ./
USER 65534:65534
EXPOSE 8000
CMD ["python", "-u", "weather.py"]
