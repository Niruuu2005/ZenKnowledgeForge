#!/bin/bash
# Script to pull all required Ollama models
# Run this after starting the Ollama service

set -e

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

echo "🚀 ZenKnowledgeForge Model Downloader"
echo "======================================"
echo ""
echo "This will download ~35GB of models. Ensure you have sufficient disk space."
echo ""

models=(
    "llama3.1:8b-instruct-q4_K_M"
    "mistral-nemo:12b-instruct-q4_K_M"
    "qwen2.5:7b-instruct-q4_K_M"
    "gemma2:9b-instruct-q4_K_M"
    "phi3.5:3.8b-mini-instruct-q4_K_M"
    "qwen2.5:14b-instruct-q4_K_M"
)

echo "Models to download:"
for model in "${models[@]}"; do
    echo "  - $model"
done
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

echo ""
echo "📥 Starting downloads..."
echo ""

for model in "${models[@]}"; do
    echo "🔄 Pulling $model..."
    if ollama pull "$model"; then
        echo "✅ $model downloaded successfully"
    else
        echo "❌ Failed to download $model"
        exit 1
    fi
    echo ""
done

echo "🎉 All models downloaded successfully!"
echo ""
echo "You can now run: python -m zen \"your brief here\""
