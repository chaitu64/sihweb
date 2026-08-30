import base64
import io
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize


MODEL_VARIANT = "SEN2SRLite"
MODEL_INTERNAL_LR = 128
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SR_OPTS = {"tta_passes": 8, "radiometric": True, "ibp_iters": 3, "ibp_step": 1.0}
REFLECTANCE_MIN = -0.05
REFLECTANCE_MAX = 1.60


def _load_model() -> tuple[Any | None, str | None]:
    model_path = Path(__file__).resolve().parents[1] / "model" / "SEN2SRLite_RGBN"
    try:
        import mlstac

        model = mlstac.load(str(model_path)).compiled_model(device=DEVICE)
        model.eval()
        return model, None
    except Exception as exc:
        return None, f"SEN2SRLite unavailable: {exc}"


MODEL, MODEL_STATUS = _load_model()
MC_DROPOUT_AVAILABLE = bool(
    MODEL and any(isinstance(layer, torch.nn.Dropout) for layer in MODEL.modules())
)


def _png_data_url(array: np.ndarray) -> str:
    image = Image.fromarray((np.clip(array, 0.0, 1.0) * 255).astype(np.uint8), "RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _gray_png_data_url(array: np.ndarray, cmap: str, vmin: float | None = None, vmax: float | None = None) -> str:
    clean = np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)
    finite = clean[np.isfinite(clean)]
    if vmin is None and finite.size:
        vmin = float(np.percentile(finite, 1))
    if vmax is None and finite.size:
        vmax = float(np.percentile(finite, 99))
    vmin = 0.0 if vmin is None else vmin
    vmax = 1.0 if vmax is None else vmax
    if finite.size and vmax <= vmin:
        vmin = float(np.min(finite))
        vmax = float(np.max(finite))
    if vmax <= vmin:
        vmax = vmin + 1e-8
    figure, axis = plt.subplots(figsize=(5, 5), dpi=110)
    image = axis.imshow(clean, cmap=cmap, norm=Normalize(vmin=vmin, vmax=vmax))
    axis.axis("off")
    figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    figure.tight_layout(pad=0)
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(figure)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _stretch(rgb: np.ndarray) -> np.ndarray:
    finite = rgb[np.isfinite(rgb)]
    if finite.size == 0:
        return np.zeros_like(rgb, dtype=np.float32)
    low, high = np.percentile(finite, (2, 98))
    return np.clip((rgb - low) / (high - low + 1e-8), 0.0, 1.0).astype(np.float32)


def _dihedral(value: torch.Tensor, index: int) -> torch.Tensor:
    rotated = torch.rot90(value, index % 4, dims=(-2, -1))
    return torch.flip(rotated, dims=(-1,)) if index >= 4 else rotated


def _inverse_dihedral(value: torch.Tensor, index: int) -> torch.Tensor:
    unflipped = torch.flip(value, dims=(-1,)) if index >= 4 else value
    return torch.rot90(unflipped, -(index % 4), dims=(-2, -1))


def _radiometric_align(sr: torch.Tensor, lr: torch.Tensor) -> torch.Tensor:
    lr_hat = F.interpolate(sr, size=lr.shape[-2:], mode="area")
    aligned = sr.clone()
    for band in range(sr.shape[1]):
        sr_mean = lr_hat[:, band].mean()
        sr_std = lr_hat[:, band].std() + 1e-8
        lr_mean = lr[:, band].mean()
        lr_std = lr[:, band].std() + 1e-8
        gain = (lr_std / sr_std).clamp(0.5, 2.0)
        aligned[:, band] = (sr[:, band] - sr_mean) * gain + lr_mean
    return aligned


def _back_project(sr: torch.Tensor, lr: torch.Tensor) -> torch.Tensor:
    for _ in range(SR_OPTS["ibp_iters"]):
        residual = lr - F.interpolate(sr, size=lr.shape[-2:], mode="area")
        sr = sr + SR_OPTS["ibp_step"] * F.interpolate(
            residual, size=sr.shape[-2:], mode="bicubic", align_corners=False
        )
    return sr.clamp(REFLECTANCE_MIN, REFLECTANCE_MAX)


@torch.no_grad()
def _run_chunk(chunk: torch.Tensor, stochastic: bool = False) -> tuple[torch.Tensor, torch.Tensor | None]:
    if MODEL is None:
        return F.interpolate(chunk, scale_factor=4, mode="bicubic", align_corners=False), None
    MODEL.train(mode=stochastic)
    outputs = [_inverse_dihedral(MODEL(_dihedral(chunk, index)), index) for index in range(SR_OPTS["tta_passes"])]
    stack = torch.stack(outputs)
    sr = stack.mean(dim=0)
    spread = stack.std(dim=0) if stochastic else None
    if SR_OPTS["radiometric"]:
        sr = _radiometric_align(sr, chunk)
    if SR_OPTS["ibp_iters"]:
        sr = _back_project(sr, chunk)
    MODEL.eval()
    return sr, spread


@torch.no_grad()
def run_sr(lr_input: torch.Tensor, return_spread: bool = False, stochastic: bool = False) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
    lr = lr_input.unsqueeze(0) if lr_input.ndim == 3 else lr_input
    height, width = lr.shape[-2:]
    pad_height = (-height) % MODEL_INTERNAL_LR
    pad_width = (-width) % MODEL_INTERNAL_LR
    padded = F.pad(lr, (0, pad_width, 0, pad_height), mode="replicate")
    padded_height, padded_width = padded.shape[-2:]
    sr_full = torch.zeros(lr.shape[1], padded_height * 4, padded_width * 4, device=lr.device)
    spread_full = torch.zeros_like(sr_full) if return_spread else None
    for top in range(0, padded_height, MODEL_INTERNAL_LR):
        for left in range(0, padded_width, MODEL_INTERNAL_LR):
            chunk = padded[..., top:top + MODEL_INTERNAL_LR, left:left + MODEL_INTERNAL_LR]
            sr_chunk, spread_chunk = _run_chunk(chunk, stochastic=stochastic)
            target = (..., slice(top * 4, (top + MODEL_INTERNAL_LR) * 4), slice(left * 4, (left + MODEL_INTERNAL_LR) * 4))
            sr_full[target] = sr_chunk.squeeze(0)
            if spread_full is not None and spread_chunk is not None:
                spread_full[target] = spread_chunk.squeeze(0)
    sr_full = sr_full[:, :height * 4, :width * 4]
    return (sr_full, spread_full[:, :height * 4, :width * 4]) if spread_full is not None else sr_full


def _decode_reference(image_bytes: bytes) -> torch.Tensor:
    image = Image.open(io.BytesIO(image_bytes))
    image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
    image = image.resize((512, 512), Image.Resampling.BILINEAR)
    values = np.asarray(image).astype(np.float32) / 255.0
    return torch.from_numpy(np.nan_to_num(values).transpose(2, 0, 1)).to(DEVICE)


def _metric_values(estimate: torch.Tensor, reference: torch.Tensor) -> tuple[dict[str, Any], np.ndarray]:
    estimate_np = np.clip(estimate.detach().cpu().numpy(), 0.0, 1.0)
    reference_np = np.clip(reference.detach().cpu().numpy(), 0.0, 1.0)
    channels = min(estimate_np.shape[0], reference_np.shape[0])
    difference = estimate_np[:channels] - reference_np[:channels]
    error_map = np.sqrt(np.mean(difference ** 2, axis=0)).astype(np.float32)
    estimate_rgb = estimate_np[:3].transpose(1, 2, 0)
    reference_rgb = reference_np[:3].transpose(1, 2, 0)
    metrics: dict[str, Any] = {
        "psnr": float(peak_signal_noise_ratio(reference_rgb, estimate_rgb, data_range=1.0)),
        "ssim": float(structural_similarity(reference_rgb, estimate_rgb, channel_axis=2, data_range=1.0)),
        "rmse": float(np.sqrt(np.mean(difference ** 2))),
        "mae": float(np.mean(np.abs(difference))),
    }
    vectors_a = estimate_np.transpose(1, 2, 0)
    vectors_b = reference_np.transpose(1, 2, 0)
    cosine = np.sum(vectors_a * vectors_b, axis=2) / (np.linalg.norm(vectors_a, axis=2) * np.linalg.norm(vectors_b, axis=2) + 1e-8)
    metrics["sam"] = float(np.mean(np.arccos(np.clip(cosine, -1.0, 1.0))))
    metrics["per_band_rmse"] = [float(np.sqrt(np.mean(channel ** 2))) for channel in difference]
    metrics["per_band_mae"] = [float(np.mean(np.abs(channel))) for channel in difference]
    return metrics, error_map


def _index(numerator: np.ndarray, denominator_band: np.ndarray) -> np.ndarray:
    denominator = numerator + denominator_band
    result = np.full_like(numerator, np.nan, dtype=np.float32)
    valid = np.abs(denominator) > 1e-6
    result[valid] = (numerator[valid] - denominator_band[valid]) / denominator[valid]
    return np.clip(result, -1.0, 1.0)


def _dashboard_data_url(lr: np.ndarray, sr: np.ndarray, reference: np.ndarray, ndvi: np.ndarray, metrics: dict[str, Any]) -> str:
    figure, axes = plt.subplots(1, 4, figsize=(20, 5))
    axes[0].imshow(lr); axes[0].set_title("LR Input"); axes[0].axis("off")
    axes[1].imshow(sr); axes[1].set_title("SEN2SR ~2.5m-equivalent"); axes[1].axis("off")
    axes[2].imshow(reference); axes[2].set_title("Reference"); axes[2].axis("off")
    axes[3].imshow(ndvi, cmap="YlGn", vmin=-1, vmax=1); axes[3].set_title("NDVI"); axes[3].axis("off")
    figure.suptitle(f"PSNR {metrics['psnr']:.2f} | SSIM {metrics['ssim']:.4f} | RMSE {metrics['rmse']:.4f}")
    figure.tight_layout()
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(figure)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def process_before_snapshot(before_bytes: bytes) -> dict[str, Any]:
    """Run the configured before/after NDWI change workflow."""
    before = _decode_reference(before_bytes)
    if before.shape[0] < 4:
        before = torch.cat((before, before[:1]), dim=0)

    def enhanced_ndwi(image: torch.Tensor) -> tuple[np.ndarray, np.ndarray]:
        lr = F.interpolate(image.unsqueeze(0), size=(MODEL_INTERNAL_LR, MODEL_INTERNAL_LR), mode="area").squeeze(0)
        sr = run_sr(lr).detach().cpu().numpy()
        ndwi = _index(sr[1], sr[3])
        return sr, ndwi

    before_sr, before_ndwi = enhanced_ndwi(before)
    return {
        "outputs": {
            "flood_before": _png_data_url(_stretch(before_sr[:3].transpose(1, 2, 0))),
            "flood_ndwi_before": _gray_png_data_url(before_ndwi, "Blues", -1.0, 1.0),
        },
        "before_ndwi": before_ndwi,
    }


def process_image(image_bytes: bytes, before_bytes: bytes | None = None) -> dict[str, Any]:
    reference = _decode_reference(image_bytes)
    if reference.shape[0] < 4:
        reference = torch.cat((reference, reference[:1]), dim=0)
    lr_input = F.interpolate(reference.unsqueeze(0), size=(MODEL_INTERNAL_LR, MODEL_INTERNAL_LR), mode="area").squeeze(0)
    sr_output = run_sr(lr_input)
    bicubic = F.interpolate(lr_input.unsqueeze(0), size=(512, 512), mode="bicubic", align_corners=False).squeeze(0)
    metrics, error_map = _metric_values(sr_output, reference)
    bicubic_metrics, _ = _metric_values(bicubic, reference)
    sr_np = sr_output.detach().cpu().numpy()
    bicubic_np = bicubic.detach().cpu().numpy()
    reference_np = reference.detach().cpu().numpy()
    
    # Enhancement difference |SR - Bicubic|
    enhancement_diff = np.mean(np.abs(sr_np[:3] - bicubic_np[:3]), axis=0).astype(np.float32)
    ed_finite = enhancement_diff[np.isfinite(enhancement_diff)]
    if ed_finite.size > 0:
        ed_min, ed_max = float(np.min(ed_finite)), float(np.max(ed_finite))
        confidence_proxy = 1.0 - ((enhancement_diff - ed_min) / (ed_max - ed_min + 1e-8))
    else:
        confidence_proxy = np.full_like(enhancement_diff, np.nan)

    red, green, blue, nir = sr_np[:4]
    ndvi = _index(nir, red)
    ndwi = _index(green, nir)
    evi_denominator = nir + 6 * red - 7.5 * blue + 1
    evi = np.where(np.abs(evi_denominator) > 1e-6, 2.5 * (nir - red) / evi_denominator, np.nan).astype(np.float32)
    evi = np.clip(evi, -1.0, 1.0)
    valid_ndvi = np.isfinite(ndvi)
    vegetation_mask = valid_ndvi & (ndvi > 0.30)
    stress_mask = valid_ndvi & (ndvi > 0.1) & (ndvi <= 0.30)
    water_mask = np.isfinite(ndwi) & (ndwi > 0.0)
    valid_count = max(int(valid_ndvi.sum()), 1)
    analytics = {
        "ndvi_mean": float(np.nanmean(ndvi)) if valid_ndvi.any() else None,
        "vegetation_percentage": float(100 * vegetation_mask.sum() / valid_count),
        "stress_percentage": float(100 * stress_mask.sum() / valid_count),
        "stress_interpretation": "Heuristic: 0.1 < NDVI <= 0.30; relative indicator, not an absolute biomass boundary.",
        "ndwi_mean": float(np.nanmean(ndwi)) if np.isfinite(ndwi).any() else None,
        "water_percentage": float(100 * water_mask.sum() / valid_count),
        "evi_mean": float(np.nanmean(evi)) if np.isfinite(evi).any() else None,
    }
    lr_display = _stretch(lr_input[:3].detach().cpu().numpy().transpose(1, 2, 0))
    sr_display = _stretch(sr_np[:3].transpose(1, 2, 0))
    reference_display = _stretch(reference_np[:3].transpose(1, 2, 0))
    outputs = {
        "lr_input": _png_data_url(lr_display),
        "sr_output": _png_data_url(sr_display),
        "hr_reference": _png_data_url(reference_display),
        "ndvi": _gray_png_data_url(ndvi, "YlGn", -1.0, 1.0),
        "validation_dashboard": _dashboard_data_url(lr_display, sr_display, reference_display, ndvi, metrics),
        "error_map": _gray_png_data_url(error_map, "inferno"),
        "enhancement_diff": _gray_png_data_url(enhancement_diff, "magma"),
        "confidence_proxy": _gray_png_data_url(confidence_proxy, "cividis", 0.0, 1.0),
        "ndwi": _gray_png_data_url(ndwi, "Blues", -1.0, 1.0),
        "evi": _gray_png_data_url(evi, "YlGn", -1.0, 1.0),
        "vegetation_mask": _gray_png_data_url(vegetation_mask.astype(np.float32), "YlGn", 0.0, 1.0),
        "water_mask": _gray_png_data_url(water_mask.astype(np.float32), "Blues", 0.0, 1.0),
    }

    if before_bytes:
        try:
            before_res = process_before_snapshot(before_bytes)
            outputs.update(before_res["outputs"])
            before_ndwi = before_res.get("before_ndwi")
            if before_ndwi is not None:
                diff_ndwi = np.clip(ndwi - before_ndwi, -1.0, 1.0)
                flood_candidate = np.where(np.isfinite(diff_ndwi), diff_ndwi > 0.20, False)
                outputs["flood_diff_map"] = _gray_png_data_url(diff_ndwi, "RdBu", -1.0, 1.0)
                outputs["flood_mask"] = _gray_png_data_url(flood_candidate.astype(np.float32), "Blues", 0.0, 1.0)
                valid_diff = np.isfinite(diff_ndwi)
                v_cnt = max(int(valid_diff.sum()), 1)
                analytics["flood_changed_percentage"] = float(100.0 * flood_candidate.sum() / v_cnt)
                analytics["flood_changed_area_km2"] = float(flood_candidate.sum() * ((2.5 / 1000.0) ** 2))
        except Exception:
            pass

    return {
        "outputs": outputs,
        "metrics": {**metrics, "bicubic": bicubic_metrics},
        "panel_mapping": {
            "lr_input": "lr_input",
            "sr_output": "sr_output",
            "hr_reference": "hr_reference",
            "ndvi": "ndvi",
            "validation_dashboard": "validation_dashboard",
            "error": "error_map",
            "enhancement_diff": "enhancement_diff",
            "confidence_proxy": "confidence_proxy",
            "ndwi": "ndwi",
            "evi": "evi",
            "before": "flood_before",
            "before_ndwi": "flood_ndwi_before",
        },
        "analytics": analytics,
        "error_analysis": {
            "mean_error": float(np.mean(error_map)),
            "maximum_error": float(np.max(error_map)),
            "reconstruction_consistency_error": float(torch.mean(torch.abs(F.interpolate(sr_output.unsqueeze(0), size=lr_input.shape[-2:], mode="area") - lr_input)).item()),
        },
        "interpretation": {
            "sr_output": "SEN2SR produces a model-reconstructed ~2.5m-equivalent representation, not an observed 2.5m sensor image.",
            "ndvi": "NDVI indicates relative vegetation density; higher values reflect denser canopy.",
            "ndwi": "NDWI (McFeeters) highlights open water and surface moisture.",
            "error_map": "Error Map displays pixel-wise RMSE between SR reconstruction and native 10m reference.",
            "enhancement_diff": "SR Enhancement Difference (|SR - Bicubic|) shows where SEN2SR resolved high frequency details.",
            "confidence_proxy": "Heuristic confidence proxy (uncalibrated) inverse to enhancement deviation.",
            "before": "Before snapshot rendered from configured baseline Sentinel-2 period.",
            "before_ndwi": "Before NDWI highlights water/open-water candidates for the baseline period.",
        },
        "validation_reference": "Synthetic self-consistency validation: native Sentinel-2 10m tile is treated as the reference target under controlled degradation.",
        "model": {"variant": MODEL_VARIANT, "device": str(DEVICE), "status": MODEL_STATUS or "loaded", "internal_lr": MODEL_INTERNAL_LR},
    }

