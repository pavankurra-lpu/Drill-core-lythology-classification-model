"""
ml/evaluation/metrics.py
-------------------------
Evaluation metrics, reporting, and plot generation for the
Lithology Classification System.

Functions
---------
compute_metrics        – accuracy, precision, recall, F1, ROC-AUC, confusion matrix
plot_confusion_matrix  – heatmap image → base64 PNG string
plot_roc_curves        – one-vs-rest ROC curves → base64 PNG string
plot_training_history  – loss & accuracy curves → base64 PNG string
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")   # headless backend — must be set before pyplot import
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.preprocessing import label_binarize

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core metric computation
# ---------------------------------------------------------------------------

def compute_metrics(
    y_true: Union[List[int], np.ndarray],
    y_pred: Union[List[int], np.ndarray],
    y_proba: Optional[np.ndarray] = None,
    class_names: Optional[List[str]] = None,
) -> Dict:
    """
    Compute a comprehensive set of classification metrics.

    Parameters
    ----------
    y_true : array-like of int
        Ground-truth class indices.
    y_pred : array-like of int
        Predicted class indices.
    y_proba : np.ndarray, optional
        Predicted probabilities, shape (N, num_classes).
        Required for ROC-AUC.
    class_names : List[str], optional
        Human-readable class names. If None, uses "Class 0", "Class 1", …

    Returns
    -------
    dict with keys:
        accuracy          float
        precision_macro   float
        recall_macro      float
        f1_macro          float
        precision_weighted float
        recall_weighted   float
        f1_weighted       float
        roc_auc_macro     float  (None if y_proba is None)
        confusion_matrix  np.ndarray (N_classes, N_classes)
        per_class_metrics dict  {class_name: {precision, recall, f1, support}}
        classification_report str
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n_classes = max(y_true.max(), y_pred.max()) + 1 if len(y_true) else 1

    if class_names is None:
        class_names = [f"Class {i}" for i in range(n_classes)]

    # ── Macro / weighted averages ──────────────────────────────────────── #
    acc = accuracy_score(y_true, y_pred)
    prec_macro = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec_macro = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    prec_weighted = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec_weighted = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    # ── Confusion matrix ──────────────────────────────────────────────── #
    cm = confusion_matrix(y_true, y_pred, labels=list(range(n_classes)))

    # ── ROC-AUC ───────────────────────────────────────────────────────── #
    roc_auc = None
    if y_proba is not None and y_proba.ndim == 2:
        try:
            if n_classes == 2:
                roc_auc = roc_auc_score(y_true, y_proba[:, 1])
            else:
                roc_auc = roc_auc_score(
                    y_true, y_proba, multi_class="ovr", average="macro"
                )
        except Exception as exc:
            logger.warning("ROC-AUC computation failed: %s.", exc)

    # ── Per-class metrics ──────────────────────────────────────────────── #
    per_class: Dict[str, Dict[str, float]] = {}
    prec_per = precision_score(y_true, y_pred, average=None, zero_division=0)
    rec_per = recall_score(y_true, y_pred, average=None, zero_division=0)
    f1_per = f1_score(y_true, y_pred, average=None, zero_division=0)
    unique, counts = np.unique(y_true, return_counts=True)
    support_map = dict(zip(unique.tolist(), counts.tolist()))

    for i, name in enumerate(class_names):
        if i < len(prec_per):
            per_class[name] = {
                "precision": float(prec_per[i]),
                "recall": float(rec_per[i]),
                "f1": float(f1_per[i]),
                "support": int(support_map.get(i, 0)),
            }

    # ── Sklearn classification report ─────────────────────────────────── #
    report = classification_report(
        y_true, y_pred,
        target_names=class_names[:n_classes],
        zero_division=0,
    )

    logger.info(
        "Metrics | acc=%.4f | f1_macro=%.4f | roc_auc=%s",
        acc, f1_macro, f"{roc_auc:.4f}" if roc_auc is not None else "N/A",
    )

    return {
        "accuracy": float(acc),
        "precision_macro": float(prec_macro),
        "recall_macro": float(rec_macro),
        "f1_macro": float(f1_macro),
        "precision_weighted": float(prec_weighted),
        "recall_weighted": float(rec_weighted),
        "f1_weighted": float(f1_weighted),
        "roc_auc_macro": float(roc_auc) if roc_auc is not None else None,
        "confusion_matrix": cm,
        "per_class_metrics": per_class,
        "classification_report": report,
    }


# ---------------------------------------------------------------------------
# Confusion matrix plot
# ---------------------------------------------------------------------------

def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: List[str],
    normalize: bool = True,
    figsize: Tuple[int, int] = (14, 12),
    cmap: str = "Blues",
    title: str = "Confusion Matrix",
) -> str:
    """
    Render a confusion matrix as a heatmap and return it as a base64 PNG.

    Parameters
    ----------
    cm : np.ndarray  (N, N)
        Confusion matrix from sklearn.metrics.confusion_matrix.
    class_names : List[str]
    normalize : bool
        If True, normalise each row to show recall per class.
    figsize : (width, height) in inches.
    cmap : matplotlib colourmap name.
    title : Plot title.

    Returns
    -------
    str  base64-encoded PNG image (data:image/png;base64,…).
    """
    if normalize:
        row_sums = cm.sum(axis=1, keepdims=True)
        cm_display = np.where(row_sums == 0, 0, cm / (row_sums + 1e-10))
        fmt = ".2f"
    else:
        cm_display = cm
        fmt = "d"

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(cm_display, interpolation="nearest", cmap=cmap, vmin=0, vmax=1 if normalize else cm.max())

    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set(
        xticks=range(len(class_names)),
        yticks=range(len(class_names)),
        xticklabels=class_names,
        yticklabels=class_names,
        title=title,
        ylabel="True label",
        xlabel="Predicted label",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
    plt.setp(ax.get_yticklabels(), fontsize=9)

    # Text annotations
    thresh = cm_display.max() / 2.0
    for i in range(cm_display.shape[0]):
        for j in range(cm_display.shape[1]):
            val = cm_display[i, j]
            text = f"{val:.2f}" if normalize else f"{int(val)}"
            ax.text(
                j, i, text,
                ha="center", va="center",
                color="white" if val > thresh else "black",
                fontsize=7,
            )

    fig.tight_layout()
    return _fig_to_base64(fig)


# ---------------------------------------------------------------------------
# ROC curves plot
# ---------------------------------------------------------------------------

def plot_roc_curves(
    y_true: Union[List[int], np.ndarray],
    y_proba: np.ndarray,
    class_names: List[str],
    figsize: Tuple[int, int] = (10, 8),
    title: str = "ROC Curves (One-vs-Rest)",
) -> str:
    """
    Plot per-class ROC curves (one-vs-rest) and the macro-average.

    Parameters
    ----------
    y_true : array-like of int
    y_proba : np.ndarray  (N, num_classes)
    class_names : List[str]
    figsize : (width, height) in inches.
    title : Plot title.

    Returns
    -------
    str  base64-encoded PNG.
    """
    y_true = np.asarray(y_true)
    n_classes = len(class_names)
    y_bin = label_binarize(y_true, classes=list(range(n_classes)))

    fig, ax = plt.subplots(figsize=figsize)

    colors = plt.cm.tab20(np.linspace(0, 1, n_classes))  # type: ignore[attr-defined]
    all_fpr: List[np.ndarray] = []
    all_tpr: List[np.ndarray] = []

    for i, (name, color) in enumerate(zip(class_names, colors)):
        if y_proba.shape[1] <= i:
            continue
        try:
            fpr, tpr, _ = roc_curve(y_bin[:, i], y_proba[:, i])
            roc_auc = auc(fpr, tpr)
            ax.plot(fpr, tpr, color=color, lw=1.2, label=f"{name} (AUC={roc_auc:.2f})")
            all_fpr.append(fpr)
            all_tpr.append(tpr)
        except Exception:
            pass

    # Macro-average ROC
    if all_fpr:
        try:
            mean_fpr = np.linspace(0, 1, 200)
            mean_tpr = np.zeros_like(mean_fpr)
            for fpr, tpr in zip(all_fpr, all_tpr):
                mean_tpr += np.interp(mean_fpr, fpr, tpr)
            mean_tpr /= len(all_fpr)
            macro_auc = auc(mean_fpr, mean_tpr)
            ax.plot(
                mean_fpr, mean_tpr,
                color="navy", lw=2.5, linestyle="--",
                label=f"Macro-average (AUC={macro_auc:.2f})",
            )
        except Exception:
            pass

    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Random")
    ax.set(xlim=[0, 1], ylim=[0, 1.02], xlabel="False Positive Rate",
           ylabel="True Positive Rate", title=title)
    ax.legend(loc="lower right", fontsize=7, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _fig_to_base64(fig)


# ---------------------------------------------------------------------------
# Training history plot
# ---------------------------------------------------------------------------

def plot_training_history(
    train_losses: List[float],
    val_losses: List[float],
    train_accs: List[float],
    val_accs: List[float],
    lr_history: Optional[List[float]] = None,
    figsize: Tuple[int, int] = (14, 5),
    title: str = "Training History",
) -> str:
    """
    Plot training / validation loss and accuracy curves.

    Parameters
    ----------
    train_losses, val_losses : per-epoch loss values.
    train_accs, val_accs : per-epoch accuracy values (0–1 scale).
    lr_history : per-epoch learning rates (optional; adds a third subplot).
    figsize : (width, height) in inches.
    title : Figure super-title.

    Returns
    -------
    str  base64-encoded PNG.
    """
    n_plots = 3 if lr_history else 2
    fig, axes = plt.subplots(1, n_plots, figsize=figsize)
    epochs = list(range(1, len(train_losses) + 1))

    # ── Loss ──────────────────────────────────────────────────────────── #
    ax = axes[0]
    ax.plot(epochs, train_losses, "b-o", markersize=3, label="Train Loss")
    ax.plot(epochs, val_losses, "r-o", markersize=3, label="Val Loss")
    ax.set(title="Loss", xlabel="Epoch", ylabel="Cross-Entropy Loss")
    ax.legend()
    ax.grid(alpha=0.3)

    # Annotate best val loss
    if val_losses:
        best_epoch = int(np.argmin(val_losses)) + 1
        best_val = min(val_losses)
        ax.annotate(
            f"Best: {best_val:.4f}",
            xy=(best_epoch, best_val),
            xytext=(best_epoch + 1, best_val + (max(val_losses) - min(val_losses)) * 0.1),
            arrowprops=dict(arrowstyle="->", color="red"),
            color="red", fontsize=8,
        )

    # ── Accuracy ──────────────────────────────────────────────────────── #
    ax = axes[1]
    ax.plot(epochs, [a * 100 for a in train_accs], "b-o", markersize=3, label="Train Acc")
    ax.plot(epochs, [a * 100 for a in val_accs], "r-o", markersize=3, label="Val Acc")
    ax.set(title="Accuracy", xlabel="Epoch", ylabel="Accuracy (%)", ylim=[0, 100])
    ax.legend()
    ax.grid(alpha=0.3)

    if val_accs:
        best_epoch = int(np.argmax(val_accs)) + 1
        best_acc = max(val_accs) * 100
        ax.annotate(
            f"Best: {best_acc:.1f}%",
            xy=(best_epoch, best_acc),
            xytext=(best_epoch + 1, best_acc - 5),
            arrowprops=dict(arrowstyle="->", color="red"),
            color="red", fontsize=8,
        )

    # ── Learning rate ─────────────────────────────────────────────────── #
    if lr_history and n_plots == 3:
        ax = axes[2]
        ax.plot(epochs[:len(lr_history)], lr_history, "g-o", markersize=3)
        ax.set(title="Learning Rate", xlabel="Epoch", ylabel="LR")
        ax.set_yscale("log")
        ax.grid(alpha=0.3)

    fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.tight_layout()
    return _fig_to_base64(fig)


# ---------------------------------------------------------------------------
# Per-class bar chart
# ---------------------------------------------------------------------------

def plot_per_class_metrics(
    per_class_metrics: Dict[str, Dict[str, float]],
    figsize: Tuple[int, int] = (14, 6),
    title: str = "Per-Class Precision / Recall / F1",
) -> str:
    """
    Bar chart of per-class precision, recall, and F1 scores.

    Parameters
    ----------
    per_class_metrics : dict from compute_metrics().
    figsize, title.

    Returns
    -------
    str  base64-encoded PNG.
    """
    class_names = list(per_class_metrics.keys())
    precisions = [per_class_metrics[c]["precision"] for c in class_names]
    recalls = [per_class_metrics[c]["recall"] for c in class_names]
    f1s = [per_class_metrics[c]["f1"] for c in class_names]

    x = np.arange(len(class_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(x - width, precisions, width, label="Precision", color="#2196F3", alpha=0.85)
    ax.bar(x, recalls, width, label="Recall", color="#4CAF50", alpha=0.85)
    ax.bar(x + width, f1s, width, label="F1", color="#FF9800", alpha=0.85)

    ax.set(
        title=title, xlabel="Class", ylabel="Score",
        xticks=x, xticklabels=class_names, ylim=[0, 1.05],
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return _fig_to_base64(fig)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fig_to_base64(fig: plt.Figure) -> str:
    """Render a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"
