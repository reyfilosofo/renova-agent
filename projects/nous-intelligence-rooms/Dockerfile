FROM python:3.13-slim
WORKDIR /app
COPY app /app/app
ENV PORT=8000 HOST=0.0.0.0
EXPOSE 8000
CMD ["python", "app/server.py"]
