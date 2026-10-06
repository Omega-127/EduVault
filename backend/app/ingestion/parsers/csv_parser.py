import io
from typing import Any, Dict, List
import pandas as pd


class CSVParser:
    """Parses CSV files converting each row into key-value formatted natural-language strings."""

    @staticmethod
    def parse(file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")

        results: List[Dict[str, Any]] = []

        # Replace NaN values with empty string or 'N/A'
        df = df.fillna("")

        for index, row in df.iterrows():
            row_items = []
            for col in df.columns:
                val = str(row[col]).strip()
                if val:
                    row_items.append(f"{col}: {val}")

            if row_items:
                formatted_text = " | ".join(row_items)
                results.append({
                    "text": formatted_text,
                    "page": int(index) + 1,  # Row number acts as page/entry identifier
                    "section": f"Row {index + 1}",
                })

        return results
