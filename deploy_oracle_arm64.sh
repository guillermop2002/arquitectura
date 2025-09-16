#!/bin/bash

# Script de despliegue para Oracle Cloud ARM64
# Sistema de Verificación Arquitectónica

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
PROJECT_NAME="verificacion-arquitectonica"
REGION="eu-madrid-1"
SHAPE="VM.Standard.A1.Flex"
OCPUS=4
MEMORY_GB=24

# Funciones de logging
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Verificar dependencias
check_dependencies() {
    info "Verificando dependencias..."
    
    if ! command -v oci &> /dev/null; then
        error "OCI CLI no está instalado"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado"
        exit 1
    fi
    
    success "Dependencias verificadas"
}

# Crear instancia
create_instance() {
    info "Creando instancia en Oracle Cloud..."
    
    # Obtener OCID del compartment
    COMPARTMENT_ID=$(oci iam compartment list --query "data[0].id" --raw-output)
    
    # Crear instancia
    INSTANCE_ID=$(oci compute instance launch \
        --compartment-id $COMPARTMENT_ID \
        --availability-domain AD-1 \
        --shape $SHAPE \
        --shape-config '{"ocpus":'$OCPUS',"memoryInGBs":'$MEMORY_GB'}' \
        --source-boot-volume-id ocid1.image.oc1.eu-madrid-1.aaaaaaaaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
        --boot-volume-size-in-gbs 100 \
        --subnet-id $(oci network subnet list --compartment-id $COMPARTMENT_ID --query "data[0].id" --raw-output) \
        --assign-public-ip true \
        --ssh-authorized-keys-file ~/.ssh/id_rsa.pub \
        --display-name $PROJECT_NAME \
        --query "data.id" \
        --raw-output)
    
    success "Instancia creada: $INSTANCE_ID"
    
    # Obtener IP pública
    PUBLIC_IP=$(oci compute instance list-vnics --instance-id $INSTANCE_ID --query "data[0].public-ip" --raw-output)
    
    echo "INSTANCE_ID=$INSTANCE_ID" > .oracle_instance_info
    echo "PUBLIC_IP=$PUBLIC_IP" >> .oracle_instance_info
    
    success "IP Pública: $PUBLIC_IP"
}

# Configurar instancia
setup_instance() {
    source .oracle_instance_info
    
    info "Configurando instancia..."
    
    # Script de configuración
    cat > setup_instance.sh << 'EOF'
#!/bin/bash
sudo apt-get update && sudo apt-get upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo apt-get install -y git curl wget htop
sudo mkdir -p /opt/verification-app
sudo chown $USER:$USER /opt/verification-app
cd /opt/verification-app
git clone https://github.com/guillermop2002/arquitectura.git .
cp env.oracle_arm64.txt .env
chmod +x *.sh
echo "Configuración completada"
EOF

    scp -o StrictHostKeyChecking=no setup_instance.sh ubuntu@$PUBLIC_IP:/tmp/
    ssh -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "chmod +x /tmp/setup_instance.sh && /tmp/setup_instance.sh"
    
    success "Instancia configurada"
}

# Desplegar aplicación
deploy_application() {
    source .oracle_instance_info
    
    info "Desplegando aplicación..."
    
    # Script de despliegue
    cat > deploy_app.sh << 'EOF'
#!/bin/bash
cd /opt/verification-app
docker-compose -f docker-compose.oracle_arm64.yml down --remove-orphans
docker system prune -f
docker-compose -f docker-compose.oracle_arm64.yml up --build -d
sleep 30
docker-compose -f docker-compose.oracle_arm64.yml ps
echo "Aplicación desplegada"
EOF

    scp -o StrictHostKeyChecking=no deploy_app.sh ubuntu@$PUBLIC_IP:/tmp/
    ssh -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "chmod +x /tmp/deploy_app.sh && /tmp/deploy_app.sh"
    
    success "Aplicación desplegada"
}

# Verificar despliegue
verify_deployment() {
    source .oracle_instance_info
    
    info "Verificando despliegue..."
    sleep 60
    
    if curl -s http://$PUBLIC_IP/health | grep -q "healthy"; then
        success "✅ Aplicación funcionando"
    else
        warning "⚠️ Aplicación iniciando"
    fi
    
    success "Despliegue completado"
    echo ""
    echo "🎉 SISTEMA DESPLEGADO"
    echo "===================="
    echo "• Aplicación: http://$PUBLIC_IP"
    echo "• Health: http://$PUBLIC_IP/health"
    echo "• Rasa: http://$PUBLIC_IP:5005"
    echo "• Neo4j: http://$PUBLIC_IP:7474"
}

# Función principal
main() {
    case "${1:-deploy}" in
        "deploy")
            check_dependencies
            create_instance
            setup_instance
            deploy_application
            verify_deployment
            ;;
        "cleanup")
            if [ -f ".oracle_instance_info" ]; then
                source .oracle_instance_info
                oci compute instance terminate --instance-id $INSTANCE_ID --force
                rm -f .oracle_instance_info
            fi
            ;;
        *)
            echo "Uso: $0 [deploy|cleanup]"
            ;;
    esac
}

main "$@"