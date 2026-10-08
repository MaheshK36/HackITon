"""Evaluation metrics and benchmark comparison for the world model."""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
from torch.utils.data import DataLoader, TensorDataset

from data_pipeline import WindowedData


def stage_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> pd.DataFrame:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=np.arange(7), zero_division=0)
    return pd.DataFrame({"stage": np.arange(7), "precision": precision, "recall": recall,
                         "f1": f1, "support": support})


def binary_fpr(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp = matrix[0]
    return float(fp / max(tn + fp, 1))


@torch.no_grad()
def evaluate_model(model: torch.nn.Module, data: WindowedData, batch_size: int = 256) -> dict:
    model.eval()
    loader = DataLoader(TensorDataset(torch.from_numpy(data.sequences)), batch_size=batch_size)
    stages, infiltration = [], []
    for (sequence,) in loader:
        output = model(sequence)
        stages.extend(output["stage_logits"].argmax(dim=1).cpu().numpy())
        infiltration.extend((torch.sigmoid(output["infiltration_logit"]) >= 0.5).cpu().numpy())
    y_stage, y_infiltration = data.stages, data.infiltration.astype(int)
    weighted = precision_recall_fscore_support(y_stage, stages, average="weighted", zero_division=0)
    return {"per_stage": stage_metrics(y_stage, np.asarray(stages)),
            "macro_f1": float(precision_recall_fscore_support(y_stage, stages, average="macro", zero_division=0)[2]),
            "precision": float(weighted[0]), "recall": float(weighted[1]),
            "fpr": binary_fpr(y_infiltration, np.asarray(infiltration))}


def train_logistic_baseline(train: WindowedData, test: WindowedData, seed: int = 42) -> dict:
    classifier = LogisticRegression(max_iter=300, class_weight="balanced", random_state=seed)
    classifier.fit(train.sequences[:, -1, :], train.stages)
    predictions = classifier.predict(test.sequences[:, -1, :])
    precision, recall, f1, _ = precision_recall_fscore_support(test.stages, predictions, average="weighted", zero_division=0)
    return {"model": "logistic_regression", "f1": float(f1), "precision": float(precision),
            "recall": float(recall), "fpr": binary_fpr(test.infiltration.astype(int), (predictions > 0).astype(int))}


def print_benchmark_table(world_model_metrics: dict, baseline_metrics: dict) -> None:
    rows = [{"model": "LSTM/GRU world model", "f1": world_model_metrics["macro_f1"],
             "precision": world_model_metrics["precision"], "recall": world_model_metrics["recall"], "fpr": world_model_metrics["fpr"]}, baseline_metrics]
    print("\nBenchmark (test split)\n" + pd.DataFrame(rows).to_string(index=False, float_format=lambda value: f"{value:.4f}"))