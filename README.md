# card-data

The open credit card dataset. Every card's earn rates, fees, credits, signup
bonuses, and transfer partners — in human-editable YAML, with validated JSON
builds for apps to consume.

**Data is king.** Card comparison tools live or die on data freshness. This repo
exists so the data is open, versioned, and community-maintained instead of
locked inside paid apps.

## Layout

```
cards/<issuer>/<card>.yaml   human-editable source of truth (one file per card)
valuations.yaml              cents-per-point valuations per rewards program
transfer-partners.yaml       points -> airline/hotel transfer graph
dist/card-catalog.json       built artifact — what apps fetch
dist/transfer-partners.json  built artifact
schemas/                     JSON Schemas the dist files validate against
tools/                       importer, builder, validator
```

Edit the YAML. Never edit `dist/` by hand — it's built by `tools/build.py`
(and by CI on every merge).

## Consuming the data

Fetch the built JSON (no auth, no key):

- `https://raw.githubusercontent.com/lalit10/card-data/main/dist/card-catalog.json`
- `https://raw.githubusercontent.com/lalit10/card-data/main/dist/transfer-partners.json`

Both validate against `schemas/`. Point valuations in the catalog are
cents-per-point (floor + optimistic); effective earn % = points-per-dollar ×
average cpp.

## Contributing

Found a stale rate, a new credit, a devaluation? PRs welcome:

1. Edit the card's YAML in `cards/<issuer>/` (or `transfer-partners.yaml`).
2. Set `verified_date` to today and bump `confidence` if you checked the issuer.
3. CI validates your YAML against the schema and flags stale entries.

Keep entries factual and cite the issuer page in a `sources:` note where
practical. No affiliate links, no marketing copy.

## Sources

- Transfer partners from [card-links-mcp](https://mcp.milesandpointsdaily.com)
  (free endpoint) plus hand-compiled additions, each row marked with provenance.
- Transfer ratios are issuer-published facts. Always confirm with the issuer
  before transferring — transfers are irreversible.

## License

MIT. Data is facts; the curation is shared.
