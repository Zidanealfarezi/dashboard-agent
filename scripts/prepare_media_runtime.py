"""Reuse the existing Android Studio FFmpeg runtime locally; no download or global install."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/Applications/Android Studio.app/Contents/plugins/android/lib/ffmpeg-7.1.1-1.5.12-macosx-arm64.jar')
DEST = ROOT / 'tools/ffmpeg-runtime'


def main():
    if not SOURCE.is_file():
        raise SystemExit('Existing Android Studio FFmpeg jar not found; no installation attempted')
    DEST.mkdir(parents=True, exist_ok=True)
    prefix = 'org/bytedeco/ffmpeg/macosx-arm64/'
    with zipfile.ZipFile(SOURCE) as archive:
        for name in archive.namelist():
            if not name.startswith(prefix) or name.endswith('/'):
                continue
            label = name[len(prefix):]
            if '/' in label or (label not in ('ffmpeg', 'ffprobe') and not label.endswith('.dylib')):
                continue
            target = DEST / label
            data = archive.read(name)
            if target.exists() and target.read_bytes() != data:
                raise SystemExit('Runtime differs; inspect it before replacement')
            if not target.exists():
                target.write_bytes(data)
            target.chmod(0o755)
    version = subprocess.run([str(DEST / 'ffmpeg'), '-version'], check=True,
                             capture_output=True, text=True).stdout.splitlines()[0]
    digest = hashlib.sha256()
    with SOURCE.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    report = {'source': str(SOURCE), 'source_sha256': digest.hexdigest(),
              'version': version, 'downloaded': False, 'global_path_changed': False,
              'scope': 'local runtime reuse from installed Android Studio'}
    (DEST / 'SOURCE.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
