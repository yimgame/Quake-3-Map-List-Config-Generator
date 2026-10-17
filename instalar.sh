#!/usr/bin/env bash
# Instalador del Q3 Map Config Generator para Linux.
#   1) Python  -> entorno virtual en .venv (y opcional: servicio systemd que arranca solo)
#   2) Docker  -> genera docker-compose.yml con esta carpeta montada (el código no se copia a ningún volumen)
# Uso: bash instalar.sh
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
DIR="$(pwd)"

preguntar() { local p="$1" d="$2" r; read -r -p "$p [$d]: " r; echo "${r:-$d}"; }

echo "============================================================"
echo "  Q3 MAP CONFIG GENERATOR - instalador Linux"
echo "============================================================"
echo "  1) Python (venv)        2) Docker (docker compose)"
MODO="$(preguntar 'Elegí 1 o 2' 1)"

if [ "$MODO" = "2" ]; then
  Q3="$(preguntar 'Carpeta de Quake 3 en este equipo (la que tiene baseq3 y cpma)' /opt/quake3)"
  [ -d "$Q3/baseq3" ] || echo "AVISO: no encuentro $Q3/baseq3 (igual sigo; lo podés cambiar después en docker-compose.yml)"
  HOST="$(preguntar 'IP donde corren los servers Q3 (para aplicar next/prev en vivo por rcon)' "$(hostname -I 2>/dev/null | awk '{print $1}')")"
  PUERTO="$(preguntar 'Puerto web' 5050)"
  # dentro del container Quake 3 siempre queda en /quake3
  printf '{\n  "baseq3_path": "/quake3/baseq3",\n  "output_path": "/quake3/cpma/cfg-maps",\n  "ra3_path": "/quake3/cpma/cfg-ra3",\n  "q3_host": "%s"\n}\n' "$HOST" > config.json
  cat > docker-compose.yml <<YML
services:
  q3-map-config-generator:
    image: python:3.13-slim
    container_name: q3-map-config-generator
    working_dir: /app
    ports:
      - "${PUERTO}:5000"
    volumes:
      - ${DIR}:/app            # el código es esta carpeta (git pull y reiniciar = actualizado)
      - ${Q3}:/quake3:rw
    environment:
      - TZ=America/Argentina/Buenos_Aires
    command: ["bash", "-lc", "pip install --no-cache-dir --quiet flask && mkdir -p /quake3/cpma/cfg-ra3 && python /app/app.py"]
    restart: unless-stopped
YML
  echo
  echo "Listo: config.json y docker-compose.yml creados."
  if command -v docker >/dev/null 2>&1; then
    [ "$(preguntar '¿Lo levanto ahora con docker compose up -d? (s/n)' s)" = "s" ] && docker compose up -d
  else
    echo "No encontré docker: instalalo y corré 'docker compose up -d' en esta carpeta."
  fi
  echo "Abrí http://$HOST:$PUERTO"
  exit 0
fi

command -v python3 >/dev/null 2>&1 || { echo "Falta python3 (ej: sudo apt install python3 python3-venv)"; exit 1; }
Q3="$(preguntar 'Carpeta de Quake 3 (la que tiene baseq3 y cpma)' /opt/quake3)"
[ -d "$Q3/baseq3" ] || echo "AVISO: no encuentro $Q3/baseq3 (lo podés cambiar después desde la web, en Configuración)"
HOST="$(preguntar 'IP donde corren los servers Q3 (rcon)' 127.0.0.1)"
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet Flask==3.1.2      # pywebview solo hace falta para la versión con ventana de Windows
printf '{\n  "baseq3_path": "%s/baseq3",\n  "output_path": "%s/cpma/cfg-maps",\n  "ra3_path": "%s/cpma/cfg-ra3",\n  "q3_host": "%s"\n}\n' "$Q3" "$Q3" "$Q3" "$HOST" > config.json
cat > iniciar.sh <<SH
#!/usr/bin/env bash
cd "\$(dirname "\$(readlink -f "\$0")")" && exec .venv/bin/python app.py
SH
chmod +x iniciar.sh
echo
echo "Listo. Para abrirlo: ./iniciar.sh  -> http://localhost:5000"
if command -v systemctl >/dev/null 2>&1 && [ "$(preguntar '¿Instalar como servicio que arranca solo (systemd, pide sudo)? (s/n)' n)" = "s" ]; then
  sudo tee /etc/systemd/system/q3-map-config-generator.service >/dev/null <<UNIT
[Unit]
Description=Q3 Map Config Generator
After=network.target

[Service]
WorkingDirectory=$DIR
ExecStart=$DIR/.venv/bin/python $DIR/app.py
Restart=on-failure
User=$(id -un)

[Install]
WantedBy=multi-user.target
UNIT
  sudo systemctl daemon-reload && sudo systemctl enable --now q3-map-config-generator
  echo "Servicio instalado: systemctl status q3-map-config-generator"
fi
