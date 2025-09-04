# utils/types.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class ValidationResult:
  success: bool
  message: Optional[str] = None
  details: Optional[Dict[str, Any]] = None


@dataclass
class MirrorResult:
  total_images: int
  successful_images: int
  failed_images: int
  failed_image_details: Optional[List[Dict[str, str]]] = None


@dataclass
class RegistryConfig:
  name: str
  enabled: bool
  regions: Optional[List[str]] = None
  url: Optional[str] = None
  credentials: Optional[Dict[str, str]] = None


@dataclass
class ImageInfo:
  source: str
  repository: str
  tag: str
  destinations: List[str]
  line_number: int


@dataclass
class PushResult:
  success: bool
  source: str
  target: str
  error_message: Optional[str] = None
  retry_count: int = 0
