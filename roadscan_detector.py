"""Single-image YOLO inference returning RDD2022 D codes and pixel boxes."""
from pathlib import Path
import math

_NAME_TO_CODE = {
    'd00': 'D00', 'longitudinal_crack': 'D00',
    'd10': 'D10', 'transverse_crack': 'D10',
    'd20': 'D20', 'alligator_crack': 'D20',
    'd40': 'D40', 'pothole': 'D40',
}


class RoadDamageDetector:
    """Load a local four-class checkpoint once, then call detect_damage(image).

    image: a local image path, PIL image, or OpenCV BGR numpy array.
    Output: JSON-compatible detections; bbox_xyxy is in original-image pixels.
    An empty list means no detection above the threshold, not a verified safe road.
    """

    def __init__(self, weights, *, device='cpu', imgsz=640):
        weights = Path(weights)
        if not weights.is_file():
            raise FileNotFoundError(f'Checkpoint not found: {weights}')
        if not isinstance(imgsz, int) or isinstance(imgsz, bool) or imgsz <= 0:
            raise ValueError('imgsz must be a positive integer.')
        from ultralytics import YOLO
        self._model = YOLO(str(weights))
        self.device = device
        self.imgsz = imgsz
        names = self._model.names
        names = dict(enumerate(names)) if isinstance(names, (list, tuple)) else names
        try:
            self._codes = {int(i): _NAME_TO_CODE[str(name).strip().lower()]
                           for i, name in names.items()}
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError('Expected D00/D10/D20/D40 or the published semantic class names; incompatible checkpoint.') from exc
        if len(self._codes) != 4 or set(self._codes.values()) != {'D00', 'D10', 'D20', 'D40'}:
            raise ValueError('Checkpoint must contain each of the four RDD2022 damage classes exactly once.')

    def detect_damage(self, image, *, confidence=0.25, iou=0.7):
        """Return every retained damage as damage_code, bbox_xyxy, confidence.

        confidence=0.25 is provisional, not a validated deployment threshold.
        Invalid/unreadable images raise an exception, rather than returning [].
        """
        for name, value in [('confidence', confidence), ('iou', iou)]:
            if not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f'{name} must be between 0 and 1.')
        if image is None or isinstance(image, (list, tuple, int, float)):
            raise TypeError('Pass one local image path, PIL image, or OpenCV BGR numpy array.')
        if isinstance(image, (str, Path)):
            from PIL import Image
            with Image.open(image) as opened:
                image = opened.convert('RGB')
        else:
            # PIL images use RGB; numpy input follows Ultralytics OpenCV BGR convention.
            from PIL import Image
            import numpy as np
            if isinstance(image, Image.Image):
                image = image.convert('RGB')
            elif not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3 or image.size == 0:
                raise TypeError('Array input must be a nonempty H x W x 3 BGR image.')
        results = self._model.predict(source=image, imgsz=self.imgsz,
                                      conf=confidence, iou=iou, max_det=300,
                                      device=self.device, verbose=False)
        if len(results) != 1:
            raise ValueError('Expected exactly one image result.')
        boxes = results[0].boxes
        if boxes is None:
            return []
        detections = []
        for xyxy, cls_id, score in zip(boxes.xyxy.cpu().tolist(),
                                       boxes.cls.cpu().tolist(),
                                       boxes.conf.cpu().tolist()):
            detections.append({
                'damage_code': self._codes[int(cls_id)],
                'bbox_xyxy': [float(v) for v in xyxy],
                'confidence': float(score),
            })
        return detections
