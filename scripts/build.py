#!/usr/bin/env python3
import os, json, csv, argparse, datetime as dt, pathlib, re
import mysql.connector

ROOT = pathlib.Path(__file__).resolve().parent

def load_env():
    # Eenvoudige .env loader (geen extra dependency)
    env_path = ROOT / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        os.environ.setdefault(k, v)

def env(k, default=None):
    v = os.getenv(k)
    return v if v not in (None, "") else default

def connect():
    cfg = {
        "host": env("DB_HOST", "127.0.0.1"),
        "port": int(env("DB_PORT", "3306")),
        "user": env("DB_USER"),
        "password": env("DB_PASS"),
        "database": env("DB_NAME"),
        "charset": "utf8mb4",
        "use_unicode": True,
    }
    keymap = {"DB_USER":"user","DB_PASS":"password","DB_NAME":"database"}
    missing = [k for k in ("DB_USER","DB_PASS","DB_NAME") if not cfg.get(keymap[k])]
    if missing:
        raise SystemExit(f"Missing DB env vars: {', '.join(missing)} (see .env.example)")
    return mysql.connector.connect(**cfg)

def fetch_new_brands(conn, shop_id, start_date, end_date, min_products):
    # MySQL 5.7+ compatible (geen CTE). Alleen actieve/zichtbare producten in gekozen shop.
    sql = """
    SELECT
      pm.id_manufacturer,
      pm.name AS merknaam,
      lp.first_live_product_at,
      (
        SELECT COUNT(DISTINCT p2.id_product)
        FROM ps_product p2
        JOIN ps_product_shop s2
          ON s2.id_product = p2.id_product
         AND s2.id_shop = %s
         AND s2.active = 1
         AND s2.visibility <> 'none'
        WHERE p2.id_manufacturer = pm.id_manufacturer
      ) AS product_count
    FROM (
      SELECT
        p.id_manufacturer,
        MIN(p.date_add) AS first_live_product_at
      FROM ps_product p
      JOIN ps_product_shop s
        ON s.id_product = p.id_product
       AND s.id_shop = %s
       AND s.active = 1
       AND s.visibility <> 'none'
      GROUP BY p.id_manufacturer
    ) lp
    JOIN ps_manufacturer pm ON pm.id_manufacturer = lp.id_manufacturer
    WHERE lp.first_live_product_at >= %s
      AND lp.first_live_product_at <  %s
    HAVING product_count >= %s
    ORDER BY lp.first_live_product_at DESC
    """
    params = (shop_id, shop_id, start_date, end_date, min_products)
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows

def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def write_csv(path, items):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["merk", "eerste_product_live", "aantal_producten"])
        for r in items:
            w.writerow([r["merk"], r["eerste_product_live"], r["aantal_producten"]])

def main():
    load_env()

    ap = argparse.ArgumentParser(description="Genereer statische data voor Nieuwe Merken (SEO/SEA).")
    ap.add_argument("--shop-id", type=int, default=int(env("SHOP_ID", "4")), help="PrestaShop id_shop (default 4)")
    ap.add_argument("--since", default=None, help="Start YYYY-MM-DD (default 1 jan dit jaar)")
    ap.add_argument("--until", default=None, help="Eind YYYY-MM-DD (excl, default 1 jan volgend jaar)")
    ap.add_argument("--min-products", type=int, default=int(env("MIN_PRODUCTS", "0")), help="Min. producten")
    ap.add_argument("--out-dir", default=str(ROOT / "docs"), help="Output map (default ./docs)")
    args = ap.parse_args()

    today = dt.date.today()
    start_date = args.since or f"{today.year}-01-01"
    end_date = args.until or f"{today.year+1}-01-01"

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = connect()
    try:
        rows = fetch_new_brands(conn, args.shop_id, start_date, end_date, args.min_products)
    finally:
        conn.close()

    items, total_products = [], 0
    for r in rows:
        first_ts = r["eerste_product_launch"]
        iso = first_ts.isoformat(sep=" ") if hasattr(first_ts, "isoformat") else str(first_ts)
        count = int(r["aantal_producten"] or 0)
        items.append({"merk": r["merk"], "eerste_product_live": iso, "aantal_producten": count})
        total_products += count

    payload = {
        "meta": {
            "shop_id": args.shop_id,
            "start_date": start_date,
            "end_date": end_date,
            "min_products": args.min_products,
            "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "rows": len(items),
            "sum_producten": total_products,
        },
        "items": items,
    }

    write_json(out_dir / "data.json", payload)
    write_csv(out_dir / "data.csv", items)

    # Minimale index als je die nog niet hebt
    index_path = out_dir / "index.html"
    if not index_path.exists():
        index_path.write_text("""<!doctype html>
<html lang='nl'><head><meta charset='utf-8'><title>Nieuwe merken</title></head>
<body><p>Upload voltooid. Voeg docs/index.html toe voor een mooie weergave.</p></body></html>""", encoding="utf-8")

    print(f"OK: {len(items)} merken -> {out_dir}/data.json en data.csv")
    print(f"Periode: {start_date} t/m (excl) {end_date} | Shop {args.shop_id} | min_products={args.min_products}")

if __name__ == "__main__":
    main()