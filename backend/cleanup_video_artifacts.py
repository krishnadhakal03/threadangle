from __future__ import annotations

import argparse

from utils.video_artifacts import cleanup_old_video_artifacts, generated_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete old Threadangle generated-video artifacts safely.")
    parser.add_argument(
        "--completed-hours",
        type=int,
        default=None,
        help="Delete completed run folders older than this many hours. Defaults to VIDEO_COMPLETED_ARTIFACT_EXPIRY_HOURS or 72.",
    )
    parser.add_argument(
        "--failed-temp-hours",
        type=int,
        default=None,
        help="Delete raw/temp/cache artifacts older than this many hours. Defaults to VIDEO_TEMP_ARTIFACT_EXPIRY_HOURS or 24.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print candidates without deleting them.")
    args = parser.parse_args()

    report = cleanup_old_video_artifacts(
        completed_hours=args.completed_hours,
        failed_temp_hours=args.failed_temp_hours,
        dry_run=args.dry_run,
    )

    mode = "DRY RUN" if args.dry_run else "DELETE"
    print(f"[{mode}] Threadangle generated root: {generated_root()}")
    print(f"Deleted files: {len(report.files_deleted)}")
    for path in report.files_deleted:
        print(f"  file {path}")
    print(f"Deleted directories: {len(report.dirs_deleted)}")
    for path in report.dirs_deleted:
        print(f"  dir  {path}")
    if report.skipped:
        print(f"Skipped: {len(report.skipped)}")
        for item in report.skipped:
            print(f"  {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
