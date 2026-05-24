"""
Overmanifold Validators Module
Browser-native WebAssembly/WebGPU validator surfaces.
"""

from .browser_surface import (
    ValidationTarget,
    ComputeBackend,
    ValidationTask,
    ValidationResult,
    ValidatorSurface,
    WebAssemblyValidator,
    WebGPUValidator,
    BrowserValidatorSurface,
    ValidatorSurfaceIntegration
)

__all__ = [
    "ValidationTarget",
    "ComputeBackend",
    "ValidationTask",
    "ValidationResult",
    "ValidatorSurface",
    "WebAssemblyValidator",
    "WebGPUValidator",
    "BrowserValidatorSurface",
    "ValidatorSurfaceIntegration"
]