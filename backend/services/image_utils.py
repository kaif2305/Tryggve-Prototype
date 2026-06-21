"""Draw hazard bounding boxes on incident photos."""

from __future__ import annotations

import base64
import io

from PIL import Image, ImageDraw, ImageFont

from models.schemas import HazardBoundingBox

_BOX_COLOR = "#DC2626"
_BOX_WIDTH = 4
_LABEL_PADDING = 4


def _denormalize(coord: int, axis_size: int) -> int:
    """Map a 0–1000 normalized coordinate to pixel space."""
    return int(max(0, min(axis_size, coord / 1000 * axis_size)))


def draw_hazard_boxes(image_bytes: bytes, boxes: list[HazardBoundingBox]) -> str:
    """Draw red hazard boxes on the image and return a base64-encoded JPEG string."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    try:
        font = ImageFont.truetype("arial.ttf", size=max(14, width // 50))
    except OSError:
        font = ImageFont.load_default()

    for box in boxes:
        xmin = _denormalize(box.xmin, width)
        ymin = _denormalize(box.ymin, height)
        xmax = _denormalize(box.xmax, width)
        ymax = _denormalize(box.ymax, height)

        if xmax <= xmin:
            xmax = min(width, xmin + 20)
        if ymax <= ymin:
            ymax = min(height, ymin + 20)

        draw.rectangle(
            [(xmin, ymin), (xmax, ymax)],
            outline=_BOX_COLOR,
            width=_BOX_WIDTH,
        )

        label = box.label.strip() or "Hazard"
        text_bbox = draw.textbbox((0, 0), label, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        label_y = max(0, ymin - text_h - _LABEL_PADDING * 2)
        label_box = [
            xmin,
            label_y,
            xmin + text_w + _LABEL_PADDING * 2,
            label_y + text_h + _LABEL_PADDING * 2,
        ]
        draw.rectangle(label_box, fill=_BOX_COLOR)
        draw.text(
            (xmin + _LABEL_PADDING, label_y + _LABEL_PADDING),
            label,
            fill="white",
            font=font,
        )

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    return base64.b64encode(buffer.getvalue()).decode("ascii")
