<div align="center">

<h1>⚡ Q3 CPMA NCQ3 Map List Config Generator v2.1</h1>

**Sistema Dinámico de Generación Automática** de archivos de configuración de mapas para Quake 3 Arena CPMA

🌐 Sitio oficial de CPMA: https://playmorepromode.com/

🌐 Maked with love by https://yimgame.github.io/

<p>
 
<img width="714" height="749" alt="q3_cpma_map_list_config_generator" src="https://github.com/user-attachments/assets/1b9cdca6-88b1-4f9c-9fd6-c544e8b6af72" />

</p>


 [![GitHub Copilot](https://img.shields.io/badge/github_copilot-8957E5?style=for-the-badge&logo=github-copilot&logoColor=white)](https://github.com/copilot/)


[![Discord](https://img.shields.io/badge/Discord-5865F2?style=flat&logo=discord&logoColor=white)](https://discord.gg/pT4nmpS/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg)](https://html.spec.whatwg.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

<h2 align="center">🚀 Q3 CPMA NCQ3 Map List Config Generator v2.1</h2>

### ✨ Versión 2.1 - Sistema Dinámico
- 🤖 **Auto-detección de modos de juego**: Detecta automáticamente modos nuevos sin configuración manual
- 🎯 **Clasificación inteligente**: Identifica automáticamente si un modo usa `fraglimit`, `caplimit` o formato especial
- 📊 **Stats dinámicos**: Muestra todos los modos encontrados, no solo una lista fija
- 🎨 **Tarjetas auto-generadas**: Crea interfaces de configuración para modos desconocidos
- ♾️ **Extensibilidad infinita**: Soporta cualquier modo que aparezca en archivos `.arena`

### 🎮 Funcionalidades Core
- 🔍 Escanea automáticamente todos los archivos .pk3 en baseq3
- 📋 Parsea archivos .arena y extrae metadata de mapas
- 🎯 Clasifica mapas por tipo automáticamente
- ⚙️ Interfaz web responsive para configurar parámetros
- 💾 Genera archivos de configuración listos para usar
- 👁️ Previsualización en tiempo real antes de generar
- 🪟 Ventana GUI nativa (no necesitas navegador)
- 🔌 Detección automática de puerto disponible (5000-5009)
- 🌐 Acceso por LAN con IP detectada automáticamente
 - ☑️ Checkboxes por mapa para incluir/excluir; los excluidos se exportan con `minplayers -1` (banned) si no quieres jugarlo o esta mal seteado en el `.arena` (ej. CTF sin banderas)

### 🎲 Modos Soportados (+ Infinitos Más)

**Preconfigurados con valores optimizados:**
- **FFA** - Free For All
- **CTF / CTFS** - Capture The Flag / Strawberry
- **Tourney / 1v1 / DA** - Duelos
- **Team / TDM** - Team Deathmatch
- **CA** - Clan Arena
- **FT** - Freeze Tag
- **HM** - HoonyMode
- **RA / RA3** - Rocket Arena
- **NTF** - No Team Flags
- **2v2** - Two vs Two
- **FTAG** - Flag Tag

**Y cualquier modo nuevo** que aparezca en tus archivos `.arena` será detectado y configurado automáticamente.

## 📦 Versiones Disponibles

### 🪟 Versión GUI (Ventana Integrada) - RECOMENDADA
- Ejecutable independiente con interfaz gráfica propia
- No necesitas abrir el navegador manualmente
- Ventana nativa de Windows con la aplicación embebida
- Más profesional y fácil de usar
- **Archivo:** `dist\Q3MapConfigGenerator.exe`

### 🌐 Versión Solo Servidor
- Inicia un servidor web local
- Debes abrir manualmente el navegador
- Útil si prefieres usar tu navegador favorito
- **Archivos:** `app.py` o `run.bat` o `run_exe.bat`

## Instalación rápida (instalador)

| Sistema | Cómo | Qué hace |
|---|---|---|
| 🪟 Windows | doble clic en `instalar.bat` | Crea el entorno de Python (`q3cg`), instala dependencias y arma `config.json` con tu carpeta de Quake 3. Después: `run.bat` |
| 🐧 Linux, Python | `bash instalar.sh` → opción **1** | Crea `.venv`, arma `config.json` y `iniciar.sh`. Opcional: servicio systemd que arranca solo |
| 🐳 Linux, Docker | `bash instalar.sh` → opción **2** | Arma `config.json` y `docker-compose.yml` montando esta carpeta (un `git pull` + reinicio = actualizado) y lo levanta |

El instalador pregunta la carpeta de Quake 3 (la que tiene `baseq3` y `cpma`) y la IP donde corren los servers
(para aplicar las listas next/prev en vivo por rcon). Todo queda en `config.json`, que no se sube a git:

```json
{
  "baseq3_path": "/opt/quake3/baseq3",
  "output_path": "/opt/quake3/cpma/cfg-maps",
  "ra3_path": "/opt/quake3/cpma/cfg-ra3",
  "q3_host": "127.0.0.1"
}
```

## 🔁 Listas next / prev (vstr) — v2.2

Al **Generar** un modo con server propio (CTF, TDM, FFA, 1v1, 2v2, CA, FT, RA3) además se crea
`cfg-maps/nextmap_<modo>.cfg` con la misma lista y orden, y (si tildás *Aplicarla en vivo*) se carga en el server por rcon:

| Comando | Qué hace |
|---|---|
| `/rcon vstr next` (o `siguiente`, `nextmap`) | pasa al próximo mapa de la lista |
| `/rcon vstr prev` (o `anterior`) | vuelve al anterior de la lista |
| `/rcon vstr volver` | vuelve al mapa en el que estabas antes del último salto |
| `/rcon vstr v7` | salta directo al mapa número 7 |
| `/rcon actual` | muestra en qué mapa y número estás, ej. `basesiege[1/42]` |

Para que el server la cargue al arrancar, agregá a su línea de comando `+exec cfg-maps/nextmap_<modo>.cfg`.
Los mapas destildados salen al final del archivo de rotación con `minplayers -1` (baneados: no rotan ni se votan).
Antes de pisar cualquier archivo se guarda una copia en `cfg-maps/_respaldo/`.

## Instalación y Uso

### Opción 1: Ejecutable con GUI (¡RECOMENDADO!)

**¡La forma más fácil! Ventana propia con la aplicación integrada**

1. Haz doble clic en `run_gui.bat` o ejecuta directamente `dist\Q3MapConfigGenerator.exe`
2. La aplicación se abrirá en su propia ventana
3. ¡No necesitas abrir el navegador!

### Opción 2: Ejecutable modo web

1. Haz doble clic en `run_exe.bat` (versión solo servidor)
2. Abre tu navegador en: http://localhost:5000

### Opción 3: Con Python

1. Asegúrate de tener Python 3.8+ instalado

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta la aplicación:
```bash
python app.py
```
O simplemente haz doble clic en `run.bat`

4. Abre tu navegador en: http://localhost:5000

## Pasos para Usar la Aplicación

1. **Configurar Rutas** (primera vez):
   - Haz clic en el botón de configuración (⚙️)
   - Ingresa la ruta de tu carpeta baseq3 de Quake 3
   - Ingresa la ruta donde quieres guardar los archivos generados
   - Guarda la configuración

2. Haz clic en "Escanear Archivos .pk3" para analizar todos los mapas

4. Configura los parámetros para cada tipo de mapa:
   - **Min Players**: Número mínimo de jugadores
   - **Max Players**: Número máximo de jugadores
   - **Fraglimit/Caplimit**: Límite de frags o capturas
   - **Timelimit**: Límite de tiempo en minutos

5. Usa "Previsualizar" para ver cómo quedará el archivo

6. Haz clic en "Generar Archivo" para crear la configuración

## Archivos Generados

Los archivos se guardan en: `G:\Games\Quake3\cpma\cfg-maps\`

**Modos individuales:**
- `ffamaps.txt` - Mapas Free For All
- `1v1maps.txt` - Mapas 1v1 / Duel
- `tourneymaps.txt` - Mapas Tourney
- `damaps.txt` - Mapas Duel Arena
- `hmmaps.txt` - Mapas HoonyMode
- `2v2maps.txt` - Mapas 2 vs 2

**Modos de equipo:**
- `teammaps.txt` - Mapas Team
- `tdmmaps.txt` - Mapas Team Deathmatch
- `ctfmaps.txt` - Mapas Capture The Flag
- `ctfsmaps.txt` - Mapas CTF Strawberry
- `ntfmaps.txt` - Mapas No Team Flags
- `ftagmaps.txt` - Mapas Flag Tag

**Modos especiales:**
- `camaps.txt` - Mapas Clan Arena
- `ftmaps.txt` - Mapas Freeze Tag
- `mamaps.txt` - Mapas Rocket Arena

## Estructura de Archivos .arena

El programa busca archivos con esta estructura dentro de los .pk3:

```
{
map         "ASSault"
longname    "Levelord®'s ASSault"
bots        "Sarge Hunter Klesk Anarki"
fraglimit   17
timelimit   17
type        "ffa team tourney"
}
```

## Tipos de Mapas Soportados

**Modos de 1-4 jugadores:**
- **FFA** - Free For All
- **1v1 / Tourney** - Duelo 1vs1
- **DA** - Duel Arena
- **HM** - HoonyMode
- **2v2** - Two vs Two

**Modos de equipo:**
- **Team** - Equipo genérico
- **TDM** - Team Deathmatch
- **CTF** - Capture The Flag
- **CTFS** - CTF Strawberry
- **NTF** - No Team Flags
- **FTAG** - Flag Tag

**Modos especiales:**
- **CA** - Clan Arena
- **FT** - Freeze Tag
- **RA** - Rocket Arena
- **RA3** - Rocket Arena 3 (formato especial con arena field)

## 🧠 Sistema de Auto-Detección Inteligente

El generador v2.0 utiliza un sistema de clasificación automática:

### Reglas de Detección
```python
if "ctf" in mode_name:
    → Usa caplimit (formato CTF)
elif mode_name in ["duel", "1v1", "2v2", "tourney"]:
    → Usa fraglimit (formato Duel)
elif mode_name == "ra3":
    → Usa roundlimit + arena field (formato RA3)
else:
    → Usa fraglimit (formato FFA por defecto)
```

### Ejemplos de Auto-Detección
- Modo `"zombies"` → Detectado como FFA → `zombiesmaps.txt` con fraglimit
- Modo `"megactf"` → Detectado como CTF → `megactfmaps.txt` con caplimit
- Modo `"arena2024"` → Detectado como FFA → `arena2024maps.txt` con fraglimit

## 🛠️ Tecnologías

- **Backend**: Python 3.13 + Flask 3.1.2
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **GUI**: PyWebView (EdgeWebView2)
- **Parser**: Expresiones regulares + zipfile
- **Build**: PyInstaller 6.18.0
- **Auto-Detection Engine**: Sistema de clasificación dinámica

## 📝 Changelog

Ver [CHANGELOG.md](CHANGELOG.md) para el historial completo de versiones.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si tienes ideas para mejorar el generador:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## ✨ Autor

**Desarrollado con amor por GitHub Copilot** (Claude Sonnet 4.5)  
🤖 AI-Powered Development for the Quake 3 Community

Just coding 4 fun !!!

---

<div align="center">

**⚡ Q3 Map Config Generator v2.0 ⚡**

*Making Quake 3 CPMA server configuration effortless since 2026*

[⭐ Star en GitHub](https://github.com/yimgame/q3-map-list-config-generator) | [🐛 Reportar Bug](https://github.com/yimgame/q3-map-list-config-generator/issues) | [💡 Solicitar Feature](https://github.com/yimgame/q3-map-list-config-generator/issues)

</div>
