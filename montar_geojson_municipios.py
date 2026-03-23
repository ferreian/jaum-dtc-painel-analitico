"""
Script para gerar municipios_br.json usando geobr.
Execute na raiz do projeto:
    python montar_geojson_municipios.py
"""
import sys, json
from pathlib import Path

DESTINO = Path(__file__).parent / "assets" / "municipios_br.json"
DESTINO.parent.mkdir(exist_ok=True)

try:
    import geobr
    import geopandas as gpd
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "geobr", "geopandas"])
    import geobr
    import geopandas as gpd

print("Baixando municipios...")
mun = geobr.read_municipality(code_muni="all", year=2020)
print(f"Total: {len(mun)} municipios")

# Reprojetar e simplificar geometria para reduzir tamanho
mun = mun.to_crs(epsg=4326)
print("Simplificando geometrias...")
mun["geometry"] = mun["geometry"].simplify(tolerance=0.01, preserve_topology=True)

# Salvar como GeoJSON diretamente (sem passar por json.loads)
tmp = DESTINO.with_suffix(".tmp")
print("Salvando...")
mun.to_file(str(tmp), driver="GeoJSON", encoding="utf-8")

# Reabrir e adicionar mun_id + normalizar nomes
print("Normalizando propriedades...")
with open(tmp, "r", encoding="utf-8") as f:
    gj = json.load(f)

for i, feat in enumerate(gj["features"]):
    p = feat.get("properties", {})
    feat["properties"]["mun_id"]    = str(i)
    feat["properties"]["geocodigo"] = str(p.get("code_muni",""))
    feat["properties"]["nome"]      = str(p.get("name_muni",""))

with open(DESTINO, "w", encoding="utf-8") as f:
    json.dump(gj, f, ensure_ascii=False)

tmp.unlink(missing_ok=True)

sz = DESTINO.stat().st_size / 1024 / 1024
print(f"\nSalvo em: {DESTINO}  ({sz:.1f} MB)")
print(f"Exemplo: {json.dumps(gj['features'][0]['properties'], ensure_ascii=False)}")
