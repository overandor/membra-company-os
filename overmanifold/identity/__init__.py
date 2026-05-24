"""
Overmanifold Identity Module
Transport-independent identity management with DID integration.
"""

from .endpoint import Endpoint, EndpointRegistry
from .did import DIDDocument, DIDResolver, DIDGenerator, DIDAuthentication

__all__ = [
    "Endpoint",
    "EndpointRegistry",
    "DIDDocument",
    "DIDResolver",
    "DIDGenerator",
    "DIDAuthentication"
]