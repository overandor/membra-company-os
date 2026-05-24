FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY llm-os/llm_os llm_os/
COPY llm_signal_hunter.py .
COPY app.py .
COPY dashboard.html .

ENV HOST=0.0.0.0
ENV PORT=7860

CMD ["python", "app.py"]
