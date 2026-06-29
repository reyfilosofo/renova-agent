# Renova Index

The Renova Global Index, abbreviated IRG, is a transparent 0-100 diagnostic model for evaluating the renewal capacity of a life-system.

It is designed for cultural, educational, territorial, organizational, and community contexts. It is not a medical, legal, financial, or psychometric instrument.

## Default formula

```text
IRG = 0.35H + 0.25R + 0.20O + 0.10S + 0.10E
```

Where:

- H = habitat.
- R = repair.
- O = horizon.
- S = sensitivity.
- E = equilibrium.

## Dimensions

### Habitat

The material, symbolic, relational, and informational conditions that allow a system to continue.

### Repair

The capacity to name tensions, process memory, and create practices of restoration without reducing renewal to nostalgia.

### Horizon

The credible future that gives orientation to collective action.

### Sensitivity

The quality of attention, listening, perception, aesthetic care, and respect for value.

### Equilibrium

The rhythm, boundaries, continuity, and sustainability of action.

## Interpretation

- 85-100: excellent renewal.
- 70-84.99: active renewal.
- 55-69.99: vulnerable renewal.
- 40-54.99: critical renewal.
- 0-39.99: blocked renewal.

## Usage

```bash
python -m renova_core.cli index data/sample_assessment.json
```
