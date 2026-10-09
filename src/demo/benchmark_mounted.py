"""File read, directory-list, and bounded write benchmarks for mounted Isilon."""

import argparse
import os
import re
import statistics
import subprocess
import uuid
from pathlib import Path
from time import perf_counter

MAX_WRITE_MIB = 1024


def _mounted_path(mountpoint: Path, relative_path: Path) -> Path:
    """Return a path inside an active CIFS/SMB mount."""
    mountpoint = mountpoint.expanduser().resolve()
    if not os.path.ismount(mountpoint):
        raise ValueError(f"Not a mounted filesystem: {mountpoint}")
    mount_output = subprocess.check_output(["mount"], text=True)
    mount_pattern = (
        rf" on {re.escape(str(mountpoint))} "
        r"(?:type (?:cifs|smb3)\b|\((?:smbfs|cifs),)"
    )
    if not re.search(mount_pattern, mount_output):
        raise ValueError(f"Not a CIFS/SMB mount: {mountpoint}")
    source = (mountpoint / relative_path).resolve()
    if not source.is_relative_to(mountpoint):
        raise ValueError("Path must be inside the CIFS/SMB mount")
    return source


def validate_source(mountpoint: Path, relative_file: Path) -> Path:
    """Require an existing file inside an active CIFS/SMB mount."""
    source = _mounted_path(mountpoint, relative_file)
    if not source.is_file():
        raise ValueError(f"Not a regular file: {source}")
    return source


def validate_directory(mountpoint: Path, relative_dir: Path) -> Path:
    """Require an existing directory inside an active CIFS/SMB mount."""
    source = _mounted_path(mountpoint, relative_dir)
    if not source.is_dir():
        raise ValueError(f"Not a directory: {source}")
    return source


def benchmark_read(
    source: Path, repeats: int = 3, chunk_size: int = 1024 * 1024
) -> list[tuple[int, float]]:
    """Read a file in chunks and return (bytes, seconds) for each pass."""
    results = []
    for _ in range(repeats):
        start = perf_counter()
        size = 0
        with source.open("rb") as file:
            while chunk := file.read(chunk_size):
                size += len(chunk)
        results.append((size, perf_counter() - start))
    return results


def benchmark_list(source: Path, repeats: int = 3) -> list[tuple[int, float]]:
    """Enumerate immediate directory entries and return (count, seconds) per pass."""
    results = []
    for _ in range(repeats):
        start = perf_counter()
        with os.scandir(source) as entries:
            count = sum(1 for _ in entries)
        results.append((count, perf_counter() - start))
    return results


def benchmark_write(
    mountpoint: Path, size_mib: int = 1024, pattern: str = "random"
) -> tuple[Path, int, float, float]:
    """Write and sync one new file in an exclusively created directory."""
    if not 1 <= size_mib <= MAX_WRITE_MIB:
        raise ValueError(f"write size must be between 1 and {MAX_WRITE_MIB} MiB")
    if pattern not in {"random", "zeros"}:
        raise ValueError("pattern must be random or zeros")
    root = _mounted_path(mountpoint, Path("."))
    run_dir = root / f"benchmark-write-{uuid.uuid4().hex}"
    run_dir.mkdir(mode=0o700)
    if not os.path.ismount(root):
        raise OSError(f"Mount disconnected before writing; directory at {run_dir}")
    target = run_dir / f"{pattern}.bin"
    chunk_size = 1024 * 1024
    zero_chunk = bytes(chunk_size)
    written = 0
    start = perf_counter()
    try:
        with target.open("xb", buffering=0) as output:
            for _ in range(size_mib):
                chunk = os.urandom(chunk_size) if pattern == "random" else zero_chunk
                if output.write(chunk) != len(chunk):
                    raise OSError(f"Short write in {target}")
                written += len(chunk)
            write_seconds = perf_counter() - start
            sync_start = perf_counter()
            os.fsync(output.fileno())
            sync_seconds = perf_counter() - sync_start
        if not os.path.ismount(root):
            raise OSError("Mount disconnected during write")
        if target.stat().st_size != written:
            raise OSError(f"File size mismatch in {target}")
    except OSError as exc:
        raise OSError(f"{exc}; benchmark data left at {run_dir}") from exc
    return run_dir, written, write_seconds, sync_seconds


def main(argv: list[str] | None = None) -> None:
    """Benchmark file reads, listings, or new-file writes on a CIFS/SMB mount."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mount", type=Path, required=True, help="CIFS/SMB mountpoint")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--file", type=Path, help="file relative to the mountpoint")
    target.add_argument(
        "--directory", type=Path, help="directory relative to the mountpoint"
    )
    target.add_argument(
        "--write-mib", type=int, help="write 1-1024 MiB in a new directory"
    )
    parser.add_argument(
        "--write-pattern", choices=("zeros", "random"), default="random"
    )
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    if args.write_mib is not None:
        try:
            run_dir, size, write_seconds, sync_seconds = benchmark_write(
                args.mount, size_mib=args.write_mib, pattern=args.write_pattern
            )
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        print(f"New directory: {run_dir} (left in place)")
        print(
            f"Write: {size / 1024**2:.2f} MiB in {write_seconds:.3f} s, "
            f"{size / (1024**2 * write_seconds):.2f} MiB/s"
        )
        total_seconds = write_seconds + sync_seconds
        print(
            f"fsync: {sync_seconds:.3f} s; total: {total_seconds:.3f} s, "
            f"{size / (1024**2 * total_seconds):.2f} MiB/s"
        )
        return
    if args.directory is not None:
        try:
            source = validate_directory(args.mount, args.directory)
            results = benchmark_list(source, repeats=args.repeats)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        print(f"Directory: {source} (read-only; immediate entries, no stat)")
        for index, (count, seconds) in enumerate(results, start=1):
            print(
                f"Run {index}: {count} entries in {seconds * 1000:.3f} ms "
                f"({count / seconds:.0f} entries/s)"
            )
        median_seconds = statistics.median(seconds for _, seconds in results)
        print(f"Median: {median_seconds * 1000:.3f} ms")
        print("Later runs may use client/server caches; this is not cold-cache I/O.")
        return
    try:
        source = validate_source(args.mount, args.file)
        if source.stat().st_size == 0:
            parser.error("file must not be empty")
        results = benchmark_read(source, repeats=args.repeats)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    print(f"File: {source} (read-only; {results[0][0]} bytes)")
    for index, (size, seconds) in enumerate(results, start=1):
        print(f"Run {index}: {seconds:.3f} s, {size / (1024**2 * seconds):.2f} MiB/s")
    median_seconds = statistics.median(seconds for _, seconds in results)
    print(
        f"Median: {median_seconds:.3f} s, "
        f"{results[0][0] / (1024**2 * median_seconds):.2f} MiB/s"
    )
    print("Later runs may use client/server caches; this is not cold-cache I/O.")


if __name__ == "__main__":
    main()
