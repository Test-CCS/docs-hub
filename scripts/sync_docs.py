#!/usr/bin/env python3
"""
Sincroniza la documentación de los repos de equipo al directorio docs/teams/.
Usa sparse checkout para clonar solo la carpeta docs/ sin el historial completo.
"""

import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path
import subprocess
import yaml

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    logger.warning("GITHUB_TOKEN no configurado. Algunos repos privados podrían fallar.")

# Directorios clave
ROOT_DIR = Path(__file__).parent.parent
DOCS_DIR = ROOT_DIR / "docs"
TEAMS_DIR = DOCS_DIR / "teams"
CONFIG_FILE = ROOT_DIR / "config" / "teams.yml"


def load_config():
    """Lee config/teams.yml y retorna la configuración."""
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)


def git_clone_sparse(repo_url, docs_path, target_dir):
    """
    Clona un repo con sparse checkout, trayendo solo la carpeta docs_path.
    Retorna True si tuvo éxito, False en caso contrario.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Inicializar repo sin clonar nada
            subprocess.run(
                ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", repo_url, str(tmppath)],
                check=True,
                capture_output=True,
                timeout=60
            )

            # Sparse checkout de la carpeta docs_path
            subprocess.run(
                ["git", "-C", str(tmppath), "sparse-checkout", "set", docs_path],
                check=True,
                capture_output=True,
                timeout=30
            )

            # Copiar archivos al destino
            source_path = tmppath / docs_path
            if not source_path.exists():
                logger.error(f"  Carpeta '{docs_path}' no encontrada en {repo_url}")
                return False

            # Crear directorio destino y copiar
            target_dir.mkdir(parents=True, exist_ok=True)

            for item in source_path.iterdir():
                if item.is_dir():
                    shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, target_dir)

            logger.info(f"  ✓ Sincronizado correctamente")
            return True

    except subprocess.TimeoutExpired:
        logger.error(f"  Timeout clonando {repo_url}")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"  Error clonando: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        logger.error(f"  Error inesperado: {e}")
        return False


def generate_team_index(team_name, repos, team_dir):
    """Genera un index.md para el equipo."""
    index_path = team_dir / "index.md"

    content = f"# {team_name}\n\n"
    content += "## Repositorios\n\n"

    for repo in repos:
        label = repo.get("label", repo["name"])
        content += f"- [{label}]({label.replace(' ', '-')}/)\n"

    with open(index_path, "w") as f:
        f.write(content)

    logger.info(f"  Generado index.md para {team_name}")


def generate_global_index(config):
    """Genera el index.md global en docs/."""
    index_path = DOCS_DIR / "index.md"

    content = "# Docs Hub\n\n"
    content += "Bienvenido a la documentación centralizada.\n\n"
    content += "## Equipos\n\n"

    for team in config.get("teams", []):
        team_name = team["name"]
        team_slug = team["slug"]
        description = team.get("description", "")
        content += f"- **[{team_name}](teams/{team_slug}/)**: {description}\n"

    with open(index_path, "w") as f:
        f.write(content)

    logger.info("Generado index.md global")


def ensure_index_in_directory(directory):
    """
    Asegura que cada directorio tenga un index.md.
    Si no existe, crea un placeholder.
    """
    index_path = directory / "index.md"
    if not index_path.exists():
        content = f"# {directory.name}\n\nDocumentación de {directory.name}.\n"
        with open(index_path, "w") as f:
            f.write(content)


def main():
    logger.info("=== Sincronizando documentación ===")

    # Limpiar directorio de destino
    if TEAMS_DIR.exists():
        shutil.rmtree(TEAMS_DIR)
    TEAMS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    config = load_config()
    failed_repos = []
    successful_repos = []
    total_repos = 0

    # Procesar cada equipo
    for team in config.get("teams", []):
        team_name = team["name"]
        team_slug = team["slug"]
        team_dir = TEAMS_DIR / team_slug

        logger.info(f"\nEquipo: {team_name} ({team_slug})")

        team_dir.mkdir(parents=True, exist_ok=True)

        repos = team.get("repos", [])
        for repo_config in repos:
            total_repos += 1
            repo_name = repo_config["name"]
            repo_full = repo_config["repo"]
            docs_path = repo_config.get("docs_path", "docs")
            label = repo_config.get("label", repo_name)

            logger.info(f"  Sincronizando: {label} ({repo_full})")

            # Construir URL con token si está disponible
            if GITHUB_TOKEN:
                repo_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{repo_full}.git"
            else:
                repo_url = f"https://github.com/{repo_full}.git"

            # Directorio destino
            repo_target = team_dir / label.replace(" ", "-")

            # Intentar sincronización
            success = git_clone_sparse(repo_url, docs_path, repo_target)

            if success:
                # Asegurar que hay un index.md en el directorio del repo
                ensure_index_in_directory(repo_target)
                successful_repos.append(f"{team_name}/{label}")
            else:
                failed_repos.append(f"{team_name}/{label}")
                # Crear placeholder con advertencia
                repo_target.mkdir(parents=True, exist_ok=True)
                placeholder = repo_target / "index.md"
                with open(placeholder, "w") as f:
                    f.write(f"# {label} - No disponible\n\n")
                    f.write(f"⚠️ No se pudo obtener la documentación de este repositorio.\n\n")
                    f.write(f"**Repo**: {repo_full}\n\n")
                    f.write(f"**Razón posible**: Permisos insuficientes, carpeta '{docs_path}' no encontrada, o repositorio privado.\n")

        # Generar index del equipo
        if repos:
            generate_team_index(team_name, repos, team_dir)

    # Generar index global
    generate_global_index(config)

    # Resumen
    logger.info(f"\n=== Resumen ===")
    logger.info(f"Total de repos: {total_repos}")
    logger.info(f"Exitosos: {len(successful_repos)}")
    logger.info(f"Fallidos: {len(failed_repos)}")

    if failed_repos:
        logger.warning(f"Repos con error: {', '.join(failed_repos)}")

    # Criterio de fallo: si más del 50% de repos fallaron
    failure_rate = len(failed_repos) / total_repos if total_repos > 0 else 0
    if failure_rate > 0.5:
        logger.error(f"Tasa de fallo ({failure_rate:.0%}) excede el 50%. Abortando.")
        sys.exit(1)

    logger.info("✓ Sincronización completada")


if __name__ == "__main__":
    main()
