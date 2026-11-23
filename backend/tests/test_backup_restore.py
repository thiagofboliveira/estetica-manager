"""Teste automatizado de Backup e Restore (G-07).
Verifica a integridade do script de backup/restore e a preservação
de dados e RLS no PostgreSQL.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
BACKUP_SCRIPT = REPO_ROOT / "scripts" / "backup" / "backup.sh"
RESTORE_SCRIPT = REPO_ROOT / "scripts" / "backup" / "restore.sh"
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "backup" / "verify_backup_restore.sh"


@pytest.mark.skipif(
    not (
        shutil.which("pg_dump") and shutil.which("pg_restore") and shutil.which("psql")
    ),
    reason="Ferramentas do PostgreSQL (pg_dump, pg_restore, psql) não instaladas no ambiente",
)
def test_backup_restore_scripts_exist_and_executable():
    assert BACKUP_SCRIPT.is_file(), "backup.sh deve existir"
    assert RESTORE_SCRIPT.is_file(), "restore.sh deve existir"
    assert VERIFY_SCRIPT.is_file(), "verify_backup_restore.sh deve existir"
    assert os.access(BACKUP_SCRIPT, os.X_OK), "backup.sh deve ser executável"
    assert os.access(RESTORE_SCRIPT, os.X_OK), "restore.sh deve ser executável"
    assert os.access(VERIFY_SCRIPT, os.X_OK), (
        "verify_backup_restore.sh deve ser executável"
    )


@pytest.mark.skipif(
    not (
        shutil.which("pg_dump") and shutil.which("pg_restore") and shutil.which("psql")
    ),
    reason="Ferramentas do PostgreSQL não instaladas",
)
def test_verify_backup_restore_execution():
    """Executa a verificação completa de backup e restore contra o Postgres."""
    # O script precisa de uma URL libpq (sem "+psycopg2") e de um papel que
    # possa CRIAR banco: usa a URL do owner (a mesma das migrações). Antes ele
    # herdava a URL da aplicação (role sem CREATEDB, com sufixo de driver) ou
    # caía no default fixo da porta 5434/5432.
    env = dict(os.environ)
    owner_url = os.environ.get("DATABASE_URL_MIGRATIONS") or os.environ.get(
        "DATABASE_URL"
    )
    if owner_url:
        env["DATABASE_URL"] = owner_url.replace("postgresql+psycopg2://", "postgresql://")
    result = subprocess.run(
        [str(VERIFY_SCRIPT)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"Falha na verificação de backup/restore:\n{result.stderr}\n{result.stdout}"
    )
    assert "EVIDÊNCIA G-07: Restore testado e validado com sucesso!" in result.stdout
    assert "RLS ativo nas tabelas restauradas" in result.stdout
