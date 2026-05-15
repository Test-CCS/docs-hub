# Setup en GitHub

Pasos para configurar el repositorio `docs-hub` en GitHub y crear la GitHub App para sincronización automática.

## 1. Crear el repositorio en GitHub

1. Ve a GitHub.com
2. Click en "+" > "New repository"
3. Nombre: `docs-hub`
4. Descripción: "Documentación centralizada de todos los equipos"
5. **Visibility**: Public (si estás en plan Free) o Private (si tienes plan Team/Enterprise)
6. Desmarcar "Initialize this repository with:" (vamos a hacer push del código local)
7. Click "Create repository"

Después:
```bash
cd /ruta/a/docs-hub
git init
git add .
git commit -m "Initial commit: docs hub setup"
git branch -M main
git remote add origin https://github.com/tu-org/docs-hub.git
git push -u origin main
```

## 2. Crear la GitHub App

Esta app es lo que permite a GitHub Actions acceder a los repos de equipo sin usar un token personal.

### Pasos:

1. Ve a GitHub > Settings (en tu cuenta) > Developer Settings > GitHub Apps
2. Click "New GitHub App"
3. Completa el formulario:
   - **GitHub App name**: `docs-hub-sync`
   - **Homepage URL**: `https://github.com/tu-org/docs-hub`
   - **Webhook**: desmarcar "Active" (no lo necesitamos)

4. En "Repository permissions":
   - **Contents**: `Read-only`

5. En "Where can this GitHub App be installed?":
   - Seleccionar "Only on this account"

6. Click "Create GitHub App"

7. **Copiar el App ID** (número grande visible en la página de la App)

8. En la página de la App, click "Generate a private key" (al final de la página)
   - Se descargará un archivo `.pem`
   - **Guardar este archivo en un lugar seguro** (lo necesitarás en el siguiente paso)

### Instalar la App en los repos de equipo

1. En la página de la GitHub App que acabas de crear, click "Install App" (en el menú lateral)
2. Selecciona tu cuenta/organización
3. En "Repository access", selecciona:
   - Opción A: "Only select repositories" → selecciona cada repo de equipo
   - Opción B: "All repositories" → si prefieres acceso a todos

**Nota**: Puedes cambiar esto después en cualquier momento.

## 3. Configurar los secrets en GitHub

Los secrets almacenan de forma segura el APP_ID y APP_PRIVATE_KEY.

### Pasos:

1. Ve al repositorio `docs-hub`
2. Settings > Secrets and variables > **Actions**
3. Click "New repository secret"

**Primer secret:**
- Name: `APP_ID`
- Value: el número que copiaste en el paso 2.7
- Click "Add secret"

**Segundo secret:**
- Name: `APP_PRIVATE_KEY`
- Value: contenido completo del archivo `.pem` que descargaste
  - Abre el archivo `.pem` con un editor de texto
  - Copia TODO el contenido (incluyendo `-----BEGIN RSA PRIVATE KEY-----` y `-----END RSA PRIVATE KEY-----`)
  - Pega en el campo Value
- Click "Add secret"

✓ Ahora GitHub Actions tendrá acceso a estos secrets de forma segura.

## 4. Habilitar GitHub Pages

GitHub Pages publica automáticamente el contenido de la rama `gh-pages`.

### Pasos:

1. En el repositorio `docs-hub`, ve a Settings > Pages
2. En "Build and deployment" > "Source":
   - Selecciona "Deploy from a branch"
3. En "Branch":
   - Selecciona `gh-pages` (se creará automáticamente cuando corra el workflow por primera vez)
   - Folder: `/ (root)`
4. Click "Save"

**Nota**: El workflow crea la rama `gh-pages` automáticamente, así que si no existe aún, aparecerá después de la primera ejecución.

### URL del sitio

Después de que se genere `gh-pages`, tu documentación estará en:
```
https://tu-org.github.io/docs-hub/
```

(Si es un repo privado con plan Team/Enterprise, solo tendrán acceso los miembros con permisos en el repo)

## 5. Probar el workflow

### Primera ejecución manual

1. Ve a tu repositorio > Actions
2. En el menú izquierdo, selecciona "Sync Docs and Deploy"
3. Click "Run workflow" > "Run workflow"

Verá el workflow en ejecución. Si los repos de equipo en `config/teams.yml` existen y están correctamente configurados, sincronizará y publicará el sitio.

### Monitoreo

- Verifica que el workflow termine en verde ✓
- Si hay errores, click en el workflow para ver los logs

### Schedule automático

El workflow correrá automáticamente cada 2 horas (configurable en el `cron:` del workflow).

## Troubleshooting

### GitHub App no tiene permisos

**Error**: "API rate limit exceeded" o "Resource not accessible by integration"

**Solución**: Verifica que la GitHub App está instalada en los repos de equipo (paso 2 "Instalar la App en los repos de equipo")

### "Repository not found"

**Error**: `fatal: repository 'https://github.com/...' not found`

**Solución**: 
- Verifica que el nombre del repo en `config/teams.yml` es correcto
- Verifica que la GitHub App tiene acceso a ese repo

### Documentación no se sincroniza

**Posibles causas**:
- El repo no tiene una carpeta `docs/`
- La ruta en `config/teams.yml` está mal configurada (ej: `docs/technical` cuando debería ser `docs`)
- El repo es privado y la App no tiene acceso

## Cambios frecuentes

### Agregar un nuevo repo de equipo

1. Edita `config/teams.yml` y agrega el nuevo repo en la sección del equipo correspondiente
2. Instala la GitHub App en ese repo (si no está ya instalada)
3. Haz un `git commit` y `git push` de los cambios a `config/teams.yml`
4. El workflow se ejecutará automáticamente (detecta cambios en `config/teams.yml`)

### Cambiar el schedule

En `.github/workflows/sync-and-build.yml`, modifica la línea `cron`:
```yaml
cron: '0 */2 * * *'  # cada 2 horas
# Ejemplos:
# cron: '0 * * * *'    # cada hora
# cron: '0 */6 * * *'  # cada 6 horas
# cron: '0 0 * * *'    # diariamente a las 00:00 UTC
```

Ver: https://crontab.guru para ayuda con sintaxis cron
