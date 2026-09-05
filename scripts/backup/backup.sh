#!/usr/bin/env bash
# scripts/backup/backup.sh
# Cria backup consistente do PostgreSQL do Estética Manager
# Formato: custom (-Fc) comprimido com integridade SHA256

set -euo pipefail

DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5434/estetica}"
BACKUP_DIR="${BACKUP_DIR:-$(pwd)/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

mkdir -p "${BACKUP_DIR}"

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_NAME="estetica_backup_${TIMESTAMP}.dump"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
SHA_PATH="${BACKUP_PATH}.sha256"

echo "=== [Estética Manager] Iniciando Backup ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Destino:   ${BACKUP_PATH}"

# Dump com formato customizado (-Fc), excluindo owner/privileges específicos para portabilidade
pg_dump \
  --format=c \
  --no-owner \
  --no-privileges \
  --file="${BACKUP_PATH}" \
  "${DATABASE_URL}"

# Gerar checksum SHA256 para garantia de integridade (§Dado de Saúde)
(cd "${BACKUP_DIR}" && sha256sum "${BACKUP_NAME}" > "${BACKUP_NAME}.sha256")

BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
echo "=== Backup concluído com sucesso! ==="
echo "Arquivo:  ${BACKUP_NAME} (${BACKUP_SIZE})"
echo "Checksum: $(cat "${SHA_PATH}")"

# Limpeza de retenção (remover dumps com mais de RETENTION_DAYS dias)
if [ "${RETENTION_DAYS}" -gt 0 ]; then
  find "${BACKUP_DIR}" -name "estetica_backup_*.dump*" -mtime "+${RETENTION_DAYS}" -exec rm -f {} + 2>/dev/null || true
fi
