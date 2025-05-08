import re

def extract_project_data(text: str) -> dict:
    # Puedes usar regex o un modelo más avanzado
    name_match = re.search(r"llame\s+(.*?)\s*(,|\.)", text)
    desc_match = re.search(r"descripcion\s+es\s+(.*)", text)

    return {
        "nombre": name_match.group(1) if name_match else "Sin nombre",
        "descripcion": desc_match.group(1) if desc_match else "Sin descripción"
    }