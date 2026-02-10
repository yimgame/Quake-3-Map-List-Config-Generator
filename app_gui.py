"""
Q3 Map List Config Generator - Versión GUI
Aplicación Flask con interfaz gráfica integrada
"""
import os
import sys
import json
import zipfile
import re
import socket
import threading
import webview
import webbrowser
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_file
from collections import defaultdict

app = Flask(__name__)

# Cargar configuración desde archivo
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    """Carga la configuración desde config.json"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'baseq3_path': r"G:\Games\Quake3\baseq3",
        'output_path': r"G:\Games\Quake3\cpma\cfg-maps",
        'ra3_path': r"G:\Games\Quake3\cpma\cfg-ra3"
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
RA3_PATH = config.get('ra3_path', r"G:\Games\Quake3\cpma\cfg-ra3")

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
        
        # Clasificar por tipo (DINÁMICO - acepta cualquier tipo)
        self.maps_by_type.clear()
        
        for map_info in all_maps:
            types = map_info.get('type', '').lower().split()
            for type_name in types:
                if type_name:  # Aceptar cualquier tipo no vacío
                    self.maps_by_type[type_name].append(map_info)
                # Mapear variaciones conocidas
                if type_name == 'tourney':
                    self.maps_by_type['1v1'].append(map_info)
                elif type_name == '1v1':
                    self.maps_by_type['tourney'].append(map_info)
        
        return all_maps

class ConfigGenerator:
    """Generador de archivos de configuración de mapas"""
    
    @staticmethod
    def determine_generator_type(map_type):
        """Determina automáticamente qué generador usar basándose en el tipo de mapa"""
        # CTF-based modes: usan caplimit
        ctf_modes = ['ctf', 'ctfs', 'ntf']
        if map_type in ctf_modes:
            return 'ctf'
        
        # Tourney/Duel modes: duelos 1v1 o 2v2
        tourney_modes = ['tourney', '1v1', 'da', '2v2']
        if map_type in tourney_modes:
            return 'tourney'
        
        # RA3: modo especial con arena field
        if map_type == 'ra3':
            return 'ra3'
        
        # Default: FFA-based (fraglimit) para todo lo demás
        # Incluye: ffa, team, tdm, ra, hm, ca, ft, ftag, y cualquier modo nuevo
        return 'ffa'
    
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
        
        excluded_maps = default_params.pop('excluded_maps', [])
        
        lines = []
        lines.append("# the first map will be the one rotated to if the server is idle")
        lines.append('# entries are "mapname [minplayers] [maxplayers] [caplimit] [timelimit]"')
        lines.append('# entries with minplayers -1 are "banned" and can\'t be voted in even with map_restrict 0')
        lines.append("")
        
        for map_info in maps:
            map_name = map_info.get('map', 'unknown')
            # Si el mapa está excluido, usar minplayers -1
            if map_name in excluded_maps:
                line = f"{map_name} -1 {default_params['maxplayers']} "
            else:
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
        
        excluded_maps = default_params.pop('excluded_maps', [])
        
        lines = []
        lines.append("# the first map will be the one rotated to if the server is idle")
        lines.append('# entries are "mapname [minplayers] [maxplayers] [fraglimit] [timelimit]"')
        lines.append('# entries with minplayers -1 are "banned" and can\'t be voted in even with map_restrict 0')
        lines.append("")
        
        for map_info in maps:
            map_name = map_info.get('map', 'unknown')
            # Si el mapa está excluido, usar minplayers -1
            if map_name in excluded_maps:
                line = f"{map_name} -1 {default_params['maxplayers']} "
            else:
                line = f"{map_name} {default_params['minplayers']} {default_params['maxplayers']} "
            line += f"{default_params['fraglimit']} {default_params['timelimit']}"
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
        
        excluded_maps = default_params.pop('excluded_maps', [])
        
        lines = []
        lines.append("# the first map will be the one rotated to if the server is idle")
        lines.append('# entries are "mapname [minplayers] [maxplayers] [fraglimit] [timelimit]"')
        lines.append('# entries with minplayers -1 are "banned" and can\'t be voted in even with map_restrict 0')
        lines.append("")
        
        for map_info in maps:
            map_name = map_info.get('map', 'unknown')
            # Si el mapa está excluido, usar minplayers -1
            if map_name in excluded_maps:
                line = f"{map_name} -1 {default_params['maxplayers']} "
            else:
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
        
        excluded_maps = default_params.pop('excluded_maps', [])
        
        lines = []
        lines.append("# the first map will be the one rotated to if the server is idle")
        lines.append('# format: "mapname [minplayers] [maxplayers] [roundlimit] [timelimit] [arena]"')
        lines.append('# entries with minplayers -1 are "banned" and can\'t be voted in even with map_restrict 0')
        lines.append("")
        
        for map_info in maps:
            map_name = map_info.get('map', 'unknown')
            # Si el mapa está excluido, usar minplayers -1
            if map_name in excluded_maps:
                line = f"{map_name}\t\t-1\t{default_params['maxplayers']}\t"
            else:
                line = f"{map_name}\t\t{default_params['minplayers']}\t{default_params['maxplayers']}\t"
            line += f"{default_params['roundlimit']}\t{default_params['timelimit']}\t{default_params['arena']}"
            lines.append(line)
        
        return '\n'.join(lines)

# Inicializar parser
parser = ArenaParser()

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
        new_config = {
            'baseq3_path': baseq3_path,
            'output_path': output_path,
            'ra3_path': ra3_path
        }
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

@app.route('/api/generate', methods=['POST'])
def generate_configs():
    """Genera los archivos de configuración según los parámetros proporcionados"""
    try:
        data = request.json
        map_type = data.get('type')
        params = data.get('params', {})
        maps = parser.maps_by_type.get(map_type, [])
        
        generator = ConfigGenerator()
        
        # Mapeo de tipos conocidos a nombres de archivo
        # Para tipos nuevos/desconocidos, se genera automáticamente: {type}maps.txt
        filename_map = {
            'ctf': 'ctfmaps.txt',
            'ctfs': 'ctfsmaps.txt',
            'ffa': 'ffamaps.txt',
            'tourney': 'tourneymaps.txt',
            '1v1': '1v1maps.txt',
            'ra': 'mamaps.txt',
            'ra3': 'ra3maps.txt',
            'team': 'teammaps.txt',
            'tdm': 'tdmmaps.txt',
            'hm': 'hmmaps.txt',
            'da': 'damaps.txt',
            'ca': 'camaps.txt',
            'ft': 'ftmaps.txt',
            'ntf': 'ntfmaps.txt',
            '2v2': '2v2maps.txt',
            'ftag': 'ftagmaps.txt'
        }
        
        # Determinar nombre de archivo
        filename = filename_map.get(map_type, f'{map_type}maps.txt')
        
        # Determinar automáticamente qué generador usar
        generator_type = generator.determine_generator_type(map_type)
        
        # Generar contenido según el tipo de generador
        if generator_type == 'ctf':
            config_content = generator.generate_ctf_config(maps, params)
        elif generator_type == 'tourney':
            config_content = generator.generate_tourney_config(maps, params)
        elif generator_type == 'ra3':
            config_content = generator.generate_ra3_config(maps, params)
        else:  # ffa (default para modos nuevos)
            config_content = generator.generate_ffa_config(maps, params)
        
        # Guardar archivo
        output_file = os.path.join(OUTPUT_PATH, filename)
        os.makedirs(OUTPUT_PATH, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
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
        maps = parser.maps_by_type.get(map_type, [])
        
        generator = ConfigGenerator()
        
        # Determinar automáticamente qué generador usar
        generator_type = generator.determine_generator_type(map_type)
        
        # Generar contenido según el tipo
        if generator_type == 'ctf':
            config_content = generator.generate_ctf_config(maps, params)
        elif generator_type == 'tourney':
            config_content = generator.generate_tourney_config(maps, params)
        elif generator_type == 'ra3':
            config_content = generator.generate_ra3_config(maps, params)
        else:  # ffa (default para modos nuevos)
            config_content = generator.generate_ffa_config(maps, params)
        
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

class Api:
    """API para comunicación entre webview y Flask"""
    def open_in_browser(self, url):
        """Abre la aplicación en el navegador externo"""
        webbrowser.open(url)

def start_flask(port):
    """Inicia el servidor Flask en un thread separado"""
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False, threaded=True)

if __name__ == '__main__':
    # Obtener IP de LAN
    lan_ip = get_lan_ip()
    
    # Encontrar puerto disponible
    port = find_available_port(5000)
    localhost_url = f'http://127.0.0.1:{port}'
    lan_url = f'http://{lan_ip}:{port}'
    
    # Iniciar Flask en un thread
    flask_thread = threading.Thread(target=start_flask, args=(port,), daemon=True)
    flask_thread.start()
    
    # Esperar un momento para que Flask inicie
    import time
    time.sleep(1.5)
    
    print(f"\n{'='*70}")
    print(f"  [OK] Q3 MAP LIST CONFIG GENERATOR")
    print(f"{'='*70}")
    print(f"  [PC]  LOCAL:  {localhost_url}")
    print(f"  [NET] RED:    {lan_url}")
    print(f"  [DIR] baseq3: {BASEQ3_PATH}")
    print(f"  [SAVE] output: {OUTPUT_PATH}")
    print(f"  [GAME] RA3:    {RA3_PATH}")
    print(f"{'='*70}\n")
    
    # Intentar abrir ventana GUI
    try:
        # Crear API para comunicación con JavaScript
        api = Api()
        
        print("  [WINDOW] Abriendo ventana GUI...")
        
        # Crear ventana GUI con la aplicación embebida
        window = webview.create_window(
            'Q3 Map List Config Generator',
            localhost_url,
            width=1200,
            height=800,
            resizable=True,
            js_api=api
        )
        
        # Iniciar la GUI
        webview.start(debug=False)
    except Exception as e:
        print(f"\n  [WARN] No se pudo abrir la ventana GUI: {e}")
        print(f"  [NET] Abriendo navegador web en su lugar...")
        print(f"  [INFO] Puedes acceder desde la red usando: {lan_url}")
        webbrowser.open(localhost_url)
        print(f"\n  [OK] Aplicacion disponible en: {url}")
        print(f"  Presiona Ctrl+C para detener el servidor\n")
        
        # Mantener el servidor corriendo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n  [BYE] Cerrando servidor...")
            sys.exit(0)
