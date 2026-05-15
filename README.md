# Docs Hub

Repositorio centralizado que agrega documentación Markdown de múltiples repositorios de equipo y la publica automáticamente vía GitHub Pages.

## Arquitectura

El flujo es simple:
1. **GitHub Actions scheduler** (cada 2 horas) dispara el workflow `sync-and-build.yml`
2. **sync_docs.py** clona solo la carpeta `docs/` de cada repo configurado (sparse checkout)
3. **generate_mkdocs_nav.py** construye dinámicamente la navegación
4. **MkDocs** genera el sitio estático
5. El sitio se publica a la branch `gh-pages` → GitHub Pages lo sirve

## Estructura del repositorio

```
docs-hub/
├── .github/workflows/
│   └── sync-and-build.yml        # Workflow de CI/CD
├── config/
│   └── teams.yml                 # Fuente de verdad: equipos y repos
├── scripts/
│   ├── sync_docs.py              # Clona docs/ de cada repo
│   └── generate_mkdocs_nav.py    # Genera mkdocs.yml dinámicamente
├── docs/
│   └── overrides/                # Personalizaciones de tema
├── requirements.txt
└── README.md
```

`docs/teams/` y `mkdocs.yml` se generan en runtime durante cada ejecución del workflow.

## Configuración inicial

### 1. Crear la GitHub App

1. GitHub > Settings > Developer Settings > GitHub Apps > New GitHub App
2. Nombre: `docs-hub-sync`
3. Homepage URL: URL del repo `docs-hub`
4. Desactivar Webhooks
5. Permissions > Repository permissions > **Contents: Read-only**
6. "Only on this account"
7. Copiar el **App ID**
8. En la App > Generate a private key → descargar el `.pem`

### 2. Instalar la App en los repos de equipo

1. En la GitHub App: Install App
2. Seleccionar la cuenta/org
3. Repository access: seleccionar todos los repos de equipo

### 3. Configurar secrets en `docs-hub`

Settings > Secrets and variables > Actions:
- `APP_ID`: el ID numérico
- `APP_PRIVATE_KEY`: contenido del `.pem`

### 4. Crear la rama `gh-pages`

El workflow crea la rama automáticamente, pero puedes crearla manualmente:
```bash
git checkout --orphan gh-pages
git rm -rf .
echo "# Docs Hub" > README.md
git add README.md
git commit -m "Initial commit"
git push -u origin gh-pages
```

### 5. Activar GitHub Pages

Settings > Pages > Source: `Deploy from a branch` > Branch: `gh-pages` > Folder: `/ (root)`

## Convenciones para repos de equipo

Para que la sincronización funcione correctamente:

- **Carpeta `docs/`**: todos los archivos Markdown deben estar aquí (o la ruta configurada en `config/teams.yml`)
- **`index.md` en cada sección**: MkDocs lo usa como landing page de la sección
- **Links relativos**: usar paths relativos, no absolutos
- **Imágenes**: colocar en `docs/assets/` o `docs/images/`
- **Nombres de archivos**: no usar espacios ni caracteres especiales

Ejemplo de estructura recomendada:
```
repo/
└── docs/
    ├── index.md
    ├── getting-started.md
    ├── api-reference.md
    └── assets/
        └── diagram.png
```

## Probar localmente

```bash
# Instalar dependencias
pip install -r requirements.txt

# Sincronizar documentación
GITHUB_TOKEN=<token> python scripts/sync_docs.py

# Generar navegación
python scripts/generate_mkdocs_nav.py

# Servir localmente en http://localhost:8000
mkdocs serve
```

## Agregar un nuevo repo

1. Agregar el repo al `config/teams.yml`:
   ```yaml
   - name: "nuevo-repo"
     repo: "mi-org/nuevo-repo"
     docs_path: "docs"
     label: "Nuevo"
   ```
2. Instalar la GitHub App en ese repo
3. El workflow sincronizará automáticamente en el próximo run

## Troubleshooting

- **El sitio no se actualiza**: revisar el workflow en Actions > buscar errores en los logs
- **Un repo no se sincroniza**: verificar que la App esté instalada en ese repo y que tenga una carpeta `docs/`
- **Links rotos**: asegurar que los links en los Markdown sean relativos
- **Imágenes no cargadas**: verificar que estén en `docs/assets/` o similar y que los paths en los `.md` sean correctos
