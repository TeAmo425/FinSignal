FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only torch to avoid downloading CUDA binaries (~1.5GB saved)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

# Install tradingagents from GitHub (excluded from upload to save size)
RUN pip install --no-cache-dir git+https://github.com/TauricResearch/TradingAgents.git

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
