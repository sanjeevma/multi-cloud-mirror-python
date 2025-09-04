# utils/logger.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

import sys
from typing import Optional


class Logger:
  # Color codes
  RED = '\033[0;31m'
  GREEN = '\033[0;32m'
  YELLOW = '\033[1;33m'
  BLUE = '\033[0;34m'
  NC = '\033[0m'  # No Color

  def __init__(self, debug: bool = False):
    self.debug_enabled = debug

  def info(self, message: str):
    """Log info message"""
    print(f"{self.BLUE}[INFO]{self.NC} {message}")

  def success(self, message: str):
    """Log success message"""
    print(f"{self.GREEN}[SUCCESS]{self.NC} {message}")

  def warning(self, message: str):
    """Log warning message"""
    print(f"{self.YELLOW}[WARNING]{self.NC} {message}")

  def error(self, message: str):
    """Log error message"""
    print(f"{self.RED}[ERROR]{self.NC} {message}", file=sys.stderr)

  def debug(self, message: str):
    """Log debug message if debug is enabled"""
    if self.debug_enabled:
      print(f"{self.YELLOW}[DEBUG]{self.NC} {message}")

  def raw(self, message: str):
    """Print raw message without formatting"""
    print(message)
