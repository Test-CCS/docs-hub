#!/usr/bin/env python3
"""
Genera mkdocs.yml dinámicamente basándose en la estructura de archivos en docs/teams/.
Construye la navegación automáticamente a partir de los directorios y archivos Markdown.
"""

import os
import sys
import logging
from pathlib import Path
import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent
DOCS_DIR = ROOT_DIR / "docs"
TEAMS_DIR = DOCS_DIR / "teams"


def get_markdown_files(directory):
    """Retorna lista de archivos .md en un directorio, ordenados (index.md primero)."""
    md_files = []
    for item in sorted(directory.glob("*.md")):
        md_files.append(item.name)

    # Mover index.md al inicio si existe
    if "index.md" in md_files:
        md_files.remove("index.md")
        md_files.insert(0, "index.md")

    return md_files


def build_nav_for_directory(directory, base_path):
    """
    Construye la estructura de navegación para un directorio.
    Retorna una lista de items de navegación MkDocs.
    """
    nav_items = []
    path_obj = Path(directory)

    # Primero: archivos .md directos
    md_files = get_markdown_files(path_obj)
    for md_file in md_files:
        if md_file == "index.md":
            # No listar index.md explícitamente, MkDocs lo maneja con navigation.indexes
            continue
        nav_path = str(Path(base_path) / md_file)
        nav_items.append({md_file[:-3]: nav_path})  # Quitar .md

    # Luego: subdirectorios (para subsecciones)
    for item in sorted(path_obj.iterdir()):
        if item.is_dir() and not item.name.startswith("_"):
            subdir_nav = build_nav_for_directory(item, Path(base_path) / item.name)
            if subdir_nav:  # Solo agregar si hay contenido
                nav_items.append({
                    item.name: subdir_nav
                })

    return nav_items


def build_nav_for_team(team_slug, team_name):
    """Construye la estructura de navegación para un equipo."""
    team_dir = TEAMS_DIR / team_slug
    if not team_dir.exists():
        return None

    nav = []

    # Agregar index.md del equipo
    team_index_path = f"teams/{team_slug}/index.md"
    nav.append({team_name: team_index_path})

    # Agregar cada repo como sección
    for repo_dir in sorted(team_dir.iterdir()):
        if repo_dir.is_dir():
            repo_label = repo_dir.name
            repo_base_path = f"teams/{team_slug}/{repo_label}"

            # Incluir el index.md del repo si existe
            repo_index = repo_dir / "index.md"
            repo_nav = []

            if repo_index.exists():
                repo_nav.append({repo_label: f"{repo_base_path}/index.md"})

            # Agregar subdirectorios (subsecciones)
            for sub_dir in sorted(repo_dir.iterdir()):
                if sub_dir.is_dir() and not sub_dir.name.startswith("_"):
                    sub_nav = build_nav_for_directory(sub_dir, f"{repo_base_path}/{sub_dir.name}")
                    if sub_nav:
                        repo_nav.append({sub_dir.name: sub_nav})

            # Agregar archivos .md directos del repo (además del index)
            for md_file in get_markdown_files(repo_dir):
                if md_file != "index.md":
                    repo_nav.append({md_file[:-3]: f"{repo_base_path}/{md_file}"})

            if repo_nav:
                nav.append({repo_label: repo_nav})

    return nav


def generate_mkdocs_config():
    """Genera la configuración completa de MkDocs."""
    config = {
        "site_name": "Docs Hub",
        "theme": {
            "name": "material",
            "language": "es",
            "features": [
                "navigation.tabs",         # Tabs por sección en barra superior
                "navigation.sections",     # Secciones en sidebar
                "navigation.indexes",      # Soporta index.md en carpetas
                "search.highlight",        # Resalta términos de búsqueda
                "content.code.copy",       # Botón copy en bloques de código
            ]
        },
        "markdown_extensions": [
            "pymdownx.emoji",
            "pymdownx.superfences",
            "pymdownx.tasklist",
        ],
        "plugins": [
            "search"
        ]
    }

    # Construir navegación
    nav = [
        {"Inicio": "index.md"}
    ]

    # Agregar equipos
    config_file = ROOT_DIR / "config" / "teams.yml"
    with open(config_file) as f:
        config_data = yaml.safe_load(f)

    for team in config_data.get("teams", []):
        team_name = team["name"]
        team_slug = team["slug"]
        team_nav = build_nav_for_team(team_slug, team_name)
        if team_nav:
            nav.append({team_name: team_nav})

    config["nav"] = nav

    return config


def main():
    logger.info("=== Generando mkdocs.yml ===")

    try:
        config = generate_mkdocs_config()

        # Escribir mkdocs.yml
        output_file = ROOT_DIR / "mkdocs.yml"
        with open(output_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        logger.info(f"✓ Generado {output_file}")
        logger.info(f"  - site_name: {config['site_name']}")
        logger.info(f"  - secciones de navegación: {len(config.get('nav', []))}")

    except Exception as e:
        logger.error(f"Error generando mkdocs.yml: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
