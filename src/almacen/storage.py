from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

APP_DIR_NAME = "AlmacenInformatico"
APP_FILE_NAME = "inventory.json"
WITHDRAWAL_LOG_FILE_NAME = "withdrawal_logs.json"
FIXED_PALLETS = [str(number) for number in range(1, 11)]

DEFAULT_DATA: dict[str, Any] = {
    "meta": {
        "name": "Inventario almacen informatico",
        "version": 1,
        "last_updated": "2026-04-08T10:00:00Z",
    },
    "equipment_types": [],
    "pallets": [
        {"pale": "1", "items": []},
        {"pale": "2", "items": []},
        {"pale": "3", "items": []},
        {"pale": "4", "items": []},
        {"pale": "5", "items": []},
        {"pale": "6", "items": []},
        {"pale": "7", "items": []},
        {"pale": "8", "items": []},
        {"pale": "9", "items": []},
        {"pale": "10", "items": []},
    ],
}

DEFAULT_WITHDRAWAL_LOGS: dict[str, Any] = {
    "meta": {
        "name": "Registro de retiradas almacen informatico",
        "version": 1,
        "last_updated": "2026-04-08T10:00:00Z",
    },
    "withdrawals": [],
}


def get_project_default_data_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "default_inventory.json"


def get_user_data_dir() -> Path:
    app_data = Path.home() / "AppData" / "Local"
    return app_data / APP_DIR_NAME


def get_user_inventory_path() -> Path:
    return get_user_data_dir() / APP_FILE_NAME


def get_user_withdrawal_log_path() -> Path:
    return get_user_data_dir() / WITHDRAWAL_LOG_FILE_NAME


def ensure_inventory_file() -> Path:
    user_path = get_user_inventory_path()
    default_path = get_project_default_data_path()
    user_path.parent.mkdir(parents=True, exist_ok=True)

    if not default_path.exists():
        default_path.parent.mkdir(parents=True, exist_ok=True)
        default_path.write_text(
            json.dumps(DEFAULT_DATA, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    if not user_path.exists():
        shutil.copyfile(default_path, user_path)

    return user_path


def ensure_withdrawal_log_file() -> Path:
    log_path = get_user_withdrawal_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if not log_path.exists():
        log_path.write_text(
            json.dumps(DEFAULT_WITHDRAWAL_LOGS, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return log_path


def load_inventory() -> dict[str, Any]:
    file_path = ensure_inventory_file()
    raw_data = json.loads(file_path.read_text(encoding="utf-8"))
    normalized_data = normalize_inventory(raw_data)
    if normalized_data != raw_data:
        save_inventory(normalized_data)
    return normalized_data


def load_withdrawal_logs() -> dict[str, Any]:
    file_path = ensure_withdrawal_log_file()
    raw_data = json.loads(file_path.read_text(encoding="utf-8"))
    normalized_data = normalize_withdrawal_logs(raw_data)
    if normalized_data != raw_data:
        save_withdrawal_logs(normalized_data)
    return normalized_data


def save_inventory(data: dict[str, Any]) -> None:
    file_path = ensure_inventory_file()
    file_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_withdrawal_logs(data: dict[str, Any]) -> None:
    file_path = ensure_withdrawal_log_file()
    file_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def create_default_data_file() -> None:
    default_path = get_project_default_data_path()
    default_path.parent.mkdir(parents=True, exist_ok=True)
    default_path.write_text(
        json.dumps(deepcopy(DEFAULT_DATA), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def next_equipment_id(data: dict[str, Any]) -> str:
    current_numbers = []

    for item in data.get("equipment_types", []):
        item_id = str(item.get("id", ""))
        if not item_id.startswith("EQ-"):
            continue
        try:
            current_numbers.append(int(item_id.split("-", maxsplit=1)[1]))
        except ValueError:
            continue

    return f"EQ-{(max(current_numbers, default=0) + 1):04d}"


def normalize_inventory(data: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(data)
    normalized.setdefault("meta", deepcopy(DEFAULT_DATA["meta"]))

    if "equipment_types" not in normalized and "items" in normalized:
        equipment_types = []
        pallets_map: dict[str, list[dict[str, Any]]] = {}

        for item in normalized.get("items", []):
            equipment_types.append(
                {
                    "id": item.get("id", next_equipment_id({"equipment_types": equipment_types})),
                    "categoria": item.get("categoria", ""),
                    "marca": item.get("marca", ""),
                    "modelo": item.get("modelo", ""),
                    "observaciones": item.get("observaciones", ""),
                }
            )

            pale = str(item.get("ubicacion", "")).strip()
            cantidad = int(item.get("cantidad", 0) or 0)
            if pale and cantidad > 0:
                pallets_map.setdefault(pale, []).append(
                    {
                        "equipment_id": equipment_types[-1]["id"],
                        "cantidad": cantidad,
                    }
                )

        normalized["equipment_types"] = equipment_types
        normalized["pallets"] = [
            {"pale": pale, "items": items} for pale, items in pallets_map.items()
        ]
        normalized.pop("items", None)

    normalized.setdefault("equipment_types", [])
    normalized["pallets"] = normalize_pallets(normalized.get("pallets", []))
    return normalized


def normalize_withdrawal_logs(data: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(data)
    normalized.setdefault("meta", deepcopy(DEFAULT_WITHDRAWAL_LOGS["meta"]))
    normalized.setdefault("withdrawals", [])

    cleaned_withdrawals: list[dict[str, Any]] = []
    for entry in normalized["withdrawals"]:
        if not isinstance(entry, dict):
            continue

        cleaned_withdrawals.append(
            {
                "timestamp": str(entry.get("timestamp", "")).strip(),
                "date": str(entry.get("date", "")).strip(),
                "equipment_id": str(entry.get("equipment_id", "")).strip(),
                "categoria": str(entry.get("categoria", "")).strip(),
                "marca": str(entry.get("marca", "")).strip(),
                "modelo": str(entry.get("modelo", "")).strip(),
                "pale": str(entry.get("pale", "")).strip(),
                "cantidad": int(entry.get("cantidad", 0) or 0),
                "quien_retira": str(entry.get("quien_retira", "")).strip(),
                "motivo_retirada": str(entry.get("motivo_retirada", "")).strip(),
            }
        )

    normalized["withdrawals"] = cleaned_withdrawals
    return normalized


def normalize_pallets(pallets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pallet_map: dict[str, list[dict[str, Any]]] = {pale: [] for pale in FIXED_PALLETS}
    next_available_index = 0

    for pallet in pallets:
        raw_name = str(pallet.get("pale", "")).strip()
        raw_items = list(pallet.get("items", []))

        if raw_name in pallet_map:
            target_name = raw_name
        else:
            while (
                next_available_index < len(FIXED_PALLETS)
                and pallet_map[FIXED_PALLETS[next_available_index]]
            ):
                next_available_index += 1

            if next_available_index >= len(FIXED_PALLETS):
                continue
            target_name = FIXED_PALLETS[next_available_index]

        target_items = pallet_map[target_name]

        for raw_item in raw_items:
            equipment_id = str(raw_item.get("equipment_id", "")).strip()
            cantidad = int(raw_item.get("cantidad", 0) or 0)
            if not equipment_id or cantidad <= 0:
                continue

            for existing_item in target_items:
                if existing_item["equipment_id"] == equipment_id:
                    existing_item["cantidad"] += cantidad
                    break
            else:
                target_items.append(
                    {
                        "equipment_id": equipment_id,
                        "cantidad": cantidad,
                    }
                )

    return [{"pale": pale, "items": items} for pale, items in pallet_map.items()]
