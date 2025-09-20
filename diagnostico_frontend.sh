#!/bin/bash

echo "=========================================="
echo "🔍 DIAGNÓSTICO FRONTEND INTERACTIVIDAD"
echo "=========================================="

# 1. Verificar archivos frontend en el contenedor nginx
echo "=== 1. ARCHIVOS FRONTEND EN NGINX ==="
docker exec verificacion-nginx ls -la /usr/share/nginx/html/

echo ""
echo "=== 2. TAMAÑO DE SCRIPT.JS ==="
docker exec verificacion-nginx wc -c /usr/share/nginx/html/script.js

echo ""
echo "=== 3. PRIMERAS 10 LÍNEAS DE SCRIPT.JS ==="
docker exec verificacion-nginx head -10 /usr/share/nginx/html/script.js

echo ""
echo "=== 4. VERIFICAR SI currentStep = 0 ==="
docker exec verificacion-nginx grep -n "currentStep = 0" /usr/share/nginx/html/script.js

echo ""
echo "=== 5. VERIFICAR FUNCIÓN updateStepVisibility ==="
docker exec verificacion-nginx grep -A 5 "updateStepVisibility" /usr/share/nginx/html/script.js

echo ""
echo "=== 6. VERIFICAR LOGS NGINX PARA ERRORES ==="
docker-compose -f docker-compose.oracle_arm64.yml logs nginx --tail=20

echo ""
echo "=== 7. PROBAR ACCESO A SCRIPT.JS ==="
curl -I http://localhost/script.js

echo ""
echo "=== 8. VERIFICAR CONTENIDO DE INDEX.HTML ==="
docker exec verificacion-nginx head -20 /usr/share/nginx/html/index.html

echo ""
echo "=== 9. VERIFICAR CONSOLA DEL NAVEGADOR ==="
echo "Abre http://158.179.210.136/ en tu navegador y:"
echo "1. Presiona F12 para abrir DevTools"
echo "2. Ve a la pestaña Console"
echo "3. Recarga la página"
echo "4. Copia y pega aquí cualquier error que aparezca"

echo ""
echo "=== 10. VERIFICAR SI HAY ERRORES JAVASCRIPT ==="
echo "Ejecuta en la consola del navegador:"
echo "console.log('Script cargado:', typeof MadridVerificationSystem);"
echo "console.log('currentStep:', window.madridSystem?.currentStep);"
