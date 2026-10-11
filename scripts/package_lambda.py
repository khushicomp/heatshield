"""Create a minimal deterministic deployment ZIP; never contacts AWS."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    '__init__.py', 'contracts.py', 'thermal.py', 'interventions.py',
    'optimization.py', 'scenarios.py', 'presets.py', 'api/__init__.py',
    'api/allocations.py', 'api/lambda_handler.py',
)


def package(destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for module in MODULES:
            name = 'heatshield/' + module
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (ROOT / name).read_bytes())
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/heatshield-lambda.zip')
    args = parser.parse_args()
    path = package(args.output)
    print(f'Packaged {len(MODULES)} allowlisted Python modules: {path} ({path.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
