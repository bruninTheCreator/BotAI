"""
Perception module with hybrid text extraction.
Primary source: Windows UI Automation (when available).
Fallback/source enrichment: OCR over screenshot.
"""

from __future__ import annotations

import os
import re
import subprocess
from contextlib import nullcontext
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pyautogui
import pytesseract

try:
    from pywinauto import Desktop  # type: ignore
except Exception:
    Desktop = None
try:
    import win32gui  # type: ignore
except Exception:
    win32gui = None

from .base import Perception, Result
from .config import get_config
from .logging_module import PerformanceTracker, get_logger


class ImagePreprocessor:
    """Image preprocessor to improve OCR quality."""

    def __init__(self, scale: float = 1.5, use_threshold: bool = True):
        self.scale = scale
        self.use_threshold = use_threshold
        self.logger = get_logger("ImagePreprocessor")

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for OCR."""
        try:
            if self.scale > 1.0:
                height, width = image.shape[:2]
                new_width = int(width * self.scale)
                new_height = int(height * self.scale)
                image = cv2.resize(image, (new_width, new_height))

            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            if self.use_threshold:
                _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            else:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)

            return gray
        except Exception as e:
            self.logger.error(f"Erro ao preprocessar imagem: {e}")
            return image


class PerceptionImpl(Perception):
    """Perception implementation with UI Automation + OCR fallback."""

    def __init__(self):
        super().__init__("Perception")
        self.config = get_config()
        self.logger = get_logger("Perception")
        self._tesseract_available = False
        self._ui_automation_available = False

        self._setup_tesseract()
        self._setup_ui_automation()

        self.preprocessor = ImagePreprocessor(
            scale=self.config.perception.preprocessing_scale,
            use_threshold=self.config.perception.use_preprocessing,
        )

    def _setup_tesseract(self) -> None:
        """Configure tesseract executable path."""
        tesseract_path = self.config.perception.tesseract_path

        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            self._tesseract_available = True
            self.logger.info(f"Tesseract configurado em: {tesseract_path}")
            return

        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tesseract-OCR\tesseract.exe",
            r"C:\Users\A21057836\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                self._tesseract_available = True
                self.logger.info(f"Tesseract encontrado em: {path}")
                return

        try:
            result = subprocess.run(["where", "tesseract"], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip().split("\n")[0]
                if path:
                    pytesseract.pytesseract.tesseract_cmd = path
                    self._tesseract_available = True
                    self.logger.info(f"Tesseract encontrado via PATH: {path}")
                    return
        except Exception:
            pass

        self._tesseract_available = False
        self.logger.warning("Tesseract-OCR nao foi encontrado. OCR sera limitado.")

    def _setup_ui_automation(self) -> None:
        """Configure UI Automation availability."""
        if not self.config.perception.use_ui_automation:
            self._ui_automation_available = False
            self.logger.info("UI Automation desabilitado por configuracao.")
            return

        if Desktop is None:
            self._ui_automation_available = False
            self.logger.warning("pywinauto nao instalado. UI Automation indisponivel.")
            return

        self._ui_automation_available = True
        self.logger.info(
            "UI Automation habilitado.",
            max_elements=self.config.perception.ui_max_elements,
            max_depth=self.config.perception.ui_max_depth,
        )

    async def initialize(self) -> Result[None]:
        """Initialize perception module."""
        try:
            screenshot = await self.capture_screen()
            if not screenshot.success:
                return Result.from_error("Falha ao capturar tela na inicializacao")

            self.initialized = True
            self.logger.info("Modulo de Percepcao inicializado com sucesso")
            return Result.ok(None)
        except Exception as e:
            return Result.from_error(f"Erro ao inicializar Percepcao: {e}")

    async def shutdown(self) -> Result[None]:
        """Shutdown perception module."""
        self.initialized = False
        self.logger.info("Modulo de Percepcao encerrado")
        return Result.ok(None)

    async def capture_screen(self, region: Optional[Tuple] = None) -> Result[np.ndarray]:
        """Capture full screen or region."""
        try:
            screenshot = pyautogui.screenshot(region=region)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            self.logger.debug(f"Tela capturada: {img.shape}")
            return Result.ok(img)
        except Exception as e:
            return Result.from_error(f"Erro ao capturar tela: {e}")

    def _read_text_via_ui_automation(self) -> Tuple[str, Dict[str, Any]]:
        """Read text from active window accessibility tree."""
        if not self._ui_automation_available:
            return "", {"available": False}

        lines: List[str] = []
        seen = set()
        scanned = 0
        title = ""

        max_elements = max(20, int(self.config.perception.ui_max_elements))
        max_depth = max(1, int(self.config.perception.ui_max_depth))

        try:
            desktop = Desktop(backend="uia")
            active_window = None

            if win32gui is not None:
                try:
                    handle = win32gui.GetForegroundWindow()
                    if handle:
                        active_window = desktop.window(handle=handle)
                except Exception:
                    active_window = None

            try:
                if active_window is None:
                    active_window = desktop.active_window()
            except Exception:
                if active_window is None:
                    active_window = None

            if active_window is None:
                try:
                    active_window = desktop.top_window()
                except Exception:
                    active_window = None

            if active_window is None:
                return "", {"available": True, "reason": "no_active_window"}

            try:
                title = (active_window.window_text() or "").strip()
            except Exception:
                title = ""

            if title:
                lines.append(f"window: {title}")
                seen.add(title.lower())

            descendants = []
            try:
                descendants = active_window.descendants(depth=max_depth)
            except TypeError:
                descendants = active_window.descendants()
            except Exception:
                descendants = []

            if not descendants:
                return "\n".join(lines).strip(), {
                    "available": True,
                    "elements_scanned": 0,
                    "window_title": title,
                }

            for element in descendants:
                if scanned >= max_elements:
                    break
                scanned += 1

                control_type = ""
                candidates: List[str] = []

                try:
                    control_type = (getattr(element.element_info, "control_type", "") or "").strip()
                except Exception:
                    control_type = ""

                try:
                    texts = element.texts()
                    for t in texts:
                        if isinstance(t, str):
                            candidates.append(t)
                except Exception:
                    pass

                if not candidates:
                    try:
                        info = element.element_info
                        name = (getattr(info, "name", "") or "").strip()
                        rich_text = (getattr(info, "rich_text", "") or "").strip()
                        if name:
                            candidates.append(name)
                        if rich_text and rich_text.lower() != name.lower():
                            candidates.append(rich_text)
                    except Exception:
                        pass

                for raw in candidates:
                    cleaned = " ".join(str(raw).split()).strip()
                    if len(cleaned) < 2:
                        continue

                    key = cleaned.lower()
                    if key in seen:
                        continue
                    seen.add(key)

                    if control_type:
                        line = f"{control_type}: {cleaned}"
                    else:
                        line = cleaned

                    lines.append(line)
                    if len(lines) >= max_elements:
                        break

                if len(lines) >= max_elements:
                    break

            text = "\n".join(lines).strip()
            meta = {
                "available": True,
                "elements_scanned": scanned,
                "lines": len(lines),
                "window_title": title,
            }
            return text, meta
        except Exception as e:
            self.logger.debug("UI Automation falhou no contexto atual", error=str(e))
            return "", {"available": True, "error": str(e)}

    async def _read_text_via_ocr(self, region: Optional[Tuple] = None) -> str:
        """Read text from screen using OCR."""
        try:
            result = await self.capture_screen(region)
            if not result.success:
                return ""

            img = result.data
            if self.config.perception.use_preprocessing:
                img = self.preprocessor.preprocess(img)

            try:
                text = pytesseract.image_to_string(img, lang=self.config.perception.ocr_lang)
            except Exception as e:
                if self._tesseract_available:
                    self.logger.warning(f"Erro no OCR: {e}")
                return ""

            return (text or "").strip()
        except Exception:
            return ""

    def _merge_text_sources(self, primary: str, secondary: str) -> str:
        """Merge and deduplicate text lines from multiple sources."""
        lines: List[str] = []
        seen = set()

        for block in (primary or "", secondary or ""):
            for line in block.splitlines():
                cleaned = " ".join(line.split()).strip()
                if not cleaned:
                    continue
                key = cleaned.lower()
                if key in seen:
                    continue
                seen.add(key)
                lines.append(cleaned)

        return "\n".join(lines).strip()

    def _redact_sensitive_text(self, text: str) -> str:
        """Redact obvious credentials/tokens from captured text."""
        if not text:
            return text

        redacted = text

        patterns = [
            # OpenAI-like keys and generic secret tokens
            (r"\bsk-[A-Za-z0-9_\-]{20,}\b", "[REDACTED_API_KEY]"),
            (r"\b(?:ghp|gho|github_pat)_[A-Za-z0-9_]{20,}\b", "[REDACTED_TOKEN]"),
            # Password labels
            (r"(?im)\b(password|senha)\s*[:=]\s*\S+", r"\1: [REDACTED]"),
            # Bearer tokens
            (r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]+=*", "Bearer [REDACTED]"),
        ]

        for pattern, replacement in patterns:
            redacted = re.sub(pattern, replacement, redacted)

        return redacted

    async def read_text(self, region: Optional[Tuple] = None) -> Result[str]:
        """Read text with hybrid strategy: UI Automation + OCR fallback."""
        tracker = PerformanceTracker(self.logger, "ReadText") if self.config.debug else nullcontext()
        with tracker:
            try:
                ui_text = ""
                ui_meta: Dict[str, Any] = {}

                # UI Automation is global (active window), so skip if a region is requested.
                if region is None:
                    ui_text, ui_meta = self._read_text_via_ui_automation()

                ocr_text = await self._read_text_via_ocr(region)

                if self.config.perception.merge_ui_and_ocr:
                    merged_text = self._merge_text_sources(ui_text, ocr_text)
                else:
                    merged_text = ui_text or ocr_text

                if ui_text and len(ui_text) < self.config.perception.ui_min_chars and ocr_text:
                    merged_text = ocr_text if not self.config.perception.merge_ui_and_ocr else merged_text

                if self.config.perception.redact_sensitive_text:
                    merged_text = self._redact_sensitive_text(merged_text)

                source = "none"
                if ui_text and ocr_text:
                    source = "uia+ocr"
                elif ui_text:
                    source = "uia"
                elif ocr_text:
                    source = "ocr"

                if merged_text:
                    self.logger.debug(
                        "Texto extraido",
                        source=source,
                        chars=len(merged_text),
                        ui_chars=len(ui_text),
                        ocr_chars=len(ocr_text),
                        ui_elements=ui_meta.get("elements_scanned", 0),
                    )
                else:
                    self.logger.debug("Nenhum texto detectado")

                return Result.ok(
                    merged_text,
                    source=source,
                    ui_chars=len(ui_text),
                    ocr_chars=len(ocr_text),
                    ui_elements=ui_meta.get("elements_scanned", 0),
                )
            except Exception as e:
                return Result.from_error(f"Erro ao ler texto: {e}")

    async def find_element(
        self,
        template_path: str,
        threshold: float = 0.8,
    ) -> Result[Optional[Tuple[int, int]]]:
        """Find element on screen using template matching."""
        try:
            template = cv2.imread(template_path)
            if template is None:
                return Result.from_error(f"Template nao encontrado: {template_path}")

            result = await self.capture_screen()
            if not result.success:
                return result

            screen = result.data
            result_match = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result_match)

            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2

                self.logger.info(
                    "Elemento encontrado",
                    confidence=round(max_val, 3),
                    position=(center_x, center_y),
                )
                return Result.ok((center_x, center_y))

            self.logger.debug(f"Elemento nao encontrado (max_confidence: {max_val:.3f})")
            return Result.ok(None)
        except Exception as e:
            return Result.from_error(f"Erro ao procurar elemento: {e}")

    async def analyze_colors(self, region: Optional[Tuple] = None) -> Result[dict]:
        """Analyze dominant colors in a region."""
        try:
            result = await self.capture_screen(region)
            if not result.success:
                return result

            img = result.data
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0], None, [256], [0, 256])
            dominant_hue = np.argmax(hist)

            analysis = {
                "dominant_hue": int(dominant_hue),
                "image_shape": img.shape,
                "pixel_count": img.shape[0] * img.shape[1],
            }

            return Result.ok(analysis)
        except Exception as e:
            return Result.from_error(f"Erro ao analisar cores: {e}")

    async def detect_edges(self, region: Optional[Tuple] = None) -> Result[np.ndarray]:
        """Detect edges using Canny."""
        try:
            result = await self.capture_screen(region)
            if not result.success:
                return result

            img = result.data
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            return Result.ok(edges)
        except Exception as e:
            return Result.from_error(f"Erro ao detectar bordas: {e}")

    async def get_screen_metadata(self) -> Result[dict]:
        """Return screen metadata."""
        try:
            result = await self.capture_screen()
            if not result.success:
                return result

            img = result.data
            height, width = img.shape[:2]

            metadata = {
                "width": width,
                "height": height,
                "resolution_ratio": f"{width}x{height}",
                "aspect_ratio": round(width / height, 2),
                "total_pixels": width * height,
            }

            return Result.ok(metadata)
        except Exception as e:
            return Result.from_error(f"Erro ao obter metadados: {e}")
