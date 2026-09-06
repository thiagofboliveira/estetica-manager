"""Cliente da Admin API do Supabase Auth — ÚNICO lugar do backend que
toca a service_role key (B-01, docs/pending/BACKLOG_GO_LIVE.md).

Por que isto existe: User (app/models/user.py) não tem password_hash de
propósito — a fonte de verdade de identidade é o Supabase Auth (I2). O
setup antigo coletava uma senha na tela e a descartava silenciosamente
(system_service.py nunca a usava), porque não havia nenhum código
criando o usuário correspondente no Supabase.

A correção NÃO é sincronizar senha — seria reintroduzir uma segunda
fonte de verdade. É o backend criar o usuário no Supabase Auth via Admin
API (que não precisa de senha, o Supabase gera um magic-link) e usar o
MESMO UUID retornado como Professional.id/User.id no nosso Postgres —
exatamente o mapeamento 1:1 que security.py já assume.

A service_role key ignora RLS do Supabase e pode fazer qualquer coisa
com qualquer usuário do projeto — é o equivalente do "owner" do banco,
nunca do "app". Por isso fica isolada aqui, nunca importada por
services/repositories comuns, e nunca é a mesma coisa que
DATABASE_URL_MIGRATIONS (que é o owner do NOSSO Postgres, não do Auth).
"""

import contextlib
from uuid import UUID

import httpx

from app.core.config import settings


class SupabaseAdminError(Exception):
    """Erro ao chamar a Admin API do Supabase — mensagem já sanitizada
    para não vazar detalhe da service_role key em logs/HTTP."""


class SupabaseAdminClient:
    def __init__(self) -> None:
        if not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise SupabaseAdminError(
                "SUPABASE_SERVICE_ROLE_KEY não configurado — necessário para "
                "criar usuários via Admin API (B-01). Nunca use a anon/publishable "
                "key aqui: ela não tem permissão para esta chamada."
            )
        self._base_url = f"{settings.SUPABASE_URL}/auth/v1"
        self._headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }

    def invite_user_by_email(self, email: str, redirect_to: str | None = None) -> UUID:
        """Cria o usuário no Supabase Auth (sem senha) e dispara o e-mail
        de convite — a pessoa define a própria senha ao clicar no link.
        Retorna o UUID que o Supabase atribuiu, para usar como
        Professional.id/User.id no nosso Postgres (mesmo mapeamento 1:1
        que security.py já assume)."""
        payload: dict = {"email": email}
        if redirect_to:
            payload["options"] = {"redirect_to": redirect_to}

        try:
            resp = httpx.post(
                # Não é "/admin/invite" — o Admin API real do GoTrue expõe
                # convite em "/auth/v1/invite" (confirmado por teste manual
                # contra o projeto real em 2026-09-05: /admin/invite dá 404).
                f"{self._base_url}/invite",
                headers=self._headers,
                json=payload,
                timeout=10,
            )
        except httpx.HTTPError as exc:
            raise SupabaseAdminError(
                "Falha de rede ao chamar o Supabase Auth — tente novamente"
            ) from exc

        if resp.status_code == 422:
            # Usuário já cadastrado no Supabase Auth: recupera o UUID existente
            # para vincular ao User/Professional do banco de dados.
            try:
                get_resp = httpx.get(
                    f"{self._base_url}/admin/users",
                    headers=self._headers,
                    timeout=10,
                )
                if get_resp.status_code == 200:
                    users = get_resp.json().get("users", [])
                    matched = next((u for u in users if u.get("email") == email), None)
                    if matched and matched.get("id"):
                        return UUID(matched["id"])
            except Exception:
                pass

        if resp.status_code >= 400:
            # Mensagem genérica de propósito: o corpo do erro do Supabase
            # pode ecoar dados que não devem virar HTTPException para o
            # cliente (ver padrão de _decode() em core/security.py).
            raise SupabaseAdminError(
                f"Supabase Auth recusou o convite (HTTP {resp.status_code})"
            )

        body = resp.json()
        user_id = body.get("id")
        if not user_id:
            raise SupabaseAdminError("Resposta do Supabase sem id de usuário")
        return UUID(user_id)

    def delete_user(self, user_id: UUID) -> None:
        """Usado só para desfazer um convite se o resto da transação de
        setup falhar depois — não deixar usuário órfão no Supabase Auth
        sem User/Professional correspondente no nosso Postgres."""
        # Melhor esforço: se isto falhar, sobra um usuário órfão no
        # Supabase (inofensivo — sem User local, o login dele nunca
        # resolve professional_id) — não escalar a exceção original.
        with contextlib.suppress(httpx.HTTPError):
            httpx.delete(
                # Diferente do invite: delete/get/update de usuário vivem
                # sob "/auth/v1/admin/users/{id}" (confirmado por teste
                # manual em 2026-09-05).
                f"{self._base_url}/admin/users/{user_id}",
                headers=self._headers,
                timeout=10,
            )
