from pathlib import Path
import yaml

from core.log.voice import info, err


# Mapping from on-disk filenames to logical keys
METADATA_FILES = {
    "builder.yaml": "builder",
    "installer.yaml": "installer",
    "policy.yaml": "policy",
}


class MetadataError(SystemExit):
    """Raised when metadata cannot be loaded cleanly."""
    pass


class PackageMetadata:
    """
    Loads metadata for a single package.

    Responsibilities:
      - Ensure required metadata files exist
      - Parse YAML safely
      - Return a structured dictionary keyed by role

    Explicitly does NOT:
      - Validate schemas
      - Interpret semantics
      - Execute commands
    """

    def __init__(self, metadata_dir: Path):
        self.metadata_dir = Path(metadata_dir)
        self.data: dict[str, dict] = {}

    def load(self) -> dict:
        info(f"Reviewing package metadata at {self.metadata_dir}")

        if not self.metadata_dir.exists():
            err(f"Metadata directory does not exist: {self.metadata_dir}")
            raise MetadataError(1)

        if not self.metadata_dir.is_dir():
            err(f"Metadata path is not a directory: {self.metadata_dir}")
            raise MetadataError(1)

        for filename, key in METADATA_FILES.items():
            path = self.metadata_dir / filename

            if not path.exists():
                err(f"Required metadata file is missing: {path}")
                raise MetadataError(1)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
            except Exception as e:
                err(f"Failed to read {path}: {e}")
                raise MetadataError(1)

            # Empty YAML is permitted; treat as empty mapping
            if content is None:
                content = {}

            if not isinstance(content, dict):
                err(f"Metadata file {path} must contain a YAML mapping")
                raise MetadataError(1)

            self.data[key] = content

        info("All package metadata files loaded successfully")
        return self.data
