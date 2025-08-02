#!/usr/bin/env python3
"""
Script pour vérifier que requirements.txt est trié et bien formaté
"""

import sys
from pathlib import Path


def check_requirements_sorted(requirements_file: Path) -> bool:
    """Vérifie si un fichier requirements.txt est trié."""
    if not requirements_file.exists():
        print(f"❌ {requirements_file} n'existe pas")
        return False
    
    with open(requirements_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Filtrer les commentaires et lignes vides
    package_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-'):
            # Extraire le nom du package (avant ==, >=, etc.)
            package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('~=')[0]
            package_lines.append((package_name.lower(), line))
    
    # Vérifier le tri
    sorted_packages = sorted(package_lines, key=lambda x: x[0])
    
    if package_lines != sorted_packages:
        print(f"❌ {requirements_file} n'est pas trié alphabétiquement")
        print("\nOrdre actuel:")
        for _, line in package_lines:
            print(f"  {line}")
        print("\nOrdre attendu:")
        for _, line in sorted_packages:
            print(f"  {line}")
        return False
    
    print(f"✅ {requirements_file} est correctement trié")
    return True


def main():
    """Point d'entrée principal."""
    backend_dir = Path(__file__).parent.parent / 'backend'
    requirements_files = [
        backend_dir / 'requirements.txt',
        backend_dir / 'requirements-dev.txt',
    ]
    
    all_good = True
    
    for req_file in requirements_files:
        if req_file.exists():
            if not check_requirements_sorted(req_file):
                all_good = False
    
    if not all_good:
        print("\n💡 Pour trier automatiquement:")
        print("pip-compile --upgrade requirements.in")
        sys.exit(1)
    
    print("✅ Tous les fichiers requirements sont correctement formatés")


if __name__ == '__main__':
    main()