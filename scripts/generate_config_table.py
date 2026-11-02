"""Generate markdown configuration tables from Pydantic config models."""

from __future__ import annotations

from sitesentry.config import ApiConfig, ScanConfig


def generate_scan_config_table() -> str:
    lines = [
        "| Field | Type | Default | Description |",
        "|---|---|---|---|",
    ]
    for name, field in ScanConfig.model_fields.items():
        type_name = getattr(field.annotation, "__name__", str(field.annotation))
        default_val = field.default
        if default_val is not None:
            default_str = f"`{default_val}`"
        else:
            default_str = "*none*"
        desc = field.description or ""
        lines.append(f"| `{name}` | `{type_name}` | {default_str} | {desc} |")
    return "\n".join(lines)


def generate_api_config_table() -> str:
    lines = [
        "| Field | Type | Default | Description |",
        "|---|---|---|---|",
    ]
    for name, field in ApiConfig.model_fields.items():
        type_name = getattr(field.annotation, "__name__", str(field.annotation))
        default_val = field.default
        if default_val is not None:
            default_str = f"`{default_val}`"
        else:
            default_str = "*none*"
        desc = field.description or ""
        lines.append(f"| `{name}` | `{type_name}` | {default_str} | {desc} |")
    return "\n".join(lines)


if __name__ == "__main__":
    print("### Scan Configuration (`ScanConfig`)\n")
    print(generate_scan_config_table())
    print("\n### API Configuration (`ApiConfig`)\n")
    print(generate_api_config_table())
