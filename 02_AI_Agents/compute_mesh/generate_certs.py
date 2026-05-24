"""Generate self-signed TLS certificates for compute_mesh."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate_self_signed(hostname: str = "localhost", out_dir: str = "certs") -> tuple[str, str]:
    """Generate a self-signed cert/key pair using cryptography."""
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
    except ImportError:
        raise RuntimeError("Install cryptography: pip install cryptography")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    key_path = out_path / "key.pem"
    cert_path = out_path / "cert.pem"

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, hostname)])
    alt_names = x509.SubjectAlternativeName([
        x509.DNSName(hostname),
        x509.DNSName("*." + hostname),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .add_extension(alt_names, critical=False)
        .sign(key, hashes.SHA256())
    )

    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    print(f"Generated: {cert_path}, {key_path}")
    return str(cert_path), str(key_path)


if __name__ == "__main__":
    import argparse
    import ipaddress

    parser = argparse.ArgumentParser(description="Generate self-signed TLS certs")
    parser.add_argument("--hostname", default="localhost")
    parser.add_argument("--out-dir", default="certs")
    args = parser.parse_args()
    generate_self_signed(args.hostname, args.out_dir)
