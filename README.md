# Nieuwe merken (SEO/SEA)

Genereer een statische pagina met nieuwe merken uit PrestaShop en host via GitHub Pages.

## Snel starten

1) Vereisten
- Python 3.9+
- `pip install -r requirements.txt`
- Maak `.env` op basis van `.env.example` (read-only DB user).

2) Data genereren (lokaal)
```bash
python scripts/build.py --since 2025-10-01 --until 2027-01-01 --shop-id 4 --min-products 0
```
Dit schrijft `docs/data.json` en `docs/data.csv`.

3) Publiceren
```bash
git add docs/data.* && git commit -m "Update data" && git push
```
Zet GitHub Pages aan op de `docs/` folder (Settings → Pages → Deploy from a branch → main → /docs).

4) Delen
- De pagina staat op: https://<user>.github.io/<repo>/
- CSV: `https://<user>.github.io/<repo>/data.csv`

## Aanpassen
- Shop wisselen: `--shop-id` of `SHOP_ID` in `.env`.
- Periode: `--since` / `--until` (einddatum is exclusief).
- Min. producten: `--min-products`.

## Opmerking
De query telt alle producten van een merk. Het aantal actieve en zichtbare producten wordt als aparte kolom weergegeven in de output.