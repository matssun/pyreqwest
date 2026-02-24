#!/usr/bin/env python3
"""Build a wheel from Bazel-compiled pyreqwest shared library + Python sources.

Usage:
    python build_wheel.py --so-path <path-to-.so> --python-dir <python-source-dir> --out-dir <output-dir> --platform <platform-tag>

Example:
    python build_wheel.py \
        --so-path bazel-out/.../libpyreqwest.dylib \
        --python-dir python/pyreqwest \
        --out-dir dist \
        --platform manylinux_2_28_aarch64
"""

import argparse
import hashlib
import base64
import os
import sys
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


VERSION = "0.11.0"
PACKAGE_NAME = "pyreqwest"


def sha256_digest_b64(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def make_zipinfo(name: str) -> ZipInfo:
    info = ZipInfo(name)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def detect_so_name(platform_tag: str) -> str:
    """Determine the .so filename based on the platform tag."""
    python_tag = f"cpython-313-{'aarch64-linux-gnu' if 'linux' in platform_tag else 'darwin'}"
    return f"_pyreqwest.{python_tag}.so"


def build_wheel(so_path: Path, python_dir: Path, out_dir: Path, platform_tag: str) -> Path:
    python_version = "cp313"
    wheel_name = f"{PACKAGE_NAME}-{VERSION}-{python_version}-{python_version}-{platform_tag}.whl"
    wheel_path = out_dir / wheel_name
    out_dir.mkdir(parents=True, exist_ok=True)

    so_target_name = detect_so_name(platform_tag)
    dist_info = f"{PACKAGE_NAME}-{VERSION}.dist-info"

    records: list[tuple[str, str, int]] = []

    with ZipFile(wheel_path, "w", ZIP_DEFLATED) as whl:
        # Add Python source files
        for root, _dirs, files in os.walk(python_dir):
            for filename in sorted(files):
                filepath = Path(root) / filename
                rel_path = filepath.relative_to(python_dir.parent)
                arcname = str(rel_path)
                data = filepath.read_bytes()
                info = make_zipinfo(arcname)
                whl.writestr(info, data)
                records.append((arcname, sha256_digest_b64(data), len(data)))

        # Add the shared library
        so_data = so_path.read_bytes()
        so_arcname = f"{PACKAGE_NAME}/{so_target_name}"
        info = make_zipinfo(so_arcname)
        info.external_attr = 0o755 << 16
        whl.writestr(info, so_data)
        records.append((so_arcname, sha256_digest_b64(so_data), len(so_data)))

        # METADATA
        metadata = (
            f"Metadata-Version: 2.4\n"
            f"Name: {PACKAGE_NAME}\n"
            f"Version: {VERSION}\n"
            f"Summary: Rust-powered HTTP client with Python bindings\n"
            f"License: MIT\n"
            f"Requires-Python: >=3.11\n"
        )
        metadata_bytes = metadata.encode()
        info = make_zipinfo(f"{dist_info}/METADATA")
        whl.writestr(info, metadata_bytes)
        records.append((f"{dist_info}/METADATA", sha256_digest_b64(metadata_bytes), len(metadata_bytes)))

        # WHEEL
        wheel_meta = (
            f"Wheel-Version: 1.0\n"
            f"Generator: bazel-pyreqwest\n"
            f"Root-Is-Purelib: false\n"
            f"Tag: {python_version}-{python_version}-{platform_tag}\n"
        )
        wheel_bytes = wheel_meta.encode()
        info = make_zipinfo(f"{dist_info}/WHEEL")
        whl.writestr(info, wheel_bytes)
        records.append((f"{dist_info}/WHEEL", sha256_digest_b64(wheel_bytes), len(wheel_bytes)))

        # RECORD (self-entry has no hash)
        record_lines = [f"{name},sha256={digest},{size}" for name, digest, size in records]
        record_lines.append(f"{dist_info}/RECORD,,")
        record_content = "\n".join(record_lines) + "\n"
        info = make_zipinfo(f"{dist_info}/RECORD")
        whl.writestr(info, record_content.encode())

    return wheel_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pyreqwest wheel from Bazel output")
    parser.add_argument("--so-path", required=True, help="Path to the compiled .so/.dylib")
    parser.add_argument("--python-dir", required=True, help="Path to python/pyreqwest source directory")
    parser.add_argument("--out-dir", required=True, help="Output directory for the wheel")
    parser.add_argument("--platform", required=True, help="Platform tag (e.g. manylinux_2_28_aarch64)")
    args = parser.parse_args()

    so_path = Path(args.so_path)
    python_dir = Path(args.python_dir)
    out_dir = Path(args.out_dir)

    if not so_path.exists():
        print(f"Error: shared library not found at {so_path}", file=sys.stderr)
        sys.exit(1)

    if not python_dir.exists():
        print(f"Error: Python source directory not found at {python_dir}", file=sys.stderr)
        sys.exit(1)

    wheel_path = build_wheel(so_path, python_dir, out_dir, args.platform)
    print(f"Built wheel: {wheel_path}")
    print(f"Size: {wheel_path.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
