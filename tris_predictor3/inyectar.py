"""
inyectar.py — Actualiza los datos embebidos en index.html desde tris_data.json
Uso: python inyectar.py

Ejecutar DESPUÉS de actualizar.py cada vez que tengas un Excel más reciente.
"""
import json, sys
from pathlib import Path

HTML_PATH = Path("index.html")
JSON_PATH = Path("data/tris_data.json")

def main():
    # Verificar que existen los archivos
    if not HTML_PATH.exists():
        print(f"✗ No se encontró {HTML_PATH}")
        sys.exit(1)
    if not JSON_PATH.exists():
        print(f"✗ No se encontró {JSON_PATH}")
        print("  Ejecuta primero: python actualizar.py")
        sys.exit(1)

    print(f"Leyendo {JSON_PATH}...")
    with open(JSON_PATH, encoding="utf-8") as f:
        new_json = f.read().strip()

    # Validar que es JSON válido
    try:
        data = json.loads(new_json)
        n_sorteos = data.get("par_final", {}).get("n", "?")
        ultima    = data.get("par_final", {}).get("ultimos_10", ["?"])[-1]
        print(f"✓ JSON válido — {n_sorteos} sorteos, último par final: {ultima}")
    except Exception as e:
        print(f"✗ JSON inválido: {e}")
        sys.exit(1)

    print(f"Leyendo {HTML_PATH}...")
    with open(HTML_PATH, encoding="utf-8") as f:
        html = f.read()

    # Encontrar el bloque const ALL = {...}
    marker = "const ALL = "
    start  = html.find(marker)
    if start < 0:
        print("✗ No se encontró 'const ALL = ' en el HTML")
        print("  Asegúrate de que estás usando index.html generado por este proyecto")
        sys.exit(1)

    # Encontrar el cierre del objeto JSON contando llaves
    pos = start + len(marker)
    depth = 0
    i = pos
    while i < len(html):
        if   html[i] == '{': depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0:
                json_end = i + 1
                break
        i += 1
    else:
        print("✗ No se pudo encontrar el cierre del JSON en el HTML")
        sys.exit(1)

    old_size = (json_end - start - len(marker)) // 1024
    new_size = len(new_json) // 1024
    print(f"  JSON anterior: ~{old_size} KB")
    print(f"  JSON nuevo:    ~{new_size} KB")

    # Hacer backup del HTML anterior
    backup = HTML_PATH.with_suffix(".html.bak")
    with open(backup, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Backup guardado en: {backup.name}")

    # Reemplazar
    html_new = html[:start] + marker + new_json + html[json_end:]

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_new)

    print(f"\n✓ {HTML_PATH} actualizado correctamente")
    print(f"  Tamaño final: {len(html_new)//1024} KB")
    print(f"  Recarga la página en el navegador para ver los cambios")

if __name__ == "__main__":
    main()
