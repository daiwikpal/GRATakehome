# Data Processing Web System 

A Python-based web system that ingests JSON datasets, processes them asynchronously, and exposes results via a REST API and a browser dashboard. The architecture separates a lightweight HTTP layer (FastAPI) from a horizontally-scalable worker pool (Celery), coordinated by a durable message broker (RabbitMQ) with all task state persisted to PostgreSQL. 
