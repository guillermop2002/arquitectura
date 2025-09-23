#!/bin/bash
# Script de monitoreo de espacio en disco
# Se ejecuta cada 5 minutos para verificar el uso de disco

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Función para obtener uso de disco
get_disk_usage() {
    df / | awk 'NR==2 {print $5}' | sed 's/%//'
}

# Función para limpiar si es necesario
cleanup_if_needed() {
    local usage=$1
    
    if [ "$usage" -gt 85 ]; then
        echo -e "${RED}⚠️ Uso de disco crítico: ${usage}%${NC}"
        echo -e "${YELLOW}🧹 Ejecutando limpieza automática...${NC}"
        
        # Limpiar archivos temporales
        find /tmp -type f -mtime +0 -delete 2>/dev/null || true
        find /var/tmp -type f -mtime +0 -delete 2>/dev/null || true
        
        # Limpiar logs del sistema
        find /var/log -name "*.log" -type f -mtime +1 -delete 2>/dev/null || true
        find /var/log -name "*.log.*" -type f -mtime +1 -delete 2>/dev/null || true
        
        # Limpiar directorios de la aplicación
        find /app/uploads -name "session_*" -type d -mtime +0 -exec rm -rf {} + 2>/dev/null || true
        find /app/temp -type f -mtime +0 -delete 2>/dev/null || true
        find /app/analysis_results -type f -mtime +0 -delete 2>/dev/null || true
        find /app/logs -name "*.log" -type f -mtime +0 -delete 2>/dev/null || true
        find /app/logs -name "session_*.json" -type f -mtime +0 -delete 2>/dev/null || true
        
        # Limpiar cache de Python
        find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        find /app -name "*.pyc" -type f -delete 2>/dev/null || true
        find /app -name "*.pyo" -type f -delete 2>/dev/null || true
        
        # Limpiar cache de pip
        pip cache purge 2>/dev/null || true
        
        # Limpiar directorios vacíos
        find /app -type d -empty -delete 2>/dev/null || true
        
        echo -e "${GREEN}✅ Limpieza automática completada${NC}"
        
        # Verificar uso después de limpieza
        new_usage=$(get_disk_usage)
        echo -e "${BLUE}📊 Uso de disco después de limpieza: ${new_usage}%${NC}"
        
        # Si sigue siendo crítico, limpiar Docker
        if [ "$new_usage" -gt 85 ]; then
            echo -e "${YELLOW}🐳 Limpieza de Docker necesaria...${NC}"
            docker system prune -a -f --volumes 2>/dev/null || true
            docker builder prune -a -f 2>/dev/null || true
            
            final_usage=$(get_disk_usage)
            echo -e "${BLUE}📊 Uso de disco final: ${final_usage}%${NC}"
        fi
        
    elif [ "$usage" -gt 70 ]; then
        echo -e "${YELLOW}⚠️ Uso de disco alto: ${usage}%${NC}"
        echo -e "${BLUE}💡 Considerando limpieza preventiva...${NC}"
        
        # Limpieza preventiva suave
        find /app/temp -type f -mtime +0 -delete 2>/dev/null || true
        find /app/logs -name "*.log" -type f -mtime +0 -delete 2>/dev/null || true
        
    else
        echo -e "${GREEN}✅ Uso de disco normal: ${usage}%${NC}"
    fi
}

# Función principal
main() {
    echo -e "${BLUE}🔍 Verificando espacio en disco...${NC}"
    
    # Obtener uso actual
    usage=$(get_disk_usage)
    
    # Mostrar estado actual
    echo -e "${BLUE}📊 Estado actual del disco:${NC}"
    df -h / | head -2
    
    # Limpiar si es necesario
    cleanup_if_needed $usage
    
    # Mostrar estado final
    echo -e "${BLUE}📊 Estado final del disco:${NC}"
    df -h / | head -2
    
    echo -e "${GREEN}✅ Monitoreo completado${NC}"
}

# Ejecutar función principal
main "$@"
