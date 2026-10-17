# Q3 Map Config Generator - Changelog

## [v2.2] - 2026-10-17 - Next/Prev (vstr) por server, tipos unificados y exclusión real

### ✨ Nuevas Características
- **Lista next/prev (vstr) automática**: al generar, arma `cfg-maps/nextmap_<modo>.cfg` con la misma lista y orden
  (`v1..vN`, `actual`, `siguiente`/`next`/`nextmap`, `anterior`/`prev`, `volver`)
- **Aplicar en vivo**: carga la lista en el server corriendo por rcon (lee `rconpassword` del cfg del server) y alinea
  los alias con el mapa actual, sin reiniciar. Host de los servers configurable con la variable `Q3_HOST`
- **Tildar la lista actual del server**: marca los mismos mapas que ya usa el server, para partir de ahí
- **Archivo que lee el server**: además del `.txt`, escribe `ctfmaps.cfg` / `tdmmaps.cfg` (los que usa `seta map`)
- **Respaldo automático**: antes de pisar un archivo guarda copia en `cfg-maps/_respaldo/<archivo>.<fecha>`

### 🐛 Correcciones
- Los mapas destildados ahora sí se excluyen (antes se ignoraba `excluded_maps`) y salen al final con
  `minplayers -1` (baneados, como decía la v2.1)
- Sin mapas repetidos cuando el mismo mapa viene en varios `.pk3`
- `tourney` y `1v1` unificados en una sola tarjeta "1v1 - Duel / Tourney"; `team` dentro de `tdm`
- Orden alfabético de los mapas (next/prev predecible)
- Rutas por defecto de Linux/Docker (`/quake3/...`), las del server

### 🎨 UI
- Opciones next/prev y "aplicar en vivo" en cada tarjeta, mensaje con el resultado (mapa actual, next y prev)

## [v2.1] - 2026-02-10 - Sistema de Exclusión de Mapas con Checkboxes

### ✨ Nuevas Características
- **Checkboxes individuales por mapa**: Cada mapa ahora tiene un checkbox para incluirlo/excluirlo
- **Seleccionar/Deseleccionar todo**: Checkbox maestro en cada tarjeta para control rápido
- **Mapas excluidos con minplayers -1**: Los mapas desmarcados se exportan con `minplayers -1` (baneados)
- **Indicador visual de exclusión**: Mapas desmarcados se muestran con opacidad reducida
- **Contador dinámico**: Muestra cantidad de mapas seleccionados vs excluidos en tiempo real
- **Estado intermedio**: Checkbox maestro muestra estado intermedio cuando hay selección parcial

### 🎯 Sistema de Banneo de Mapas
Los mapas desmarcados se generan con `minplayers -1` siguiendo la convención de CPMA:
```
# entries with minplayers -1 are "banned"
# and can't be voted in even with map_restrict 0
```

**Casos de uso:**
- Excluir mapas de mala calidad incluidos en pk3 con otros buenos
- Disable mapas que reclaman soportar un modo pero no lo hacen (ej. CTF sin flags)
- Gestión flexible sin necesidad de borrar archivos pk3

### 🎨 Mejoras UI/UX
- Estructura de mapas rediseñada con layout flex
- Mapas clicables: hacer click en el nombre también marca/desmarca
- Transiciones suaves en hover y cambio de estado
- Mejor contraste visual entre mapas activos y excluidos
- Stats actualizados automáticamente al cambiar selección

### 🔧 Mejoras Backend
- Todas las funciones generadoras actualizadas (CTF, FFA, Tourney, RA3)
- Parámetro `excluded_maps` en configuración
- Comentarios explicativos en archivos generados
- Soporte completo para formatos: fraglimit, caplimit, roundlimit

### 📝 Formato de Salida
**Ejemplo de archivo generado:**
```
# entries with minplayers -1 are "banned" and can't be voted in
q3dm1       02  16  30  20
q3dm2       -1  16  30  20   # EXCLUIDO
q3dm3       02  16  30  20
```

---

## [v2.0] - 2026-02-10 - Sistema Dinámico de Detección de Modos

### ✨ Nuevas Características
- **Sistema dinámico de detección de modos de juego**: Ya no requiere configuración manual para cada modo nuevo
- **Auto-detección inteligente**: El sistema detecta automáticamente qué tipo de generador usar basándose en el nombre del modo:
  - Modos tipo CTF (contienen "ctf"): usan `caplimit`
  - Modos tipo Duel (contienen "duel", "1v1", "2v2", "tourney"): usan formato duel
  - Modos RA3: usan formato especial con campo `arena`
  - Otros modos: usan formato FFA con `fraglimit` por defecto

### 🔧 Mejoras Backend
- Eliminado filtro de tipos soportados - ahora acepta **cualquier tipo** que venga en los archivos `.arena`
- Nueva función `determine_generator_type()` que clasifica automáticamente el tipo de generador
- Generación automática de nombres de archivo: `{tipo}maps.txt`
- Código más mantenible y extensible

### 🎨 Mejoras Frontend
- **Stats dinámicos**: Muestra automáticamente todos los modos encontrados, no solo una lista fija
- **Tarjetas dinámicas**: Genera tarjetas de configuración para modos nuevos con valores por defecto inteligentes
- Etiquetas mejoradas para modos nuevos con indicador "(Auto-detected)"
- Ordenamiento alfabético de modos en panel de estadísticas

### 📋 Modos Preconfigurados (con configuraciones optimizadas)
- FFA, CTF, CTFS, Tourney, 1v1, 2v2
- Team, TDM, RA, RA3
- CA (Clan Arena), FT (Freeze Tag), HM (HoonyMode)
- DA (Duel Arena), NTF (No Team Flags), FTAG (Flag Tag)

### 🚀 Ventajas del Sistema Dinámico
1. **Extensibilidad**: Soporta modos futuros sin modificar código
2. **Flexibilidad**: Detecta modos custom de mapas de comunidad
3. **Automatización**: Elimina la necesidad de actualizar listas manualmente
4. **Compatibilidad**: Mantiene todas las configuraciones existentes

### 🔍 Ejemplo de Auto-Detección
```
Modo en .arena: "newctf"      → Detecta CTF → Genera con caplimit
Modo en .arena: "customduel"  → Detecta Duel → Genera con fraglimit (formato tourney)
Modo en .arena: "zombies"     → Default FFA → Genera con fraglimit
```

### 📦 Archivos Modificados
- `app_gui.py`: Sistema de clasificación dinámica y función `determine_generator_type()`
- `templates/index.html`: Generación dinámica de stats y tarjetas con detección inteligente

---

## [v1.0] - 2026-02-09 - Versión Inicial

### Características Originales
- Escaneo de archivos .pk3 y extracción de .arena
- Generación de configuraciones para 15+ modos de juego
- Interfaz web responsive con Flask
- GUI nativa con PyWebView
- Detección automática de puerto disponible (5000-5009)
- Detección de IP LAN para acceso en red
- Soporte RA3 con dual output path
- Ejecutable standalone sin dependencias Python
