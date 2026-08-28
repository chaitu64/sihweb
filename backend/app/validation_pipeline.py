import base64
import io
from typing import Any

import matplotlib
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, PowerNorm


def _png_data_url(array: np.ndarray) -> str:
    image = Image.fromarray(np.clip(array * 255, 0, 255).astype(np.uint8), "RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _gray_png_data_url(
    array: np.ndarray,
    cmap: str,
    vmin: float | None = None,
    vmax: float | None = None,
    gamma: float = 1.0,
) -> str:
    clean_array = np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)
    if vmin is None:
        vmin = float(np.percentile(clean_array, 1))
    if vmax is None:
        vmax = float(np.percentile(clean_array, 99))
    if vmax <= vmin:
        vmax = vmin + 1e-8

    norm = PowerNorm(gamma=gamma, vmin=vmin, vmax=vmax) if gamma != 1.0 else Normalize(vmin=vmin, vmax=vmax)
    figure, axis = plt.subplots(figsize=(5, 5), dpi=120)
    image = axis.imshow(clean_array, cmap=cmap, norm=norm)
    axis.axis("off")
    figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    figure.tight_layout(pad=0)
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(figure)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _dashboard_data_url(
    lr_disp: np.ndarray,
    sr_disp: np.ndarray,
    hr_disp: np.ndarray,
    uncertainty_map: np.ndarray,
    ndvi_hr: np.ndarray,
    psnr_val: float,
    ssim_val: float,
    sam_val: float,
    rmse_val: float,
) -> str:
    fig, axes = plt.subplots(1, 5, figsize=(25, 5))
    axes[0].imshow(lr_disp)
    axes[0].set_title(f"1. LR Input (10m)\n{lr_disp.shape[0]}x{lr_disp.shape[1]}")
    axes[0].axis("off")
    axes[1].imshow(sr_disp)
    axes[1].set_title(f"2. AI SR Output (2.5m)\n{sr_disp.shape[0]}x{sr_disp.shape[1]}")
    axes[1].axis("off")
    axes[2].imshow(hr_disp)
    axes[2].set_title(f"3. HR Ground-Truth Ref\n{hr_disp.shape[0]}x{hr_disp.shape[1]}")
    axes[2].axis("off")
    uncertainty_vmax = max(float(np.percentile(uncertainty_map, 99.5)), 1e-8)
    uncertainty_norm = PowerNorm(gamma=0.45, vmin=0.0, vmax=uncertainty_vmax)
    im3 = axes[3].imshow(uncertainty_map, cmap="inferno", norm=uncertainty_norm)
    axes[3].set_title("4. Uncertainty Map\n(Inferred Detail Intensity)")
    axes[3].axis("off")
    fig.colorbar(im3, ax=axes[3], fraction=0.046, pad=0.04)
    im4 = axes[4].imshow(ndvi_hr, cmap="YlGn")
    axes[4].set_title("5. Analytics\n(2.5m Enhanced NDVI)")
    axes[4].axis("off")
    fig.colorbar(im4, ax=axes[4], fraction=0.046, pad=0.04)
    plt.suptitle(
        f"NTRO PS 26142 — Deep Learning Super-Resolution Mapping with Reference Validation\n"
        f"PSNR: {psnr_val:.2f} dB  |  SSIM: {ssim_val:.4f}  |  "
        f"SAM: {sam_val:.4f} rad  |  RMSE: {rmse_val:.4f}",
        fontsize=13,
        y=1.06,
        fontweight="bold",
    )
    plt.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _stretch(rgb_arr: np.ndarray) -> np.ndarray:
    p2, p98 = np.percentile(rgb_arr, (2, 98))
    return np.clip((rgb_arr - p2) / (p98 - p2 + 1e-8), 0, 1)


def _decode_reference(image_bytes: bytes) -> torch.Tensor:
    source = Image.open(io.BytesIO(image_bytes))
    channels = 4 if source.mode in ("RGBA", "CMYK", "I;16", "F") else 3
    image = source.convert("RGBA" if channels == 4 else "RGB")
    image = image.resize((512, 512), Image.Resampling.BILINEAR)
    raw_np = np.asarray(image).astype(np.float32) / 255.0
    raw_np = np.nan_to_num(raw_np, nan=0.0, posinf=0.0, neginf=0.0)
    return torch.from_numpy(raw_np.transpose(2, 0, 1)).float()


def _run_super_resolution(lr_input: torch.Tensor) -> torch.Tensor:
    try:
        import mlstac

        mlstac.download(
            file="https://huggingface.co/tacofoundation/sen2sr/resolve/main/SEN2SRLite/NonReference_RGBN_x4/mlm.json",
            output_dir="model/SEN2SRLite_RGBN",
        )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = mlstac.load("model/SEN2SRLite_RGBN").compiled_model(device=device)
        with torch.no_grad():
            return model(lr_input.to(device)[None]).squeeze(0).cpu()
    except (ImportError, OSError, RuntimeError, ValueError):
        # Keep the API usable when the optional SEN2SR model package is absent.
        return F.interpolate(lr_input[None], size=(512, 512), mode="bicubic", align_corners=False).squeeze(0)


def process_image(image_bytes: bytes) -> dict[str, Any]:
    hr_reference = _decode_reference(image_bytes)
    lr_input = F.interpolate(hr_reference[None], scale_factor=0.25, mode="area").squeeze(0)
    sr_output = _run_super_resolution(lr_input)

    c_h = min(sr_output.shape[1], hr_reference.shape[1])
    c_w = min(sr_output.shape[2], hr_reference.shape[2])
    sr_output = sr_output[:, :c_h, :c_w]
    hr_reference = hr_reference[:, :c_h, :c_w]

    bicubic_baseline = F.interpolate(
        lr_input[None], size=(c_h, c_w), mode="bicubic", align_corners=False
    ).squeeze(0)
    uncertainty_map = torch.abs(sr_output[:3] - bicubic_baseline[:3]).mean(dim=0).numpy()
    uncertainty_vmax = max(float(np.percentile(uncertainty_map, 99.5)), 1e-8)
    nir_hr = sr_output[3].numpy()
    red_hr = sr_output[0].numpy()
    ndvi_hr = (nir_hr - red_hr) / (nir_hr + red_hr + 1e-8)

    sr_np = sr_output[:3].numpy().transpose(1, 2, 0)
    hr_np = hr_reference[:3].numpy().transpose(1, 2, 0)
    sr_norm = np.clip(sr_np / (np.max(sr_np) + 1e-8), 0, 1)
    hr_norm = np.clip(hr_np / (np.max(hr_np) + 1e-8), 0, 1)

    psnr_val = psnr(hr_norm, sr_norm, data_range=1.0)
    ssim_val = ssim(hr_norm, sr_norm, channel_axis=2, data_range=1.0)
    dot = np.sum(sr_norm * hr_norm, axis=2)
    norm_sr = np.linalg.norm(sr_norm, axis=2)
    norm_hr = np.linalg.norm(hr_norm, axis=2)
    sam_val = np.mean(np.arccos(np.clip(dot / (norm_sr * norm_hr + 1e-8), -1.0, 1.0)))
    rmse_val = np.sqrt(np.mean((hr_norm - sr_norm) ** 2))

    lr_disp = _stretch(lr_input[:3].numpy().transpose(1, 2, 0))
    sr_disp = _stretch(sr_np)
    hr_disp = _stretch(hr_np)

    return {
        "outputs": {
            "lr_input": _png_data_url(lr_disp),
            "sr_output": _png_data_url(sr_disp),
            "hr_reference": _png_data_url(hr_disp),
            "uncertainty_map": _gray_png_data_url(
                uncertainty_map, "inferno", vmin=0.0, vmax=uncertainty_vmax, gamma=0.45
            ),
            "ndvi": _gray_png_data_url(ndvi_hr, "YlGn", vmin=-1.0, vmax=1.0),
            "validation_dashboard": _dashboard_data_url(
                lr_disp, sr_disp, hr_disp, uncertainty_map, ndvi_hr,
                psnr_val, ssim_val, sam_val, rmse_val,
            ),
        },
        "metrics": {
            "psnr": float(psnr_val),
            "ssim": float(ssim_val),
            "sam": float(sam_val),
            "rmse": float(rmse_val),
        },
        "validation_reference": (
            "Synthetic validation: the API image is treated as HR_Reference, "
            "downsampled to LR_Input, then compared with the reconstruction."
        ),
    }