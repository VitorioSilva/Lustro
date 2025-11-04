#!/bin/bash

set -e

IMAGE_NAME="lustro-backend"
VERSION="1.0.0"
CONTAINER_NAME="lustro-container"
PORT=5000

echo "🛠  Building Docker image ($IMAGE_NAME:$VERSION)..."

# Verifica se Docker está rodando
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker não está rodando. Abra o Docker Desktop e tente novamente."
    exit 1
fi

# Build com BuildKit e exportação local
docker buildx build --load -t $IMAGE_NAME:$VERSION -t $IMAGE_NAME:latest .

echo "✅ Build concluído!"

# Remove container anterior se existir
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "🧹 Removendo container antigo..."
    docker stop $CONTAINER_NAME >/dev/null 2>&1 || true
    docker rm $CONTAINER_NAME >/dev/null 2>&1 || true
fi

# Executa o container com as variáveis do .env
echo "🚀 Iniciando container $CONTAINER_NAME..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:$PORT \
  --env-file .env \
  $IMAGE_NAME:latest

echo "✅ Container iniciado!"
echo "🌐 Acesse: http://localhost:$PORT"
echo ""
echo "📜 Logs da aplicação (Ctrl+C para sair):"
docker logs -f $CONTAINER_NAME