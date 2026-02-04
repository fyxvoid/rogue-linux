from jsonschema import validate, ValidationError
from pathlib import Path
import yaml

from core.log.voice import info, ok, err


# Logical metadata sections → schema paths
SCHEMA_MAP = {
    "builder": "metadata/schemas/builder.schema.yaml",
    "installer": "metadata/schemas/installer.schema.yaml",
    "policy": "metadata/schemas/policy.schema.yaml",
    # "identity" intentionally not enforced yet
}


class VerificationError(SystemExit):
    """
    Raised when metadata verification fails.
    """
    pass


def load_schema(path: str) -> dict:
    schema_path = Path(path)

    if not schema_path.exists():
        err(f"Schema file missing: {schema_path}")
        raise VerificationError(1)

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        err(f"Failed to read schema file {schema_path}: {e}")
        raise VerificationError(1)

    if not isinstance(schema, dict):
        err(f"Schema file is invalid or empty: {schema_path}")
        raise VerificationError(1)

    return schema


def verify(metadata: dict):
    """
    Perform strict metadata verification.

    Responsibilities:
      - Ensure required metadata sections exist
      - Validate each section against its schema

    Explicitly does NOT:
      - Resolve dependencies
      - Infer build order
      - Execute commands
    """

    info("Conducting a thorough inspection of package metadata")

    for key, schema_path in SCHEMA_MAP.items():
        schema = load_schema(schema_path)
        data = metadata.get(key)

        if data is None:
            err(f"Missing required metadata file: {key}.yaml")
            raise VerificationError(1)

        try:
            validate(instance=data, schema=schema)
            ok(f"{key}.yaml is structurally sound")
        except ValidationError as e:
            err(f"{key}.yaml schema violation — {e.message}")
            raise VerificationError(1)

    ok("All metadata verification checks have passed cleanly")
