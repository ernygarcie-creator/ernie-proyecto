# TRIS — Análisis Estadístico Completo

Herramienta de análisis estadístico para el sorteo Tris de Pronósticos para la Asistencia Pública.

## Estructura del proyecto

```
tris/
├── index.html          ← La app (66 KB, sin datos)
├── data/
│   └── tris_data.json  ← Los datos calculados (1.2 MB, actualizable)
├── actualizar.py       ← Script para recalcular los datos
└── README.md
```

## Cómo usar en local (VS Code)

1. Instala la extensión **Live Server** en VS Code
2. Haz clic derecho en `index.html` → **Open with Live Server**
3. La app abre en `http://localhost:5500`

> ⚠️ No puedes abrir index.html directo desde el explorador de archivos  
> (doble clic) porque el navegador bloquea el fetch() por seguridad.  
> **Necesitas un servidor local** — Live Server es el más sencillo.

## Cómo actualizar los datos

Cuando tengas un histórico más reciente:

1. Coloca el nuevo Excel en la misma carpeta que `actualizar.py`
2. Edita la variable `EXCEL_PATH` en `actualizar.py`
3. Ejecuta: `python actualizar.py`
4. El script regenera `data/tris_data.json` automáticamente
5. Recarga la app en el navegador

## Modalidades disponibles

| Modalidad | Combinaciones | Descripción |
|---|---|---|
| Número Inicial | 10 (0–9) | Primer dígito del sorteo |
| Número Final | 10 (0–9) | Último dígito del sorteo |
| Par Inicial | 100 (00–99) | Primeros dos dígitos |
| Par Final | 100 (00–99) | Últimos dos dígitos ← **más analizado** |
| Directa 3 | 1,000 | Últimos tres dígitos |
| Directa 4 | 10,000 | Últimos cuatro dígitos |
| Directa 5 | 100,000 | Los cinco dígitos |

## Datos históricos

- **32,792 sorteos** registrados (1996-07-20 → 2026-03-12)
- Era 4 cifras: hasta 2007-09-02
- Era 5 cifras: desde 2007-09-03

## Nota importante

Esta herramienta es **informativa, no predictiva**. El Tris es un juego  
estadísticamente aleatorio. La única ventaja estadística confirmada es  
la distribución de sumas (+0.88% al jugar en zona 5–13 para par final).
