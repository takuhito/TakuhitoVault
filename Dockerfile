# 本番環境用Dockerfile
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY receipt-processor/ ./receipt-processor/
COPY config/ ./config/
COPY utils.py .

# 環境変数を設定
ENV PYTHONPATH=/app

# アプリケーションを実行
CMD ["python", "receipt-processor/main.py"]
