#!/bin/bash

# Script para entrenar el modelo de Rasa

echo "🤖 Entrenando modelo de Rasa..."

# Navegar al directorio de Rasa
cd rasa_bot

# Crear directorio de modelos si no existe
mkdir -p models

# Entrenar el modelo
echo "📚 Entrenando modelo con los datos de ejemplo..."
rasa train

# Verificar que el modelo se creó
if [ -f "models/*.tar.gz" ]; then
    echo "✅ Modelo entrenado exitosamente"
    ls -la models/
else
    echo "❌ Error al entrenar el modelo"
    exit 1
fi

echo "🎉 Entrenamiento completado"
