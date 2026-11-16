"""Configuración de pytest: añade la raíz del proyecto al path."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
