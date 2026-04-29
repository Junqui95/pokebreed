"""
Sincroniza la base de datos con los JSONs de data/.
Ejecutar cada vez que se modifiquen los JSONs.
"""
import subprocess
import sys

scripts = [
    ("seed_evolucion.py",  "Especies raíz, formas finales y evoluciones"),
    ("seed_recetas.py",    "Recetas de breeding"),
]

print("🔄 Sincronizando base de datos con JSONs...\n")
for script, descripcion in scripts:
    print(f"── {descripcion}")
    resultado = subprocess.run(
        [sys.executable, script],
        capture_output=False
    )
    if resultado.returncode != 0:
        print(f"❌ Error en {script}, abortando.")
        sys.exit(1)
    print()

print("✅ Base de datos sincronizada.")