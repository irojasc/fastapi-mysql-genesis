from collections import defaultdict
import secrets
import string
import re

def get_all_publishers(value):
    index, data = value
    return {
        "index": index,
        "publisher": data[0]
    }

def get_all_pair_company_publishers(data):
    result = defaultdict(list)
    for item in data:
        key = item[1]
        value = item[0]
        result[key].append(value)
    return (dict(result))

def generate_filename(
        numero: int,
        extension: str,
        valor_inicial: str | None = None
    ) -> str:
    extension = extension.lstrip('.')  # asegura "webp" y no ".webp"

    # --- Caso 1: no existe valor inicial ---
    if not valor_inicial:
        chars = string.ascii_letters + string.digits
        random_part = ''.join(secrets.choice(chars) for _ in range(8))
        return f"gn_{random_part}_{numero}.{extension}"

    # --- Caso 2: existe valor inicial ---
    base_name = valor_inicial.rsplit('.', 1)[0]  # sin extensión

    # Detectar versión
    match = re.search(r'_v(\d+)$', base_name)

    if match:
        version = int(match.group(1)) + 1
        base_name = re.sub(r'_v\d+$', f'_v{version}', base_name)
    else:
        base_name = f"{base_name}_v1"

    return f"{base_name}.{extension}"