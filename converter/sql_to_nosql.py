# converter/sql_to_nosql.py
import re
from collections import defaultdict
from typing import List, Dict, Any, Optional

def parse_sql_inserts(sql_text: str) -> List[Dict[str, str]]:
    """Parse SQL INSERT statements into list of dicts."""
    pattern = r"INSERT\s+INTO\s+\w+\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\);"
    matches = re.findall(pattern, sql_text, re.IGNORECASE | re.MULTILINE)
    data = []
    for cols, vals in matches:
        col_list = [c.strip() for c in cols.split(",")]
        # Handle quoted and unquoted values
        val_list = []
        for v in vals.split(","):
            v_clean = v.strip()
            # Remove surrounding quotes if present
            if (v_clean.startswith("'") and v_clean.endswith("'")) or \
               (v_clean.startswith('"') and v_clean.endswith('"')):
                v_clean = v_clean[1:-1]
            val_list.append(v_clean)
        data.append(dict(zip(col_list, val_list)))
    return data

def sql_to_nosql(
    sql_data: List[Dict[str, str]], 
    group_key: Optional[str] = None, 
    nest_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convert flat SQL rows to nested NoSQL (JSON).
    If group_key and nest_key provided, groups child records under parent.
    """
    if not group_key or not nest_key:
        return sql_data  # Flat output

    # Group child records by group_key
    children = defaultdict(list)
    parents = {}

    for row in sql_data:
        if group_key in row:
            if nest_key in row:
                # Likely a child record (has both keys)
                children[row[group_key]].append(row)
            else:
                # Likely a parent record (has group_key but not nest_key)
                pid = row[group_key]
                parents[pid] = row.copy()
                # Reserve space for children
                parents[pid]["items"] = []

    # Attach children to parents
    for pid, child_list in children.items():
        if pid in parents:
            parents[pid]["items"].extend(child_list)
        else:
            # Orphaned children → treat as standalone
            for child in child_list:
                sql_data.append(child)

    return list(parents.values()) if parents else sql_data