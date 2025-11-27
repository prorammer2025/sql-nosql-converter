# converter/nosql_to_sql.py
import json
from typing import List, Dict, Any

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict[str, str]:
    """Recursively flatten a nested dict."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}{sep}{i}", sep=sep).items())
                else:
                    items.append((f"{new_key}{sep}{i}", str(item)))
        else:
            items.append((new_key, str(v)))
    return dict(items)

def nosql_to_sql(json_data: List[Dict], table_name: str = "data") -> str:
    """Convert list of JSON docs → SQL CREATE + INSERT statements."""
    if not json_data:
        return "-- No data to convert"

    # Flatten all documents to determine full schema
    flattened_docs = [flatten_dict(doc) for doc in json_data]
    all_columns = sorted({col for doc in flattened_docs for col in doc.keys()})

    # Build CREATE TABLE
    lines = [
        f"-- Generated from NoSQL JSON (flattened)",
        f"DROP TABLE IF EXISTS {table_name};",
        f"CREATE TABLE {table_name} ("
    ]
    lines.extend([f"  `{col}` TEXT" for col in all_columns])
    lines[-1] += ");\n"

    # Build INSERTs
    for doc in flattened_docs:
        values = []
        for col in all_columns:
            val = doc.get(col, 'NULL')
            # Escape single quotes
            safe_val = val.replace("'", "''") if isinstance(val, str) else str(val)
            values.append(f"'{safe_val}'" if val != 'NULL' else "NULL")
        lines.append(
            f"INSERT INTO {table_name} ({', '.join(f'`{c}`' for c in all_columns)}) "
            f"VALUES ({', '.join(values)});"
        )

    return "\n".join(lines)