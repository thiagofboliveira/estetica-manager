import re
from uuid import UUID


def generate_slug(name: str, id_val: UUID | str) -> str:
    """Gera um slug URL-friendly a partir do nome e ID do profissional."""
    clean = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not clean:
        clean = "agenda"
    short_id = str(id_val).replace("-", "")[:6]
    return f"{clean}-{short_id}"
