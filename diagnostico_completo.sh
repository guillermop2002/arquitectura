#!/bin/bash

echo "=========================================="
echo "🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA"
echo "=========================================="

# 1. Estado de contenedores
echo "=== 1. ESTADO DE CONTENEDORES ==="
docker-compose -f docker-compose.oracle_arm64.yml ps

# 2. Verificar logs de Nginx
echo ""
echo "=== 2. LOGS NGINX (últimas 20 líneas) ==="
docker-compose -f docker-compose.oracle_arm64.yml logs --tail=20 nginx

# 3. Verificar logs de la aplicación
echo ""
echo "=== 3. LOGS APP (últimas 30 líneas) ==="
docker-compose -f docker-compose.oracle_arm64.yml logs --tail=30 app

# 4. Verificar conectividad interna
echo ""
echo "=== 4. CONECTIVIDAD INTERNA ==="
echo "Probando Nginx interno:"
docker exec verificacion-nginx curl -I http://localhost:80 2>/dev/null || echo "❌ Nginx no responde"

echo ""
echo "Probando App interna:"
docker exec verificacion-app curl -I http://localhost:5000/health 2>/dev/null || echo "❌ App no responde"

# 5. Verificar archivos estáticos
echo ""
echo "=== 5. ARCHIVOS ESTÁTICOS ==="
echo "Verificando archivos en Nginx:"
docker exec verificacion-nginx ls -la /usr/share/nginx/html/ | head -10

echo ""
echo "Verificando index.html:"
docker exec verificacion-nginx head -20 /usr/share/nginx/html/index.html

# 6. Verificar JavaScript
echo ""
echo "=== 6. JAVASCRIPT ==="
echo "Verificando script.js:"
docker exec verificacion-nginx head -20 /usr/share/nginx/html/script.js

# 7. Verificar CSS
echo ""
echo "=== 7. CSS ==="
echo "Verificando styles.css:"
docker exec verificacion-nginx head -10 /usr/share/nginx/html/styles.css

# 8. Probar endpoints de la API
echo ""
echo "=== 8. ENDPOINTS API ==="
echo "Probando health endpoint:"
curl -s http://localhost/health | head -5 || echo "❌ Health endpoint no responde"

echo ""
echo "Probando API base:"
curl -s http://localhost/api/health | head -5 || echo "❌ API base no responde"

# 9. Verificar configuración de Nginx
echo ""
echo "=== 9. CONFIGURACIÓN NGINX ==="
docker exec verificacion-nginx cat /etc/nginx/nginx.conf | grep -A 10 -B 5 "location"

# 10. Verificar puertos
echo ""
echo "=== 10. PUERTOS ==="
netstat -tlnp | grep :80 || echo "Puerto 80 no encontrado"
netstat -tlnp | grep :5000 || echo "Puerto 5000 no encontrado"

echo ""
echo "=========================================="
echo "🎯 DIAGNÓSTICO COMPLETADO"
echo "=========================================="
