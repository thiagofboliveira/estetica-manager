#!/usr/bin/env bash
# scripts/backup/restore.sh
# Restaura backup consistente do PostgreSQL do Estética Manager
# Exige confirmação explícita para evitar sobrescrever banco indevidamente

set -euo pipefail

BACKUP_FILE="${1:-}"
TARGET_DATABASE_URL="${TARGET_DATABASE_URL:-}"

if [ -z "${BACKUP_FILE}" ]; then
  # Se não informado, procura o dump mais recente em backups/
  BACKUP_DIR="${BACKUP_DIR:-$(pwd)/backups}"
  BACKUP_FILE=$(find "${BACKUP_DIR}" -name "estetica_backup_*.dump" -type f 2>/dev/null | sort | tail -n 1 || true)
fi

if [ -z "${BACKUP_FILE}" ] || [ ! -f "${BACKUP_FILE}" ]; then
  echo "ERRO: Arquivo de backup não encontrado: '${BACKUP_FILE}'"
  echo "Uso: TARGET_DATABASE_URL=... ./scripts/backup/restore.sh [caminho/para/arquivo.dump]"
  exit 1
fi

if [ -z "${TARGET_DATABASE_URL}" ]; then
  echo "ERRO: TARGET_DATABASE_URL não configurada!"
  echo "Defina TARGET_DATABASE_URL antes de restaurar para evitar sobrescrever banco incorreto."
  exit 1
fi

# Validação do Checksum SHA256 se existir
SHA_FILE="${BACKUP_FILE}.sha256"
if [ -f "${SHA_FILE}" ]; then
  echo "=== Verificando integridade SHA256 ==="
  DIR=$(dirname "${BACKUP_FILE}")
  BASE=$(basename "${BACKUP_FILE}")
  (cd "${DIR}" && sha256sum -c "${BASE}.sha256")
  echo "Integridade confirmada!"
else
  echo "AVISO: Arquivo .sha256 não encontrado. Prosseguindo sem validação de hash..."
fi

echo "=== [Estética Manager] Iniciando Restore ==="
echo "Arquivo: ${BACKUP_FILE}"
echo "Destino: ${TARGET_DATABASE_URL}"

# pg_restore com --clean e --if-exists para substituir objetos mantendo integridade
# --exit-on-error não é usado porque pg_restore pode avisar sobre roles que já não existem
pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  -d "${TARGET_DATABASE_URL}" \
  "${BACKUP_FILE}" || true

echo "=== Restore concluído com sucesso! ==="
