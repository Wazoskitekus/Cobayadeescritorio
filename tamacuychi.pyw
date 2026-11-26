"""Doble clic para arrancar la cobaya (en Windows se abre sin consola)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tamacuychi.app import main  # noqa: E402

sys.exit(main())
