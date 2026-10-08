# Network Attack World Model

This is Stage 1 of the planned system: one CPU-trainable LSTM or GRU backbone with three heads. It predicts the raw next state, infiltration probability, and one of seven ordinal ATT&CK stages. There is intentionally no GNN, attention/Transformer, or multi-step rollout logic.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Place a CIC-IDS-2018 or CTU-13 CSV under `data/`, then edit the constants at the top of [data_pipeline.py](data_pipeline.py), especially `STAGE_MAPPING` and aliases in `FEATURE_ALIASES` when the export uses different names.

## Window selection, then training

Run the experiment first. It reports framed sequence count, stage counts, and mean raw rows per time window, and loudly flags settings below 300 sequences:

```powershell
python window_size_experiment.py --data data/CIC-IDS-2018.csv
python train.py --data data/CIC-IDS-2018.csv --window-seconds 30 --sequence-length 10 --backbone lstm
```

For a dependency and CPU smoke test without a dataset:

```powershell
python window_size_experiment.py --synthetic
python train.py --synthetic --epochs 2 --patience 1
```

The default history length is `k=10`; it is a documented, revisitable configuration choice. Input feature vectors are standardized across aggregated windows before entering the recurrent backbone, while the next-state target remains in raw feature units. Splits use `StratifiedGroupKFold` so windows from the same source/destination group cannot cross train, validation, and test.

## Output contract

`AttackWorldModel.predict(window_sequence)` returns:

```python
{
    "next_state_pred": [...],
    "infiltration_prob": float,
    "stage_probabilities": [...],  # length 7
    "predicted_stage": int,
    "confidence": float,
}
```

The sequence passed to `predict` must have shape `(k, n_features)` and use the saved pipeline scaler. Checkpoints are written to `checkpoints/attack_world_model.pt`.