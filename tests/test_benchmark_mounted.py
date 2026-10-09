"""Tests for the mounted CIFS read, list, and bounded write benchmarks."""

import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.demo import benchmark_mounted


class BenchmarkReadTests(unittest.TestCase):
    def test_repeated_reads_leave_source_unchanged(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            source = Path(directory) / "image.tif"
            content = b"an image" * 100
            source.write_bytes(content)

            results = benchmark_mounted.benchmark_read(source, repeats=2, chunk_size=17)

            self.assertEqual(len(results), 2)
            self.assertTrue(all(size == len(content) for size, _ in results))
            self.assertTrue(all(seconds > 0 for _, seconds in results))
            self.assertEqual(source.read_bytes(), content)

    def test_source_requires_cifs_mount_and_stays_inside_it(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            mountpoint = Path(directory)
            source = mountpoint / "image.tif"
            source.write_bytes(b"image")
            with (
                patch("os.path.ismount", return_value=False),
                self.assertRaisesRegex(ValueError, "mounted"),
            ):
                benchmark_mounted.validate_source(mountpoint, Path("image.tif"))
            with (
                patch("os.path.ismount", return_value=True),
                patch("subprocess.check_output", return_value="not a CIFS mount"),
                self.assertRaisesRegex(ValueError, "CIFS/SMB"),
            ):
                benchmark_mounted.validate_source(mountpoint, Path("image.tif"))
            with (
                patch("os.path.ismount", return_value=True),
                patch(
                    "subprocess.check_output",
                    return_value=f"//server/share on {mountpoint} (smbfs, nodev)",
                ),
            ):
                self.assertEqual(
                    benchmark_mounted.validate_source(mountpoint, Path("image.tif")),
                    source,
                )
                with self.assertRaisesRegex(ValueError, "inside"):
                    benchmark_mounted.validate_source(
                        mountpoint, Path("../outside.tif")
                    )

    def test_directory_selection_rejects_files_and_mount_escapes(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            mountpoint = Path(directory)
            subdir = mountpoint / "images"
            subdir.mkdir()
            (mountpoint / "image.tif").write_bytes(b"image")
            with (
                patch("os.path.ismount", return_value=True),
                patch(
                    "subprocess.check_output",
                    return_value=f"//server/share on {mountpoint} (smbfs, nodev)",
                ),
            ):
                self.assertEqual(
                    benchmark_mounted.validate_directory(mountpoint, Path("images")),
                    subdir,
                )
                with self.assertRaisesRegex(ValueError, "directory"):
                    benchmark_mounted.validate_directory(mountpoint, Path("image.tif"))
                with self.assertRaisesRegex(ValueError, "inside"):
                    benchmark_mounted.validate_directory(mountpoint, Path("../outside"))

    def test_cli_reports_each_read_and_median(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            mountpoint = Path(directory)
            source = mountpoint / "image.tif"
            source.write_bytes(b"image" * 100)
            output = StringIO()
            with (
                patch("os.path.ismount", return_value=True),
                patch(
                    "subprocess.check_output",
                    return_value=f"//server/share on {mountpoint} type cifs (rw)",
                ),
                redirect_stdout(output),
            ):
                benchmark_mounted.main(
                    [
                        "--mount",
                        str(mountpoint),
                        "--file",
                        "image.tif",
                        "--repeats",
                        "2",
                    ]
                )
            self.assertIn("Run 1:", output.getvalue())
            self.assertIn("Run 2:", output.getvalue())
            self.assertIn("Median:", output.getvalue())
            self.assertEqual(source.read_bytes(), b"image" * 100)

    def test_cli_reports_directory_listing_time_and_count(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            mountpoint = Path(directory)
            (mountpoint / "image.tif").write_bytes(b"image")
            (mountpoint / "images").mkdir()
            output = StringIO()
            with (
                patch("os.path.ismount", return_value=True),
                patch(
                    "subprocess.check_output",
                    return_value=f"//server/share on {mountpoint} type cifs (rw)",
                ),
                redirect_stdout(output),
            ):
                benchmark_mounted.main(
                    ["--mount", str(mountpoint), "--directory", ".", "--repeats", "2"]
                )
            self.assertIn("Directory:", output.getvalue())
            self.assertIn("Run 1: 2 entries", output.getvalue())
            self.assertIn("Run 2: 2 entries", output.getvalue())
            self.assertIn("Median:", output.getvalue())
            self.assertTrue((mountpoint / "image.tif").exists())

    def test_write_creates_only_a_new_directory_and_new_file(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            mountpoint = Path(directory)
            sentinel = mountpoint / "keep.txt"
            sentinel.write_text("do not change")
            with (
                patch("os.path.ismount", return_value=True),
                patch(
                    "subprocess.check_output",
                    return_value=f"//server/share on {mountpoint} (smbfs, nodev)",
                ),
            ):
                result = benchmark_mounted.benchmark_write(
                    mountpoint, size_mib=1, pattern="zeros"
                )
            run_dir, size, write_seconds, sync_seconds = result
            self.assertEqual(run_dir.parent, mountpoint)
            self.assertEqual(size, 1024 * 1024)
            self.assertGreater(write_seconds, 0)
            self.assertGreaterEqual(sync_seconds, 0)
            self.assertEqual((run_dir / "zeros.bin").read_bytes(), bytes(size))
            self.assertEqual(sentinel.read_text(), "do not change")
            self.assertEqual(
                {p.name for p in mountpoint.iterdir()}, {sentinel.name, run_dir.name}
            )

    def test_write_random_pattern_has_nonzero_content(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            mountpoint = Path(directory)
            with (
                patch("os.path.ismount", return_value=True),
                patch(
                    "subprocess.check_output",
                    return_value=f"//server/share on {mountpoint} (smbfs, nodev)",
                ),
            ):
                run_dir, size, _, _ = benchmark_mounted.benchmark_write(
                    mountpoint, size_mib=1, pattern="random"
                )
            content = (run_dir / "random.bin").read_bytes()
            self.assertEqual(len(content), size)
            self.assertNotEqual(content, bytes(size))

    def test_write_rejects_invalid_target_and_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            mountpoint = Path(directory)
            with (
                patch("os.path.ismount", return_value=False),
                self.assertRaisesRegex(ValueError, "mounted"),
            ):
                benchmark_mounted.benchmark_write(mountpoint, size_mib=1)
            with self.assertRaisesRegex(ValueError, "between"):
                benchmark_mounted.benchmark_write(mountpoint, size_mib=0)
            existing = mountpoint / "benchmark-write-collision"
            existing.mkdir()
            sentinel = existing / "keep.txt"
            sentinel.write_text("keep")
            with (
                patch("os.path.ismount", return_value=True),
                patch(
                    "subprocess.check_output",
                    return_value=f"//server/share on {mountpoint} (smbfs, nodev)",
                ),
                patch("uuid.uuid4", return_value=SimpleNamespace(hex="collision")),
                self.assertRaises(FileExistsError),
            ):
                benchmark_mounted.benchmark_write(mountpoint, size_mib=1)
            self.assertEqual(sentinel.read_text(), "keep")
            self.assertEqual({p.name for p in existing.iterdir()}, {"keep.txt"})

    def test_failed_sync_preserves_partial_file_and_reports_its_path(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            mountpoint = Path(directory)
            with (
                patch("os.path.ismount", return_value=True),
                patch(
                    "subprocess.check_output",
                    return_value=f"//server/share on {mountpoint} (smbfs, nodev)",
                ),
                patch("os.fsync", side_effect=OSError("flush failed")),
                self.assertRaisesRegex(OSError, "benchmark-write-"),
            ):
                benchmark_mounted.benchmark_write(
                    mountpoint, size_mib=1, pattern="zeros"
                )
            run_dir = next(mountpoint.iterdir())
            self.assertEqual((run_dir / "zeros.bin").stat().st_size, 1024 * 1024)

    def test_write_stops_if_mount_disappears_before_file_creation(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            mountpoint = Path(directory)
            with (
                patch("os.path.ismount", side_effect=[True, False]),
                patch(
                    "subprocess.check_output",
                    return_value=f"//server/share on {mountpoint} (smbfs, nodev)",
                ),
                self.assertRaisesRegex(OSError, "disconnected"),
            ):
                benchmark_mounted.benchmark_write(
                    mountpoint, size_mib=1, pattern="zeros"
                )
            run_dir = next(mountpoint.iterdir())
            self.assertEqual(list(run_dir.iterdir()), [])

    def test_cli_write_reports_speed_and_new_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            mountpoint = Path(directory)
            output = StringIO()
            with (
                patch("os.path.ismount", return_value=True),
                patch(
                    "subprocess.check_output",
                    return_value=f"//server/share on {mountpoint} (smbfs, nodev)",
                ),
                redirect_stdout(output),
            ):
                benchmark_mounted.main(
                    [
                        "--mount",
                        str(mountpoint),
                        "--write-mib",
                        "1",
                        "--write-pattern",
                        "zeros",
                    ]
                )
            self.assertIn("1.00 MiB", output.getvalue())
            self.assertIn("MiB/s", output.getvalue())
            self.assertIn("fsync", output.getvalue())
            self.assertEqual(len(list(mountpoint.iterdir())), 1)

    def test_directory_listing_counts_entries_without_modifying_them(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
            source = Path(directory)
            (source / "image.tif").write_bytes(b"image")
            (source / "subdir").mkdir()

            results = benchmark_mounted.benchmark_list(source, repeats=2)

            expected_names = {"image.tif", "subdir"}
            self.assertEqual(len(results), 2)
            self.assertTrue(all(count == len(expected_names) for count, _ in results))
            self.assertTrue(all(seconds > 0 for _, seconds in results))
            self.assertEqual({p.name for p in source.iterdir()}, expected_names)
            self.assertEqual((source / "image.tif").read_bytes(), b"image")
