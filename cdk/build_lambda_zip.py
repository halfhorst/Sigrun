import zipfile

from pathlib import Path

import loguru
from loguru import logger


def main():
    site_packages = Path(loguru.__file__).resolve().parents[1]
    package_root = Path(__file__).resolve().parents[1]
    handler_source = package_root / "lambda" / "handler.py"
    sigrun_source = package_root / "sigrun"
    zipf = zipfile.ZipFile(package_root / "sigrun.zip", mode="w")

    logger.info("Constructing a zip archive out of sigrun source "
                "code and its dependencies. Using loguru to "
                "determine dependency location.")
    logger.info(f"Site packages are located at {site_packages}.")
    logger.info(f"Sigrun source code is located at {sigrun_source}.")

    for path in site_packages.rglob("*"):
        if path.is_file():
            zipf.write(path, arcname=path.relative_to(site_packages))

    for path in sigrun_source.glob("*"):
        if path.is_file():
            zipf.write(path, arcname=path.relative_to(package_root))

    zipf.write(handler_source, arcname="handler.py")

    zipf.close()
    logger.info(f"Created zip archive at {zipfile.Path(zipf)}")

if __name__=="__main__":
    main()
