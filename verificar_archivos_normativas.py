#!/usr/bin/env python3
"""
Script para verificar qué archivos de normativas existen y cuáles faltan
"""

from pathlib import Path
import os

def verificar_archivos_normativas():
    print("🔍 VERIFICACIÓN DE ARCHIVOS DE NORMATIVAS")
    print("=" * 60)
    
    # Definir estructura esperada
    normativas_esperadas = {
        "PGOUM General": "Normativa/PGOUM/pgoum_general.pdf",
        
        # PGOUM por Uso
        "PGOUM Residencial": "Normativa/PGOUM/Usos/pgoum_residencial.pdf",
        "PGOUM Industrial": "Normativa/PGOUM/Usos/pgoum_industrial.pdf",
        "PGOUM Garaje": "Normativa/PGOUM/Usos/pgoum_garaje.pdf",
        "PGOUM Servicios Terciarios": "Normativa/PGOUM/Usos/pgoum_terciario.pdf",
        "PGOUM Dotacional": "Normativa/PGOUM/Usos/pgoum_dotacional.pdf",
        "PGOUM Dotacional Deportivo": "Normativa/PGOUM/Usos/pgoum_dotacional deportivo.pdf",
        
        # PGOUM por Zona
        "Norma Zonal NZ1": "Normativa/PGOUM/Zonas/NZ1.pdf",
        "Norma Zonal NZ2": "Normativa/PGOUM/Zonas/NZ2.pdf",
        "Norma Zonal NZ3": "Normativa/PGOUM/Zonas/NZ3.pdf",
        "Norma Zonal NZ4": "Normativa/PGOUM/Zonas/NZ4.pdf",
        "Norma Zonal NZ5": "Normativa/PGOUM/Zonas/NZ5.pdf",
        "Norma Zonal NZ6": "Normativa/PGOUM/Zonas/NZ6.pdf",
        "Norma Zonal NZ7": "Normativa/PGOUM/Zonas/NZ7.pdf",
        "Norma Zonal NZ8": "Normativa/PGOUM/Zonas/NZ8.pdf",
        "Norma Zonal NZ9": "Normativa/PGOUM/Zonas/NZ9.pdf",
        
        # Documentos Básicos
        "DB-SI": "Normativa/DOCUMENTOS BASICOS/DBSI/DBSI.pdf",
        "Reglamento Instalaciones": "Normativa/DOCUMENTOS BASICOS/DBSI/REGLAMENTO INSTALACIONES.pdf",
    }
    
    archivos_existentes = []
    archivos_faltantes = []
    
    for nombre, ruta in normativas_esperadas.items():
        path = Path(ruta)
        if path.exists():
            size = path.stat().st_size
            archivos_existentes.append((nombre, ruta, size))
            print(f"✅ {nombre}")
            print(f"   📁 {ruta}")
            print(f"   📊 Tamaño: {size:,} bytes ({size/1024/1024:.2f} MB)")
        else:
            archivos_faltantes.append((nombre, ruta))
            print(f"❌ {nombre}")
            print(f"   📁 {ruta}")
            
            # Verificar si el directorio padre existe
            parent_dir = path.parent
            if parent_dir.exists():
                print(f"   📂 Directorio existe: {parent_dir}")
                # Listar archivos en el directorio
                try:
                    files_in_dir = list(parent_dir.glob("*.pdf"))
                    if files_in_dir:
                        print(f"   📄 Archivos PDF encontrados:")
                        for file in files_in_dir:
                            print(f"      - {file.name}")
                    else:
                        print(f"   📄 No se encontraron archivos PDF")
                except Exception as e:
                    print(f"   ❌ Error listando archivos: {e}")
            else:
                print(f"   📂 Directorio NO existe: {parent_dir}")
        print()
    
    print("=" * 60)
    print("📊 RESUMEN:")
    print(f"✅ Archivos existentes: {len(archivos_existentes)}")
    print(f"❌ Archivos faltantes: {len(archivos_faltantes)}")
    print()
    
    if archivos_faltantes:
        print("⚠️  ARCHIVOS FALTANTES:")
        for nombre, ruta in archivos_faltantes:
            print(f"   • {nombre}: {ruta}")
        print()
    
    print("📋 ESTRUCTURA DE DIRECTORIOS:")
    normativa_dir = Path("Normativa")
    if normativa_dir.exists():
        print(f"📂 {normativa_dir}/")
        for item in sorted(normativa_dir.rglob("*")):
            if item.is_file() and item.suffix.lower() == '.pdf':
                relative_path = item.relative_to(normativa_dir)
                size = item.stat().st_size
                print(f"   📄 {relative_path} ({size:,} bytes)")
            elif item.is_dir():
                relative_path = item.relative_to(normativa_dir)
                print(f"   📁 {relative_path}/")
    else:
        print(f"❌ Directorio Normativa no existe")

def verificar_directorios_detallado():
    """Verificación más detallada de la estructura de directorios"""
    print("\n" + "=" * 60)
    print("🔍 VERIFICACIÓN DETALLADA DE DIRECTORIOS")
    print("=" * 60)
    
    base_dir = Path(".")
    normativa_dir = base_dir / "Normativa"
    
    print(f"📂 Directorio base: {base_dir.absolute()}")
    print(f"📂 Directorio Normativa: {normativa_dir.absolute()}")
    print(f"   Existe: {normativa_dir.exists()}")
    
    if normativa_dir.exists():
        subdirs = [
            "PGOUM",
            "PGOUM/Usos", 
            "PGOUM/Zonas",
            "DOCUMENTOS BASICOS",
            "DOCUMENTOS BASICOS/DBSI"
        ]
        
        for subdir in subdirs:
            full_path = normativa_dir / subdir
            print(f"   📁 {subdir}: {'✅' if full_path.exists() else '❌'}")
            if full_path.exists():
                pdf_files = list(full_path.glob("*.pdf"))
                print(f"      📄 Archivos PDF: {len(pdf_files)}")
                for pdf in pdf_files[:5]:  # Mostrar solo los primeros 5
                    print(f"         - {pdf.name}")
                if len(pdf_files) > 5:
                    print(f"         ... y {len(pdf_files) - 5} más")

if __name__ == "__main__":
    verificar_archivos_normativas()
    verificar_directorios_detallado()
