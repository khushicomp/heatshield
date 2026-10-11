"""Package verified frontend/dist contents with portable paths; never calls AWS."""
import argparse
import struct
from html.parser import HTMLParser
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def verify_zip_paths(filename):
    """Check both ZIP indexes: Windows tools can disagree between the two."""
    raw = Path(filename).read_bytes()
    with ZipFile(filename) as archive:
        for entry in archive.infolist():
            offset = entry.header_offset
            if raw[offset:offset + 4] != b'PK\x03\x04':
                raise ValueError('Invalid ZIP local header')
            length = struct.unpack_from('<H', raw, offset + 26)[0]
            local = raw[offset + 30:offset + 30 + length].decode('utf-8' if entry.flag_bits & 0x800 else 'cp437')
            if (local != entry.filename or '\\' in local or local.startswith('/')
                    or '..' in local.split('/')):
                raise ValueError(f'Nonportable ZIP path: local={local!r}, central={entry.filename!r}')


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' or (tag == 'link' and attrs.get('rel') == 'stylesheet'):
            ref = attrs.get('src' if tag == 'script' else 'href', '')
            if not ref.startswith('/assets/') or '..' in ref or '\\' in ref:
                raise ValueError(f'Unexpected production asset reference: {ref}')
            self.paths.append(ref.lstrip('/'))


def package_frontend(dist, output):
    dist, output = Path(dist).resolve(), Path(output).resolve()
    if output.is_relative_to(dist):
        raise ValueError('Output ZIP must be outside dist')
    index = dist / 'index.html'
    parser = Assets()
    parser.feed(index.read_text(encoding='utf-8'))
    if not any(p.endswith('.js') for p in parser.paths) or not any(p.endswith('.css') for p in parser.paths):
        raise ValueError('Missing JS/CSS references')
    for ref in parser.paths:
        if not (dist / ref).is_file() or not (dist / ref).stat().st_size:
            raise ValueError(f'Missing or empty referenced asset: {ref}')
    files = sorted(p for p in dist.rglob('*') if p.is_file())
    for p in files:
        if p.is_symlink() or not p.resolve().is_relative_to(dist):
            raise ValueError('Symlinks/external files are not deployment artifacts')
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
        for p in files:
            archive.writestr(p.relative_to(dist).as_posix(), p.read_bytes())
    with ZipFile(output) as archive:
        if set(archive.namelist()) != {p.relative_to(dist).as_posix() for p in files}:
            raise ValueError('ZIP inventory does not match dist')
        for p in files:
            if archive.read(p.relative_to(dist).as_posix()) != p.read_bytes():
                raise ValueError('ZIP bytes do not match dist')
    verify_zip_paths(output)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist', type=Path, default=ROOT / 'frontend/dist')
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/heatshield-frontend.zip')
    args = parser.parse_args()
    print(f'Verified deployment ZIP: {package_frontend(args.dist, args.output)}')
