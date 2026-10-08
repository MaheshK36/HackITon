"""Train the CPU-friendly single-branch attack world model."""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset

from data_pipeline import DEFAULT_DATA_PATHS, SEQUENCE_LENGTH, load_csv, load_frame, make_windows, split_by_group
from evaluate import evaluate_model, print_benchmark_table, train_logistic_baseline
from models import AttackWorldModel, ModelConfig

EPOCHS = 30
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
PATIENCE = 5
CHECKPOINT_PATH = "checkpoints/attack_world_model.pt"
WINDOW_SECONDS = 30.0
BACKBONE = "lstm"
LOSS_WEIGHTS = {"mse": 1.0, "bce": 1.0, "cross_entropy": 1.0}


def synthetic_frame(groups: int = 21, rows_per_group: int = 50, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    labels = ["BENIGN", "RECONNAISSANCE", "INITIAL ACCESS", "LATERAL MOVEMENT", "C2", "EXFILTRATION", "IMPACT"]
    records = []
    for group in range(groups):
        stage = group % 7
        for row in range(rows_per_group):
            record = {name: float(rng.normal(stage * 2, 1)) for name in [
                "src_port", "dst_port", "protocol", "tcp_flags", "bytes_per_flow", "packets_per_flow",
                "flow_duration", "iat_mean", "iat_variance", "iat_max", "bidirectional_flow_ratio", "ttl",
                "ttl_variance", "tcp_window_size", "ip_fragment_flags", "payload_size", "port_scan_signature", "retransmission_count"]}
            record.update({"src_ip": f"10.0.{group}.1", "dst_ip": "10.0.0.2", "label": labels[stage], "timestamp": pd.Timestamp("2024-01-01") + pd.Timedelta(seconds=row * 10)})
            records.append(record)
    return pd.DataFrame(records)


def _class_weights(stages: np.ndarray) -> torch.Tensor:
    counts = np.bincount(stages, minlength=7).astype(np.float32)
    weights = np.zeros_like(counts)
    np.divide(len(stages), 7 * counts, out=weights, where=counts > 0)
    return torch.from_numpy(weights)


def train(args: argparse.Namespace) -> tuple[AttackWorldModel, dict]:
    frame = load_frame(synthetic_frame()) if args.synthetic else load_csv(args.data)
    windowed = make_windows(frame, args.window_seconds, args.sequence_length)
    splits = split_by_group(windowed, args.seed)
    model = AttackWorldModel(ModelConfig(input_size=len(windowed.feature_names), backbone=args.backbone,
                                         w_mse=1.0, w_bce=1.0, w_ce=1.0))
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    class_weights = _class_weights(splits["train"].stages)
    train_loader = DataLoader(TensorDataset(torch.from_numpy(splits["train"].sequences), torch.from_numpy(splits["train"].next_states), torch.from_numpy(splits["train"].infiltration), torch.from_numpy(splits["train"].stages)), batch_size=args.batch_size, shuffle=True)
    best = float("inf"); stale = 0
    for epoch in range(1, args.epochs + 1):
        model.train(); totals = {"mse": 0.0, "bce": 0.0, "cross_entropy": 0.0, "total": 0.0}
        for sequence, next_state, infiltration, stage in train_loader:
            optimizer.zero_grad(); losses = model.compute_loss(model(sequence), next_state, infiltration, stage, class_weights)
            losses["total"].backward(); optimizer.step()
            for key in totals: totals[key] += float(losses[key].detach())
        totals = {key: value / max(len(train_loader), 1) for key, value in totals.items()}
        validation = evaluate_model(model, splits["val"])
        print(f"epoch={epoch:03d} " + " ".join(f"{key}={value:.4f}" for key, value in totals.items()) + f" val_macro_f1={validation['macro_f1']:.4f}")
        if totals["total"] < best:
            best, stale = totals["total"], 0; Path(args.checkpoint).parent.mkdir(parents=True, exist_ok=True)
            torch.save({"model_state": model.state_dict(), "config": model.config.__dict__, "scaler": windowed.scaler}, args.checkpoint)
        else:
            stale += 1
            if stale >= args.patience: break
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model_state"])
    test_metrics = evaluate_model(model, splits["test"])
    print("\nPer-stage test metrics\n" + test_metrics["per_stage"].to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print_benchmark_table(test_metrics, train_logistic_baseline(splits["train"], splits["test"], args.seed))
    return model, test_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=next((path for path in DEFAULT_DATA_PATHS if Path(path).exists()), DEFAULT_DATA_PATHS[0]))
    parser.add_argument("--synthetic", action="store_true", help="Run a deterministic CPU smoke dataset.")
    parser.add_argument("--window-seconds", type=float, default=WINDOW_SECONDS)
    parser.add_argument("--sequence-length", type=int, default=SEQUENCE_LENGTH)
    parser.add_argument("--backbone", choices=["lstm", "gru"], default=BACKBONE)
    parser.add_argument("--epochs", type=int, default=EPOCHS); parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--learning-rate", type=float, default=LEARNING_RATE); parser.add_argument("--patience", type=int, default=PATIENCE)
    parser.add_argument("--checkpoint", default=CHECKPOINT_PATH); parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    torch.manual_seed(42); np.random.seed(42); train(parse_args())