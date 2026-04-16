from __future__ import annotations

import hashlib
import shutil
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable
import xml.etree.ElementTree as ET


ASSEMBLEE_NS = "http://schemas.assemblee-nationale.fr/referentiel"
EXPECTED_ROOT_TAG = f"{{{ASSEMBLEE_NS}}}compteRendu"


@dataclass(frozen=True)
class SessionXmlMetadata:
    source_file: str
    seance_id: str
    seance_date: str
    seance_date_label: str
    local_path: str


@dataclass(frozen=True)
class ImportResult:
    source_file: str
    destination_path: str
    content_hash: str
    metadata: SessionXmlMetadata
    status: str


@dataclass(frozen=True)
class DownloadResult:
    source_url: str
    destination_path: str
    content_hash: str
    bytes_written: int
    status: str


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_zip_archive(
    source_url: str,
    destination_path: Path,
    *,
    fetcher: Callable[[str], bytes] | None = None,
    overwrite: bool = True,
) -> DownloadResult:
    payload = fetcher(source_url) if fetcher is not None else _fetch_url_bytes(source_url)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        dir=destination_path.parent,
        prefix=f".{destination_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
        temporary_file.write(payload)

    try:
        _validate_zip_archive(temporary_path)
        downloaded_hash = file_sha256(temporary_path)
        bytes_written = temporary_path.stat().st_size

        if destination_path.exists():
            existing_hash = file_sha256(destination_path)
            if existing_hash == downloaded_hash:
                temporary_path.unlink()
                return DownloadResult(
                    source_url=source_url,
                    destination_path=str(destination_path),
                    content_hash=existing_hash,
                    bytes_written=destination_path.stat().st_size,
                    status="unchanged",
                )
            if not overwrite:
                raise FileExistsError(
                    f"Archive existante differente : {destination_path}. "
                    "Utiliser overwrite=True pour la remplacer."
                )
            status = "updated"
        else:
            status = "downloaded"

        temporary_path.replace(destination_path)
        return DownloadResult(
            source_url=source_url,
            destination_path=str(destination_path),
            content_hash=downloaded_hash,
            bytes_written=bytes_written,
            status=status,
        )
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise


def validate_session_xml(path: Path) -> SessionXmlMetadata:
    return read_session_xml_metadata(path)


def read_session_xml_metadata(path: Path) -> SessionXmlMetadata:
    seance_id = ""
    raw_date = ""
    seance_date_label = ""
    has_contenu = False
    root_checked = False

    try:
        for event, element in ET.iterparse(path, events=("start", "end")):
            if event == "start" and not root_checked:
                root_checked = True
                if element.tag != EXPECTED_ROOT_TAG:
                    raise ValueError(f"Format compte rendu Assemblee inattendu dans {path}.")
                continue

            if event != "end":
                continue

            tag = _local_name(element.tag)
            text = "".join(element.itertext()).strip()

            if tag == "uid" and not seance_id:
                seance_id = text
            elif tag == "dateSeance" and not raw_date:
                raw_date = text
            elif tag == "dateSeanceJour" and not seance_date_label:
                seance_date_label = text
            elif tag == "contenu":
                has_contenu = True

            element.clear()
    except ET.ParseError as exc:
        raise ValueError(f"XML compte rendu non parseable : {path}") from exc

    if not root_checked:
        raise ValueError(f"XML vide ou illisible : {path}.")
    if not seance_id:
        raise ValueError(f"UID introuvable dans {path}.")
    if not raw_date:
        raise ValueError(f"dateSeance introuvable dans {path}.")
    if not seance_date_label:
        raise ValueError(f"Libelle dateSeanceJour introuvable dans {path}.")
    if not has_contenu:
        raise ValueError(f"Bloc contenu introuvable dans {path}.")

    return SessionXmlMetadata(
        source_file=path.name,
        seance_id=seance_id,
        seance_date=_normalize_syceron_date(raw_date, path),
        seance_date_label=seance_date_label,
        local_path=str(path),
    )


def import_session_xml(
    source_path: Path,
    destination_dir: Path,
    *,
    overwrite: bool = False,
) -> ImportResult:
    source_metadata = validate_session_xml(source_path)
    source_hash = file_sha256(source_path)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / source_path.name

    if destination_path.exists():
        destination_hash = file_sha256(destination_path)
        if destination_hash == source_hash:
            return ImportResult(
                source_file=source_path.name,
                destination_path=str(destination_path),
                content_hash=source_hash,
                metadata=validate_session_xml(destination_path),
                status="already_exists",
            )

        if not overwrite:
            raise FileExistsError(
                f"Conflit d'import : {destination_path.name} existe deja avec un contenu different."
            )

        status = "overwritten"
    else:
        status = "imported"

    shutil.copy2(source_path, destination_path)
    destination_metadata = validate_session_xml(destination_path)
    return ImportResult(
        source_file=source_metadata.source_file,
        destination_path=str(destination_path),
        content_hash=file_sha256(destination_path),
        metadata=destination_metadata,
        status=status,
    )


def list_session_xmls_in_zip(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as archive:
        names = {
            Path(member.filename).name
            for member in archive.infolist()
            if not member.is_dir() and Path(member.filename).name.endswith(".xml")
        }
    return sorted(names)


def extract_session_xml_from_zip(
    zip_path: Path,
    source_file: str,
    destination_dir: Path,
    *,
    overwrite: bool = False,
) -> ImportResult:
    with zipfile.ZipFile(zip_path) as archive:
        member_name = _find_zip_member(archive, source_file)
        payload = archive.read(member_name)

    with tempfile.TemporaryDirectory() as tmp_dir:
        temporary_path = Path(tmp_dir) / Path(source_file).name
        temporary_path.write_bytes(payload)
        return import_session_xml(temporary_path, destination_dir, overwrite=overwrite)


def _find_zip_member(archive: zipfile.ZipFile, source_file: str) -> str:
    direct_matches = [
        member.filename
        for member in archive.infolist()
        if not member.is_dir() and member.filename == source_file
    ]
    if len(direct_matches) == 1:
        return direct_matches[0]

    basename = Path(source_file).name
    basename_matches = [
        member.filename
        for member in archive.infolist()
        if not member.is_dir() and Path(member.filename).name == basename
    ]
    if len(basename_matches) == 1:
        return basename_matches[0]
    if not basename_matches:
        raise FileNotFoundError(f"{source_file} introuvable dans l'archive.")
    raise ValueError(f"Nom XML ambigu dans l'archive : {source_file}.")


def _fetch_url_bytes(source_url: str) -> bytes:
    request = urllib.request.Request(source_url, headers={"User-Agent": "OBSERVATOIRE/phase-f"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def _validate_zip_archive(path: Path) -> None:
    if not zipfile.is_zipfile(path):
        raise ValueError(f"Archive ZIP invalide : {path}")
    with zipfile.ZipFile(path) as archive:
        corrupt_member = archive.testzip()
    if corrupt_member is not None:
        raise ValueError(f"Archive ZIP corrompue : {corrupt_member}")


def _local_name(tag: str) -> str:
    return tag.split("}")[-1]


def _normalize_syceron_date(raw_date: str, path: Path) -> str:
    if len(raw_date) < 8 or not raw_date[:8].isdigit():
        raise ValueError(f"dateSeance invalide dans {path} : {raw_date}")
    return date(
        int(raw_date[0:4]),
        int(raw_date[4:6]),
        int(raw_date[6:8]),
    ).isoformat()
