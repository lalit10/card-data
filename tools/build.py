#!/usr/bin/env python3
"""Build dist/ from the YAML sources. Also validates.

Usage:
    python3 tools/build.py            # validate + write dist/
    python3 tools/build.py --check     # validate only (CI)

Reads:
    cards/<issuer>/<card>.yaml
    valuations.yaml
    transfer-partners.yaml
    schemas/catalog.schema.json
Writes:
    dist/card-catalog.json
    dist/transfer-partners.json
"""
import argparse
import glob
import json
import os
import sys
import time

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_yaml(path):
    with open(path) as f:
        # strip leading # comments are handled by yaml itself
        return yaml.safe_load(f)


def parse_ratio(ratio):
    try:
        a, b = str(ratio).split(":")
        return float(b) / float(a)
    except Exception:  # noqa: BLE001
        return None


def build_catalog():
    valuations = load_yaml(os.path.join(ROOT, "valuations.yaml"))["programs"]
    cards = []
    for path in sorted(glob.glob(os.path.join(ROOT, "cards", "*", "*.yaml"))):
        doc = load_yaml(path)
        issuer = os.path.basename(os.path.dirname(path))
        card_id = doc.get("id") or os.path.splitext(os.path.basename(path))[0]
        if doc.get("issuer", issuer) != issuer:
            raise ValueError(f"{path}: issuer field {doc.get('issuer')!r} != directory {issuer!r}")
        cards.append({
            "id": f"{issuer}-{card_id}",
            "name": doc.get("name"),
            "issuer": issuer,
            "network": doc.get("network"),
            "availability": doc.get("availability") or "active",
            "annual_fee_usd": doc.get("annual_fee_usd", 0),
            "foreign_transaction_pct": doc.get("foreign_transaction_pct"),
            "currency_type": doc.get("currency_type"),
            "currency_program": doc.get("currency_program"),
            "cpp_floor": (valuations.get(doc.get("currency_program") or "", {}) or {}).get("floor_cpp"),
            "cpp_optimistic": (valuations.get(doc.get("currency_program") or "", {}) or {}).get("optimistic_cpp"),
            "base_rate": doc.get("base_rate"),
            "earn": doc.get("earn") or [],
            "credits": doc.get("credits") or [],
            "signup_bonus": doc.get("signup_bonus"),
            "benefits": doc.get("benefits") or [],
            "verified_date": doc.get("verified_date"),
            "confidence": doc.get("confidence"),
        })
    catalog = {
        "source": "github.com/lalit10/card-data",
        "source_license": "see LICENSE; card facts compiled from public issuer sources",
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "card_count": len(cards),
        "valuations": {k: {"floor_cpp": v.get("floor_cpp"), "optimistic_cpp": v.get("optimistic_cpp")}
                       for k, v in valuations.items()},
        "cards": sorted(cards, key=lambda c: c["name"] or c["id"]),
    }
    schema = json.load(open(os.path.join(ROOT, "schemas", "catalog.schema.json")))
    try:
        validate(catalog, schema)
    except Exception as e:  # noqa: BLE001 — short error, not the 200KB instance dump
        msg = getattr(e, "message", str(e))[:300]
        path = ".".join(str(p) for p in getattr(e, "absolute_path", []))
        print(f"SCHEMA FAIL at {path or '<root>'}: {msg}", file=sys.stderr)
        sys.exit(1)
    return catalog


def build_transfers():
    doc = load_yaml(os.path.join(ROOT, "transfer-partners.yaml"))
    programs = []
    for p in doc.get("programs", []):
        partners = []
        for t in p.get("partners", []):
            partners.append({
                "name": t.get("name"),
                "program": t.get("program"),
                "currency": t.get("currency"),
                "type": t.get("type"),
                "ratio": t.get("ratio"),
                "ratio_value": parse_ratio(t.get("ratio") or ""),
                "notes": t.get("notes"),
                "provenance": t.get("provenance") or "card-data",
            })
        programs.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "coverage": p.get("coverage", "full"),
            "coverage_note": p.get("coverage_note"),
            "partners": sorted(partners, key=lambda x: x["name"] or ""),
        })
    return {
        "source": "github.com/lalit10/card-data",
        "source_license": "see LICENSE; card facts compiled from public issuer sources",
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "program_count": len(programs),
        "pair_count": sum(len(p["partners"]) for p in programs),
        "programs": sorted(programs, key=lambda p: p["name"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate only, don't write dist/")
    args = ap.parse_args()

    global validate
    try:
        from jsonschema import validate
    except ImportError:
        print("needs jsonschema: pip install jsonschema", file=sys.stderr)
        sys.exit(2)

    catalog = build_catalog()
    transfers = build_transfers()
    print(f"catalog: {catalog['card_count']} cards OK", file=sys.stderr)
    print(f"transfers: {transfers['program_count']} programs, {transfers['pair_count']} pairs OK", file=sys.stderr)

    if not args.check:
        os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
        for name, data in (("card-catalog.json", catalog), ("transfer-partners.json", transfers)):
            with open(os.path.join(ROOT, "dist", name), "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
        print("wrote dist/", file=sys.stderr)


if __name__ == "__main__":
    main()
