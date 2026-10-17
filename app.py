"""
Q3 Map Config Generator
Aplicación Flask para generar archivos de configuración de mapas de Quake 3
"""
import os
import json
import zipfile
import re
import socket
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_file
from collections import defaultdict
from datetime import datetime
import shutil

app = Flask(__name__)

# Cargar configuración desde archivo
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    """Carga la configuración desde config.json"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'baseq3_path': "/quake3/baseq3",
        'output_path': "/quake3/cpma/cfg-maps",
        'ra3_path': "/quake3/cpma/cfg-ra3"
    }

def save_config(config):
    """Guarda la configuración en config.json"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_lan_ip():
    """Obtiene la dirección IP de la red local"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# Configuración inicial
config = load_config()
BASEQ3_PATH = config.get('baseq3_path')
OUTPUT_PATH = config.get('output_path')
RA3_PATH = config.get('ra3_path') or os.path.join(os.path.dirname(OUTPUT_PATH.rstrip('/\\')), 'cfg-ra3')

class ArenaParser:
    """Parser para archivos .arena de Quake 3"""
    
    def __init__(self):
        self.maps_by_type = defaultdict(list)
    
    def parse_arena_file(self, content):
        """Parsea el contenido de un archivo .arena"""
        maps = []
        # Buscar bloques entre llaves
        pattern = r'\{([^}]+)\}'
        blocks = re.findall(pattern, content, re.DOTALL)
        
        for block in blocks:
            map_data = {}
            # Extraer pares clave-valor
            for line in block.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Buscar patrón: clave "valor" o clave valor
                match = re.match(r'(\w+)\s+["\']?([^"\']+)["\']?', line)
                if match:
                    key, value = match.groups()
                    map_data[key.lower()] = value.strip().strip('"\'')
            
            if 'map' in map_data and 'type' in map_data:
                maps.append(map_data)
        
        return maps
    
    def scan_pk3_files(self, base_path):
        """Escanea todos los archivos .pk3 en busca de archivos .arena"""
        all_maps = []
        
        # Verificar que la ruta existe
        if not os.path.exists(base_path):
            raise Exception(f"La ruta no existe: {base_path}")
        
        pk3_files = list(Path(base_path).glob("*.pk3"))
        
        if not pk3_files:
            raise Exception(f"No se encontraron archivos .pk3 en: {base_path}")
        
        for pk3_file in pk3_files:
            try:
                with zipfile.ZipFile(pk3_file, 'r') as zip_ref:
                    # Buscar archivos .arena en la carpeta scripts
                    arena_files = [f for f in zip_ref.namelist() 
                                 if f.startswith('scripts/') and f.endswith('.arena')]
                    
                    for arena_file in arena_files:
                        content = zip_ref.read(arena_file).decode('utf-8', errors='ignore')
                        maps = self.parse_arena_file(content)
                        for map_info in maps:
                            map_info['source_pk3'] = pk3_file.name
                            all_maps.append(map_info)
            except Exception as e:
                print(f"Error procesando {pk3_file.name}: {e}")
        
        # Clasificar por tipo
        self.maps_by_type.clear()
        # Lista completa de tipos soportados de CPMA
        # 'team' no es un tipo aparte: se unifica dentro de 'tdm' (ver abajo)
        supported_types = ['ffa', 'tdm', 'tourney', '1v1', 'ctf', 'ra', 'ra3',
                          'hm', 'da', 'ca', 'ft', 'ctfs', 'ntf', '2v2', 'ftag']

        # 'tourney' y '1v1' son lo mismo (duelo): van todos a '1v1'. 'team' va a 'tdm'. Sin repetir mapas por tipo.
        alias = {'tourney': '1v1', 'team': 'tdm'}
        vistos = defaultdict(set)
        for map_info in all_maps:
            for type_name in map_info.get('type', '').lower().split():
                tipo = alias.get(type_name, type_name)
                nombre = map_info.get('map', '').lower()
                if tipo in supported_types and nombre not in vistos[tipo]:
                    vistos[tipo].add(nombre)
                    self.maps_by_type[tipo].append(map_info)
        for tipo in self.maps_by_type:
            self.maps_by_type[tipo].sort(key=lambda m: m.get('map', '').lower())
        
        return all_maps

class ConfigGenerator:
    """Generador de archivos de configuración de mapas"""
    
    @staticmethod
    def generate_ctf_config(maps, default_params=None):
        """Genera configuración para mapas CTF"""
        if default_params is None:
            default_params = {
                'minplayers': '02',
                'maxplayers': '12',
                'caplimit': '05',
                'timelimit': '05'
            }
        
        lines = []
        lines.append("# the first map will be the one rotated to if the server is idle")
        lines.append('# entries are "mapname [minplayers] [maxplayers] [caplimit] [timelimit]"')
        lines.append("")
        
        for map_info in maps:
            map_name = map_info.get('map', 'unknown')
            line = f"{map_name} {default_params['minplayers']} {default_params['maxplayers']} "
            line += f"{default_params['caplimit']} {default_params['timelimit']}"
            lines.append(line)
        
        return '\n'.join(lines)
    
    @staticmethod
    def generate_ffa_config(maps, default_params=None):
        """Genera configuración para mapas FFA"""
        if default_params is None:
            default_params = {
                'minplayers': '00',
                'maxplayers': '04',
                'fraglimit': '25',
                'timelimit': '20'
            }
        
        lines = []
        lines.append("# the first map will be the one rotated to if the server is idle")
        lines.append('# entries are "mapname [minplayers] [maxplayers] [fraglimit] [timelimit]"')
        lines.append("")
        
        for map_info in maps:
            map_name = map_info.get('map', 'unknown')
            line = f"{map_name} {default_params['minplayers']} {default_params['maxplayers']} "
            line += f"{default_params['fraglimit']} {default_params['timelimit']}"
            lines.append(line)
        
        return '\n'.join(lines)
    
    @staticmethod
    def generate_ra3_config(maps, default_params=None):
        """Genera configuración para mapas RA3 (Rocket Arena 3)"""
        if default_params is None:
            default_params = {
                'minplayers': '00',
                'maxplayers': '99',
                'roundlimit': '00',
                'timelimit': '20',
                'arena': '4'
            }
        
        lines = []
        lines.append("# the first map will be the one rotated to if the server is idle")
        lines.append('# format: "mapname [minplayers] [maxplayers] [roundlimit] [timelimit] [arena]"')
        lines.append("")
        
        for map_info in maps:
            map_name = map_info.get('map', 'unknown')
            line = f"{map_name}\t\t{default_params['minplayers']}\t{default_params['maxplayers']}\t"
            line += f"{default_params['roundlimit']}\t{default_params['timelimit']}\t{default_params['arena']}"
            lines.append(line)
        
        return '\n'.join(lines)

    @staticmethod
    def generate_tourney_config(maps, default_params=None):
        """Genera configuración para mapas Tourney (1v1)"""
        if default_params is None:
            default_params = {
                'minplayers': '00',
                'maxplayers': '02',
                'fraglimit': '20',
                'timelimit': '10'
            }
        
        lines = []
        lines.append("# the first map will be the one rotated to if the server is idle")
        lines.append('# entries are "mapname [minplayers] [maxplayers] [fraglimit] [timelimit]"')
        lines.append("")
        
        for map_info in maps:
            map_name = map_info.get('map', 'unknown')
            line = f"{map_name} {default_params['minplayers']} {default_params['maxplayers']} "
            line += f"{default_params['fraglimit']} {default_params['timelimit']}"
            lines.append(line)
        
        return '\n'.join(lines)

# Inicializar parser
parser = ArenaParser()

# ---------------------------------------------------------------- next/prev (vstr) por server
# tipo del generador -> server CPMA (puerto rcon). La lista vstr se llama nextmap_<modo>.cfg y la ejecuta el server al arrancar.
TIPO_A_SERVER = {'ctf': 'ctf', 'tdm': 'tdm', 'ffa': 'ffa', '1v1': '1v1', 'tourney': '1v1', '2v2': '2v2',
                 'ca': 'ca', 'ft': 'ft', 'ra3': 'ra3'}
PUERTOS = {"ctf": 27964, "tdm": 27963, "ft": 27966, "ra3": 27967, "2v2": 27962, "ca": 27965, "ffa": 27960, "1v1": 27961}
# archivo de rotación que de verdad lee cada server (seta map "...") ademas del .txt
ARCHIVO_SERVER = {'ctf': 'ctfmaps.cfg', 'tdm': 'tdmmaps.cfg'}
# dónde corren los servers (para rcon): config.json "q3_host", o variable Q3_HOST, o esta misma máquina
Q3_HOST = os.environ.get('Q3_HOST') or config.get('q3_host') or '127.0.0.1'
QUAKE3 = os.path.dirname(os.path.dirname(OUTPUT_PATH.rstrip('/')))   # /quake3


def seleccionar(maps, params):
    """Mapas sin repetir (el mismo mapa puede venir en varios pk3) y sin los destildados, en el orden del escaneo."""
    fuera = {m.lower() for m in (params or {}).get('excluded_maps', [])}
    vistos, out = set(), []
    for m in maps:
        nombre = m.get('map', '')
        if nombre and nombre.lower() not in vistos and nombre.lower() not in fuera:
            vistos.add(nombre.lower())
            out.append(m)
    return sorted(out, key=lambda m: m.get('map', '').lower())   # alfabético: next/prev predecible


def baneados(maps, params):
    """Los mapas destildados (sin repetir, alfabético): van al archivo con minplayers -1 (convención CPMA)."""
    fuera = {m.lower() for m in (params or {}).get('excluded_maps', [])}
    return sorted({m.get('map', '') for m in maps if m.get('map', '').lower() in fuera}, key=str.lower)


def agregar_baneados(contenido, nombres, params, map_type):
    """Agrega al final los mapas excluidos con minplayers -1: no rotan y no se pueden votar aunque map_restrict sea 0."""
    if not nombres:
        return contenido
    p = params or {}
    limite = p.get('caplimit') or p.get('roundlimit') or p.get('fraglimit') or '00'
    maxp, tiempo = p.get('maxplayers', '00'), p.get('timelimit', '00')
    lineas = ['', '', '# excluidos desde el generador: minplayers -1 = "banned", no rotan ni se pueden votar']
    for n in nombres:
        if map_type == 'ra3':
            lineas.append(f"{n}\t\t-1\t{maxp}\t{limite}\t{tiempo}\t{p.get('arena', '4')}")
        else:
            lineas.append(f"{n} -1 {maxp} {limite} {tiempo}")
    return contenido + '\n'.join(lineas)


def respaldar(ruta):
    """Copia el archivo a cfg-maps/_respaldo/ antes de pisarlo."""
    if os.path.exists(ruta):
        dest = os.path.join(os.path.dirname(ruta), '_respaldo')
        os.makedirs(dest, exist_ok=True)
        shutil.copy2(ruta, os.path.join(dest, f"{os.path.basename(ruta)}.{datetime.now():%Y%m%d-%H%M%S}"))


def cfg_server(modo):
    try:
        return open(os.path.join(QUAKE3, 'cpma', 'cfg', f'yimq3a-cpma-{modo}-server-gemini.cfg'), errors='replace').read()
    except OSError:
        return ''


def generar_nextmap(modo, mapas):
    """Misma lógica que scripts/generar_nextmap.py: vN, actual, siguiente/next/nextmap, anterior/prev, volver."""
    n = len(mapas)
    sig = lambda i: f"v{i % n + 1}"
    ant = lambda i: f"v{(i - 2) % n + 1}"
    out = [f"// Rotación manual (vstr chain) para {modo.upper()} -- {n} mapas, generado por el Map Config Generator {datetime.now():%Y-%m-%d %H:%M}",
           "// /rcon vstr siguiente   (o next / nextmap)  -> pasa al próximo mapa de la lista",
           "// /rcon actual                               -> en qué mapa y número estás, ej. basesiege[1/42]",
           "// /rcon vstr v7                              -> salta directo al mapa número 7",
           "// /rcon vstr volver                          -> vuelve al mapa de antes del último salto",
           "// /rcon vstr anterior   (o prev)             -> el anterior en la lista", ""]
    for i, mp in enumerate(mapas, 1):
        out.append(f'set v{i} "vstr aca ; map {mp} ; set actual {mp}[{i}/{n}] ; set mapa_actual {mp} ; '
                   f'set siguiente vstr {sig(i)} ; set next vstr {sig(i)} ; set nextmap vstr {sig(i)} ; '
                   f'set anterior vstr {ant(i)} ; set prev vstr {ant(i)} ; set aca set volver vstr v{i}"')
    m = re.search(r'^\s*map\s+(\S+)', cfg_server(modo), re.M)
    ini = m.group(1) if m else None
    i0 = next((k for k, x in enumerate(mapas, 1) if ini and x.lower() == ini.lower()), 0)
    out += ["", f"// arranque: el server inicia en {ini or '?'}" + ("" if i0 else " (no está en la lista: el próximo es v1)"),
            f'set actual "{ini}[{i0}/{n}]"' if i0 else f'set actual "{ini or "?"}"',
            f'set mapa_actual "{ini or ""}"',
            *[f'set {c} "vstr {sig(i0) if i0 else "v1"}"' for c in ("siguiente", "next", "nextmap")],
            *[f'set {c} "vstr {ant(i0) if i0 else "v" + str(n)}"' for c in ("anterior", "prev")],
            f'set aca "set volver vstr v{i0}"' if i0 else 'set aca ""',
            f'set volver "vstr v{i0 if i0 else 1}"', ""]
    ruta = os.path.join(OUTPUT_PATH, f'nextmap_{modo}.cfg')
    respaldar(ruta)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write("\n".join(out))
    return ruta


def rcon(puerto, clave, comando):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    try:
        s.sendto(b"\xff\xff\xff\xffrcon " + clave.encode() + b" " + comando.encode(), (Q3_HOST, puerto))
        return s.recvfrom(16384)[0][4:].decode(errors='replace')
    except OSError:
        return ''
    finally:
        s.close()


def aplicar_en_vivo(modo, mapas):
    """Carga la lista nueva en el server corriendo y alinea los alias con el mapa actual. Por rcon el ';' no separa
    comandos, así que va un set por vez. El watcher después los mantiene al día en cada cambio de mapa."""
    m = re.search(r'rconpassword\s+"([^"]+)"', cfg_server(modo))
    if not m:
        return 'sin rconpassword en el cfg del server'
    clave, puerto = m.group(1), PUERTOS[modo]
    if not rcon(puerto, clave, f"exec cfg-maps/nextmap_{modo}.cfg"):
        return f'el server {modo} no respondió (¿apagado?)'
    r = re.search(r'"mapname" is:"([^"^]+)', rcon(puerto, clave, "mapname"))
    actual = r.group(1) if r else None
    n = len(mapas)
    idx = next((i for i, x in enumerate(mapas) if actual and x.lower() == actual.lower()), None)
    if idx is None:
        for c in (f"set actual {actual}[fuera_de_lista]", f"set mapa_actual {actual}"):
            rcon(puerto, clave, c)
        return f'aplicado; el server está en {actual}, que no está en la lista: next = v1'
    sig, prev = f"v{(idx + 1) % n + 1}", f"v{(idx - 1) % n + 1}"
    for c in (f"set actual {mapas[idx]}[{idx + 1}/{n}]", f"set mapa_actual {mapas[idx]}", f"set siguiente vstr {sig}",
              f"set next vstr {sig}", f"set nextmap vstr {sig}", f"set anterior vstr {prev}", f"set prev vstr {prev}",
              f"set aca set volver vstr v{idx + 1}"):
        rcon(puerto, clave, c)
    return f'aplicado en vivo: está en {mapas[idx]} [{idx + 1}/{n}], next = {mapas[(idx + 1) % n]}, prev = {mapas[(idx - 1) % n]}'

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/scan')
def scan_maps():
    """Escanea los archivos .pk3 y devuelve los mapas encontrados"""
    try:
        all_maps = parser.scan_pk3_files(BASEQ3_PATH)
        
        return jsonify({
            'success': True,
            'total_maps': len(all_maps),
            'maps_by_type': {
                type_name: [
                    {
                        'map': m.get('map'),
                        'longname': m.get('longname', ''),
                        'source_pk3': m.get('source_pk3', '')
                    } for m in maps
                ]
                for type_name, maps in parser.maps_by_type.items()
            },
            'counts': {type_name: len(maps) for type_name, maps in parser.maps_by_type.items()}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtiene la configuración actual"""
    return jsonify({
        'success': True,
        'baseq3_path': BASEQ3_PATH,
        'output_path': OUTPUT_PATH,
        'ra3_path': RA3_PATH
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """Actualiza la configuración"""
    try:
        global BASEQ3_PATH, OUTPUT_PATH, RA3_PATH
        data = request.json
        
        baseq3_path = data.get('baseq3_path', BASEQ3_PATH)
        output_path = data.get('output_path', OUTPUT_PATH)
        ra3_path = data.get('ra3_path', RA3_PATH)
        
        # Validar que las rutas existen
        if not os.path.exists(baseq3_path):
            return jsonify({
                'success': False,
                'error': f'La ruta de baseq3 no existe: {baseq3_path}'
            }), 400
        
        if not os.path.exists(output_path):
            return jsonify({
                'success': False,
                'error': f'La ruta de salida no existe: {output_path}'
            }), 400
        
        if not os.path.exists(ra3_path):
            return jsonify({
                'success': False,
                'error': f'La ruta de RA3 no existe: {ra3_path}'
            }), 400
        
        # Guardar configuración
        new_config = dict(config, baseq3_path=baseq3_path, output_path=output_path, ra3_path=ra3_path)
        save_config(new_config)
        
        # Actualizar variables globales
        BASEQ3_PATH = baseq3_path
        OUTPUT_PATH = output_path
        RA3_PATH = ra3_path
        
        return jsonify({
            'success': True,
            'message': 'Configuración actualizada',
            'baseq3_path': BASEQ3_PATH,
            'output_path': OUTPUT_PATH,
            'ra3_path': RA3_PATH
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/actual/<map_type>')
def lista_actual(map_type):
    """Mapas de la lista vstr que hoy usa el server de ese tipo (para tildar lo mismo)."""
    modo = TIPO_A_SERVER.get(map_type)
    if not modo:
        return jsonify({'success': False, 'error': 'Ese tipo no tiene server propio'}), 404
    try:
        txt = open(os.path.join(OUTPUT_PATH, f'nextmap_{modo}.cfg'), errors='replace').read()
    except OSError:
        return jsonify({'success': True, 'server': modo, 'mapas': []})
    pares = sorted((int(a), b) for a, b in re.findall(r'^set v(\d+) "(?:vstr aca ; )?map (\S+)', txt, re.M))
    return jsonify({'success': True, 'server': modo, 'mapas': [b for _, b in pares]})


@app.route('/api/generate', methods=['POST'])
def generate_configs():
    """Genera los archivos de configuración según los parámetros proporcionados"""
    try:
        data = request.json
        map_type = data.get('type')
        params = data.get('params', {})
        maps = seleccionar(parser.maps_by_type.get(map_type, []), params)
        if not maps:
            return jsonify({'success': False, 'error': 'No hay mapas seleccionados (¿escaneaste primero?)'}), 400
        
        generator = ConfigGenerator()
        
        # Mapeo de tipos a nombres de archivo y generadores
        type_config = {
            'ctf': ('ctfmaps.txt', 'ctf'),
            'ctfs': ('ctfsmaps.txt', 'ctf'),
            'ffa': ('ffamaps.txt', 'ffa'),
            'tourney': ('tourneymaps.txt', 'tourney'),
            '1v1': ('1v1maps.txt', 'tourney'),
            'ra': ('mamaps.txt', 'ffa'),
            'ra3': ('ra3maps.txt', 'ra3'),
            'team': ('teammaps.txt', 'ffa'),
            'tdm': ('tdmmaps.txt', 'ffa'),
            'hm': ('hmmaps.txt', 'ffa'),
            'da': ('damaps.txt', 'tourney'),
            'ca': ('camaps.txt', 'ffa'),
            'ft': ('ftmaps.txt', 'ffa'),
            'ntf': ('ntfmaps.txt', 'ctf'),
            '2v2': ('2v2maps.txt', 'tourney'),
            'ftag': ('ftagmaps.txt', 'ffa')
        }
        
        if map_type in type_config:
            filename, generator_type = type_config[map_type]
            if generator_type == 'ctf':
                config_content = generator.generate_ctf_config(maps, params)
            elif generator_type == 'tourney':
                config_content = generator.generate_tourney_config(maps, params)
            elif generator_type == 'ra3':
                config_content = generator.generate_ra3_config(maps, params)
            else:  # ffa
                config_content = generator.generate_ffa_config(maps, params)
        else:
            # Genérico para otros tipos
            config_content = generator.generate_ffa_config(maps, params)
            filename = f'{map_type}maps.txt'
        
        config_content = agregar_baneados(config_content, baneados(parser.maps_by_type.get(map_type, []), params), params, map_type)

        # Guardar archivo (con respaldo del anterior)
        output_file = os.path.join(OUTPUT_PATH, filename)
        os.makedirs(OUTPUT_PATH, exist_ok=True)
        respaldar(output_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        extra = []
        # el server lee el .cfg (seta map "ctfmaps.cfg"), no el .txt
        if map_type in ARCHIVO_SERVER:
            ruta_srv = os.path.join(OUTPUT_PATH, ARCHIVO_SERVER[map_type])
            respaldar(ruta_srv)
            with open(ruta_srv, 'w', encoding='utf-8') as f:
                f.write(config_content)
            extra.append(f'rotación del server: {ARCHIVO_SERVER[map_type]}')
        nextmap = None
        modo = TIPO_A_SERVER.get(map_type)
        if params.get('nextmap', True) and modo:
            nombres = [m['map'] for m in maps]
            generar_nextmap(modo, nombres)
            nextmap = {'archivo': f'nextmap_{modo}.cfg', 'server': modo, 'mapas': len(nombres)}
            if params.get('aplicar', True):
                nextmap['vivo'] = aplicar_en_vivo(modo, nombres)
        
        # Para RA3, guardar también en cfg-ra3
        if map_type == 'ra3':
            ra3_file = os.path.join(RA3_PATH, filename)
            os.makedirs(RA3_PATH, exist_ok=True)
            with open(ra3_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': output_file,
            'maps_count': len(maps),
            'extra': extra,
            'nextmap': nextmap,
            'preview': config_content[:500]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/preview', methods=['POST'])
def preview_config():
    """Previsualiza el contenido de la configuración sin guardarla"""
    try:
        data = request.json
        map_type = data.get('type')
        params = data.get('params', {})
        maps = seleccionar(parser.maps_by_type.get(map_type, []), params)
        
        generator = ConfigGenerator()
        
        if map_type == 'ctf' or map_type == 'ctfs':
            config_content = generator.generate_ctf_config(maps, params)
        elif map_type == 'tourney' or map_type == '1v1' or map_type == 'da' or map_type == '2v2':
            config_content = generator.generate_tourney_config(maps, params)
        elif map_type == 'ra3':
            config_content = generator.generate_ra3_config(maps, params)
        else:
            config_content = generator.generate_ffa_config(maps, params)
        config_content = agregar_baneados(config_content, baneados(parser.maps_by_type.get(map_type, []), params), params, map_type)
        
        return jsonify({
            'success': True,
            'content': config_content,
            'maps_count': len(maps)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def find_available_port(start_port=5000, max_attempts=10):
    """Encuentra un puerto disponible a partir del puerto inicial"""
    for port in range(start_port, start_port + max_attempts):
        try:
            # Intenta crear un socket en el puerto
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    # Si no encuentra ninguno disponible, retorna el original
    return start_port

if __name__ == '__main__':
    # Obtener IP de LAN
    lan_ip = get_lan_ip()
    
    # Encontrar puerto disponible
    port = find_available_port(5000)
    print(f"\n{'='*70}")
    print(f"  ✅ Q3 MAP CONFIG GENERATOR")
    print(f"{'='*70}")
    print(f"  🖥️  LOCAL:  http://127.0.0.1:{port}")
    print(f"  🌐 RED:    http://{lan_ip}:{port}")
    print(f"  📁 baseq3: {BASEQ3_PATH}")
    print(f"  💾 output: {OUTPUT_PATH}")
    print(f"  🎮 RA3:    {RA3_PATH}")
    print(f"{'='*70}\n")
    # el modo debug de Flask permite ejecutar código desde el navegador: solo si se pide (Q3CG_DEBUG=1)
    app.run(debug=os.environ.get('Q3CG_DEBUG') == '1', host='0.0.0.0', port=port)
