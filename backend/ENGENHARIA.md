# Guia de Engenharia — Backend

Padrões específicos deste produto. Invariantes que atravessam os dois projetos: [../ENGENHARIA.md](../ENGENHARIA.md).

**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2.0 (sync) · PostgreSQL/Supabase · Pydantic v2

---

## As treze decisões

| Decisão | Escolha | Razão |
|---|---|---|
| Isolamento | Repository **+** RLS | Duas camadas; cada uma cobre o furo da outra |
| Conexão da app | Role não-owner `NOBYPASSRLS` | Owner ignora policies **silenciosamente** |
| Contexto de tenant | `set_config(..., true)` em transação explícita | `SET` puro vaza entre tenants via pool |
| Policy | `USING` **e** `WITH CHECK` + `FORCE` | Sem `WITH CHECK` há vazamento de escrita |
| Origem do tenant | Claim `sub` do JWT, só | Header/body = IDOR que passa nos testes de auth |
| JWT | `PyJWT[crypto]` + `PyJWKClient` | Rotação sem downtime; `python-jose` tem CVEs |
| Dinheiro | `Numeric(12,2)` + `Decimal`, `ROUND_HALF_UP` | Default do Python é banker's rounding |
| JSON | `Decimal` → **string** | `JSON.parse` de número vira float no front |
| Rateio | Largest remainder | Soma dos itens fecha com o total, exato |
| Snapshot | Copiar valores + JSONB de auditoria | FK + recálculo faz o passado mudar |
| Imutabilidade | Listener `before_flush` **+** trigger | Listener proíbe; service calcula |
| Cálculo | Service layer, domínio puro | Listener não é testável nem tem contexto |
| Estados | Enum + dict imutável + trigger | Tabela explícita é auditável |

---

## 0. Ajustes no `pyproject.toml` (T-001c)

O arquivo atual tem uma contradição: `asyncio_mode = "auto"` com `psycopg2-binary` (driver **sync**).

**Decisão: stack sync.** FastAPI roda `def` endpoints em threadpool, o volume é baixo, e o padrão `SET LOCAL` + transação é bem mais difícil de errar sem `async`.

```toml
dependencies = [
    # ...
    "pyjwt[crypto]>=2.9.0",       # ← entra (substitui python-jose)
    # ← saem: python-jose, passlib[bcrypt]
]

dev = [
    # ...
    "hypothesis>=6.100",          # ← entra: property tests do rateio
    # ← sai: pytest-asyncio
]

[tool.pytest.ini_options]
# asyncio_mode = "auto"           # ← REMOVER
```

> ⚠️ **Remover `passlib`/`bcrypt` não é cosmético.** Enquanto estiverem instalados, alguém eventualmente adiciona um `password_hash` e cria um segundo caminho de auth que ninguém audita.

---

## 1. Multi-tenancy

### RLS é a segunda linha, não a única

O erro conceitual é escolher entre RLS **ou** filtro na aplicação:

- **Repository** filtra → erro cedo, mensagem clara, `404` correto
- **RLS** é a rede → se alguém esquecer o filtro, o banco devolve zero linhas

RLS sozinho é frágil (uma migration cria tabela sem policy). Filtro sozinho é frágil (um `session.query()` esquecido). Juntos, o furo exige duas falhas simultâneas.

### O pré-requisito que todo mundo pula

> 🔴 **Se a app conectar como owner ou `service_role`, RLS é ignorado silenciosamente.** As policies existem, os testes passam, e a proteção é zero.

```sql
CREATE ROLE estetica_app LOGIN PASSWORD :'app_password' NOBYPASSRLS;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO estetica_app;

-- Vale para tabelas futuras (senão a próxima migration esquece o GRANT)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO estetica_app;
```

A `DATABASE_URL` da app usa `estetica_app`. As migrations (Alembic) usam URL separada com o owner — RLS não pode bloquear `ALTER TABLE`.

### Policy: `USING` e `WITH CHECK`

```sql
ALTER TABLE sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales FORCE  ROW LEVEL SECURITY;   -- owner também obedece

CREATE POLICY tenant_isolation ON sales
  FOR ALL TO estetica_app
  USING      (professional_id = current_setting('app.professional_id', true)::uuid)
  WITH CHECK (professional_id = current_setting('app.professional_id', true)::uuid);
```

Os dois lados fazem coisas diferentes:

| Só `USING` | Só `WITH CHECK` |
|---|---|
| Lê só o seu, mas **insere** linha no tenant alheio — e pode fazer `UPDATE SET professional_id = <outro>` | Grava só no seu, mas **lê tudo de todo mundo** |

> 🔴 **`WITH CHECK` ausente é o furo clássico** — o vazamento é de *escrita*, que nenhum teste de leitura pega.

O `true` em `current_setting` faz retornar `NULL` em vez de exceção quando a variável não foi setada → policy vira `FALSE` → zero linhas. **Fail-closed.**

### Denormalizar `professional_id` nas filhas

`sale_items` e `sessions` carregam `professional_id` mesmo sendo alcançáveis via `sale_id` — senão a policy precisaria de subquery. O custo é uma FK composta:

```sql
ALTER TABLE sales ADD CONSTRAINT uq_sales_id_prof UNIQUE (id, professional_id);
ALTER TABLE sale_items
  ADD CONSTRAINT fk_items_sale
  FOREIGN KEY (sale_id, professional_id) REFERENCES sales (id, professional_id);
```

Todo índice lidera por `professional_id` — a policy vira predicado em toda query:

```sql
CREATE INDEX ix_sales_prof_created ON sales (professional_id, created_at DESC);
```

### `SET LOCAL` e o problema do pool

> 🔴 **O bug mais perigoso deste guia.** `SET` sem `LOCAL` persiste na *conexão*. Ela volta ao pool com a variável setada e o **próximo request de outro tenant a herda**. Passa em todos os testes de tenant único e só se manifesta em produção sob concorrência — vazamento intermitente e irreproduzível.

E `SET LOCAL` fora de transação é **no-op silencioso**. Então: transação aberta antes.

```python
def _set_tenant(session: Session, professional_id: UUID) -> None:
    """
    set_config(name, value, is_local=true) == SET LOCAL, mas aceita
    parâmetro bound. SET LOCAL não aceita placeholder — usá-lo obrigaria
    a interpolar string no SQL.
    """
    session.execute(
        text("SELECT set_config('app.professional_id', :pid, true)"),
        {"pid": str(professional_id)},
    )


def get_tenant_session(professional_id: UUID) -> Iterator[Session]:
    session = SessionLocal()
    try:
        with session.begin():  # BEGIN antes do set_config
            _set_tenant(session, professional_id)
            yield session  # suspenso durante todo o handler
            # saída normal → COMMIT · exceção → ROLLBACK
    finally:
        session.close()
```

Cinto de segurança no checkin do pool:

```python
@event.listens_for(engine, "checkin")
def _reset_tenant_on_checkin(dbapi_conn, connection_record) -> None:
    """SET LOCAL já reverte no commit, mas se alguém usar SET puro
    algum dia, isso limpa antes da conexão voltar ao pool."""
    try:
        with dbapi_conn.cursor() as cur:
            cur.execute("RESET app.professional_id")
        dbapi_conn.commit()
    except Exception:
        pass
```

### A cadeia que torna o vazamento impossível

```python
CurrentProfessional = Annotated[UUID, Depends(get_current_professional_id)]


def _db(professional_id: CurrentProfessional):
    yield from get_tenant_session(professional_id)


DbSession = Annotated[Session, Depends(_db)]
```

**É impossível obter uma `DbSession` sem passar pela validação do JWT.** Rotas públicas simplesmente não declaram `DbSession`.

Para jobs, um helper explicitamente nomeado — para aparecer em code review e grep:

```python
@contextmanager
def unsafe_session_without_tenant(reason: str) -> Iterator[Session]:
    """⚠️ Sem contexto de tenant. `reason` é obrigatório de propósito."""
```

### Repository base (T-058a)

```python
class TenantRepository(Generic[M]):
    def __init__(self, session: Session, professional_id: UUID) -> None:
        if professional_id is None:
            raise ValueError("professional_id é obrigatório")
        self._session = session  # privado: autocomplete não sugere .query()
        self._professional_id = professional_id

    def _scoped(self) -> Select[tuple[M]]:
        """ÚNICA fonte de SELECT. Todo método de leitura passa por aqui."""
        return select(self.model).where(
            self.model.professional_id == self._professional_id
        )

    def add(self, obj: M) -> M:
        # Carimba o tenant em vez de confiar em quem chamou
        if obj.professional_id not in (None, self._professional_id):
            raise ValueError("tentativa de gravar em tenant alheio")
        obj.professional_id = self._professional_id
        self._session.add(obj)
        self._session.flush()
        return obj
```

O `add()` que **carimba** protege mesmo que um schema descuidado aceite `professional_id` do body. E o `raise` transforma vazamento silencioso em erro barulhento.

### Barrar query crua — três camadas

```toml
# 1) Lint (ruff já está configurado)
[tool.ruff.lint.flake8-tidy-imports.banned-api]
"sqlalchemy.orm.Session.query".msg = "Use TenantRepository — query() cru escapa do filtro"
```

```python
# 2) Teste de arquitetura
def test_nenhum_query_cru_fora_do_repositorio():
    for py in ROOT.rglob("*.py"):
        if "repositories" in py.parts:
            continue
        assert not re.search(r"\.query\(|session\.execute\(select\(", py.read_text())
```

3) RLS cobre o resto.

---

## 2. Autenticação

```python
@lru_cache(maxsize=1)
def _jwk_client() -> PyJWKClient:
    """
    lifespan=600 casa com o cache do edge do Supabase. Muito longo
    rejeita token válido após rotação; muito curto vira 1 HTTP por chamada.
    """
    return PyJWKClient(
        f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json",
        cache_keys=True,
        lifespan=600,
        max_cached_keys=8,
    )


def _decode(token: str) -> dict:
    try:
        key = _jwk_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            key.key,
            algorithms=["ES256", "RS256"],  # lista explícita; NUNCA o alg do header
            audience="authenticated",
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
            options={"require": ["exp", "sub", "aud", "iss"], "verify_signature": True},
        )
    except jwt.PyJWTError as exc:
        # Genérica de propósito: distinguir "expirado" de "assinatura inválida"
        # entrega informação a quem sonda a API.
        raise HTTPException(401, "Token inválido") from exc


def get_current_professional_id(creds=Depends(_bearer)) -> UUID:
    """ÚNICA origem de professional_id na aplicação inteira (T-006a)."""
    claims = _decode(creds.credentials)
    if claims.get("role") != "authenticated":
        raise HTTPException(403, "Role não autorizada")
    return UUID(claims["sub"])
```

### Como não aceitar tenant do request

```python
class InputSchema(BaseModel):
    """Base de TODO schema de request. extra='forbid' faz campo
    indesejado explodir em 422 em vez de ser ignorado em silêncio."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
```

```python
def test_nenhum_schema_aceita_professional_id():
    for _, obj in inspect.getmembers(schemas_pkg):
        if inspect.isclass(obj) and issubclass(obj, InputSchema):
            assert "professional_id" not in obj.model_fields
```

E **nenhuma rota tem `professional_id` no path** — `/professionals/{pid}/sales` é convite a IDOR. Use `/sales`.

> 🔴 **Aceitar `professional_id` do body:** a autenticação continua funcionando (o token é válido), então passa por todo teste de auth — e vira acesso trivial a dados alheios trocando um UUID.

---

## 3. Precisão decimal

```python
Money = Annotated[Decimal, mapped_column(Numeric(12, 2, asdecimal=True))]
Rate = Annotated[Decimal, mapped_column(Numeric(9, 4, asdecimal=True))]
```

`Rate` com 4 casas: 3,99% → `0.0399`. Duas casas arredondariam a taxa antes da multiplicação.

```python
def money(value: Decimal | int | str) -> Decimal:
    """
    ROUND_HALF_UP, não ROUND_HALF_EVEN — que é o DEFAULT do Python.
    Contabilidade brasileira e expectativa do usuário são half-up:
    0,125 → 0,13. Banker's daria 0,12 e a cliente reclamaria.
    """
    if isinstance(value, float):
        raise TypeError("float é proibido — use Decimal('10.50') ou str")
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)
```

> **Onde arredondar** é a decisão que mais gera bug: mantenha precisão total durante a cadeia e `quantize` só na fronteira (persistência/JSON). Arredondar na entrada *e* na saída arredonda duas vezes.

### Serialização

```python
MoneyOut = Annotated[
    Decimal,
    BeforeValidator(_to_decimal),
    PlainSerializer(
        lambda d: str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        return_type=str,
        when_used="json",  # em Python continua Decimal para cálculo
    ),
]
```

`when_used="json"` mantém `Decimal` em Python — testes e lógica seguem comparando `Decimal`, só a serialização HTTP vira string.

### Rateio que fecha exatamente

R$ 10,00 entre 3 itens dá R$ 3,333… Arredondando cada um para R$ 3,33, a soma é R$ 9,99. **Em relatório financeiro isso é bug de auditoria.**

```python
def allocate(total: Decimal, weights: list[Decimal]) -> list[Decimal]:
    """
    Largest remainder (Hare quota):
      1. cota exata = total * peso / soma_pesos
      2. arredonda PARA BAIXO em centavos
      3. sobram K centavos
      4. distribui 1 centavo aos K itens de maior resto fracionário

    Por que não "o último absorve o resto": concentra o desvio inteiro
    num item — com 10 itens e R$ 0,09 de sobra, o último fica 9 centavos
    fora da proporção. Pior ainda se esse item for estornado depois.
    """
    exact = [abs_total * w / total_weight for w in weights]
    floors = [e.quantize(cent, rounding=ROUND_DOWN) for e in exact]
    remainder = int(((abs_total - sum(floors)) / cent).to_integral_value())

    # Desempate por índice mantém determinístico — recálculo reproduz o mesmo rateio
    order = sorted(
        range(len(weights)), key=lambda i: (exact[i] - floors[i], -i), reverse=True
    )
    for i in order[:remainder]:
        floors[i] += cent

    assert sum(result) == total, f"rateio não fechou: {sum(result)} != {total}"
    return result
```

| | cota | floor | resto | +1¢ | final |
|---|---|---|---|---|---|
| item 1 | 3.3333… | 3.33 | .3333 | ✓ | **3.34** |
| item 2 | 3.3333… | 3.33 | .3333 | | 3.33 |
| item 3 | 3.3333… | 3.33 | .3333 | | 3.33 |
| | | 9.99 | | | **10.00** ✓ |

> 🔴 **Sem isso:** soma de itens ≠ total da venda. Aparece meses depois na conferência contábil, e **não dá para recalcular retroativamente** porque os valores são congelados (§4).

---

## 4. Snapshot congelado

**Um registro financeiro guarda o resultado *e* os insumos que o produziram.** Guardar só a FK para `Config` e recalcular ao ler significa que o histórico muda sozinho quando a config muda.

```python
class Sale(TenantModel):
    # SNAPSHOT: copiados no ato da venda, NUNCA relidos de Config depois
    snapshot_fee_rate: Mapped[Decimal] = mapped_column(Rate)
    snapshot_split_rate: Mapped[Decimal] = mapped_column(Rate)
    snapshot_fee_payer: Mapped[str] = mapped_column(String(20))  # E1
    snapshot_split_base: Mapped[str] = mapped_column(String(20))  # E2

    config_version_id: Mapped[UUID] = mapped_column(ForeignKey("config_versions.id"))
    snapshot_payload: Mapped[dict] = mapped_column(JSONB)  # auditoria

    __table_args__ = (
        # A identidade contábil, garantida pelo BANCO. Nenhum bug de
        # aplicação consegue gravar uma venda que não fecha.
        CheckConstraint(
            "net_amount = gross_amount - discount_amount", name="ck_sales_net_coerente"
        ),
    )
```

O `CheckConstraint` é a única defesa que sobrevive a bug de aplicação, migration mal feita ou correção manual via SQL.

### Config versionada

```python
class ConfigVersion(TenantModel):
    """Config NUNCA sofre UPDATE. Toda mudança cria versão nova com
    valid_from/valid_to — é o que torna possível responder
    'qual era a taxa em 12/03?'"""

    valid_from: Mapped[datetime]
    valid_to: Mapped[datetime | None]  # NULL = vigente

    __table_args__ = (
        Index(
            "uq_config_vigente",
            "professional_id",
            unique=True,
            postgresql_where=text("valid_to IS NULL"),
        ),
    )
```

```python
def editar(self, sale_id, dto):
    """
    Edição de venda histórica → config da ÉPOCA DA VENDA.
    Usar a config de hoje faria uma correção de digitação alterar
    o lucro de um mês já fechado.
    """
    cfg = self._configs.vigente_em(sale.sold_at)
```

### Listener proíbe, service calcula

```python
@event.listens_for(Session, "before_flush")
def _bloqueia_alteracao_de_snapshot(session, flush_ctx, instances) -> None:
    """
    Listener é a ferramenta CERTA aqui porque a regra é uma PROIBIÇÃO
    transversal — vale para todo caminho de código, inclusive o que
    esquecerem de escrever.
    """
    for obj in session.dirty:
        for field in FROZEN_FIELDS.get(type(obj), ()):
            hist = inspect(obj).attrs[field].history
            # deleted não-vazio = havia valor anterior = é UPDATE, não INSERT
            if hist.has_changes() and hist.deleted:
                raise ImmutableFieldError(
                    f"{field} é congelado. Para corrigir, estorne e refaça."
                )
```

**Por que NÃO calcular em listeners:**

| Problema | Detalhe |
|---|---|
| Testabilidade | Só dispara com sessão real e flush; o motor precisa rodar sem banco |
| Contexto | `before_insert` não tem o request; buscar Config no flush é desencorajado |
| Ordem | Sale e SaleItem fazem flush em ordem que o UoW decide |
| Invisibilidade | `grep calcular_lucro` deve achar o cálculo |
| Bulk | `session.execute(update(...))` **não dispara** listeners |

---

## 5. Camadas

```
api/routers/   HTTP: rota, status, schema. ZERO regra de negócio.
services/      Orquestração: transação, autorização, chama engine + repos.
domain/        ⭐ MOTOR DE LUCRO. Puro. Sem SQLAlchemy, sem FastAPI, sem I/O.
repositories/  Acesso a dados. Sempre com tenant.
models/        SQLAlchemy. Estrutura + constraints.
schemas/       Pydantic. Nunca vaza para domain/.
```

**`app/domain/` não importa nada de `models`, `schemas` ou `sqlalchemy`.** Garantido por teste (§6).

### Duas decisões dentro do motor

```python
# 1) Taxa: calcula o TOTAL e rateia — não calcula por item e soma.
#    Somar N arredondamentos diverge da taxa que a adquirente cobra sobre o total.
fee_total = money(net_total * params.fee_rate)
fees = allocate(fee_total, nets)

# 2) Total do lucro = SOMA dos itens, não cálculo independente.
#    Garante que o cabeçalho nunca contradiz o detalhamento exibido.
professional_profit = money(sum(r.professional_profit for r in resultados))
```

### Máquina de estados

```python
SALE_TRANSITIONS = MappingProxyType(
    {  # imutável em runtime
        SaleStatus.DRAFT: frozenset({SaleStatus.PENDING, SaleStatus.CANCELLED}),
        SaleStatus.PENDING: frozenset({SaleStatus.PAID, SaleStatus.CANCELLED}),
        SaleStatus.PAID: frozenset({SaleStatus.REFUNDED}),
        SaleStatus.CANCELLED: frozenset(),  # terminal
        SaleStatus.REFUNDED: frozenset(),
    }
)

# Depois de PAID o dinheiro entrou: correção é estorno + nova venda
EDITABLE_STATES = frozenset({SaleStatus.DRAFT, SaleStatus.PENDING})
```

```python
def test_todo_status_esta_na_tabela():
    """Adicionar status ao enum e esquecer da tabela = KeyError em produção."""
    assert set(SALE_TRANSITIONS) == set(SaleStatus)
```

Espelhe em trigger, para UPDATE fora da aplicação.

### Router: 404, nunca 403

```python
@router.get("/{sale_id}")
def obter_venda(sale_id: UUID, svc: SaleSvc) -> Sale:
    sale = svc.obter(sale_id)
    if sale is None:
        # "Existe mas não é seu" já vaza informação: confirma a
        # existência do recurso de outro tenant.
        raise HTTPException(404, "Venda não encontrada")
    return sale
```

---

## 6. Testes

### Fixture transacional

```python
@pytest.fixture
def db_connection(engine):
    """
    Transação externa que sofre ROLLBACK no fim. Cada teste vê banco
    limpo sem TRUNCATE (lento e reseta sequences).
    """
    conn = engine.connect()
    trans = conn.begin()
    # join_transaction_mode é o que faz funcionar no SQLAlchemy 2.0:
    # sem ele, um commit() no código sob teste encerraria a transação externa
    SessionTest = sessionmaker(bind=conn, join_transaction_mode="create_savepoint")
    session = SessionTest()
    yield conn, session
    session.close()
    trans.rollback()
    conn.close()
```

> ⚠️ O engine de teste conecta como `estetica_app` — senão RLS não vale e os testes de isolamento são teatro.

### Isolamento genérico (T-046)

O teste mais valioso do suite: cobre **rotas que ainda não existem**.

```python
@pytest.mark.parametrize("method,path,name", _rotas_de_recurso())
def test_tenant_a_nao_acessa_recurso_de_b(method, path, name, ...):
    """A→404 em TODO recurso de B, em TODA rota, em TODO método."""
    resp = client_a.request(method, url)
    assert resp.status_code in (404, 422), f"VAZAMENTO em {method} {path}"
    for valor in recursos_b.values():
        assert str(valor) not in resp.text, "ID de B vazou no corpo"
```

E os que provam o RLS em si:

```python
def test_rls_bloqueia_query_crua_cross_tenant(...):
    """Prova a segunda camada: mesmo escapando do repositório, não vaza."""
    _set_tenant(session, professional_a)
    assert session.execute(text("SELECT id FROM sales")).all() == []

def test_rls_bloqueia_insert_em_tenant_alheio(...):
    """WITH CHECK: A não grava dentro de B."""

def test_sem_contexto_nao_retorna_nada(...):
    """Fail-closed: variável não setada → zero linhas, nunca 'tudo'."""

def test_toda_tabela_de_tenant_tem_rls(db_connection):
    """Migration que cria tabela sem policy = vazamento silencioso.
    Pega no CI, não em produção."""
    faltando = conn.execute(text("""
        SELECT c.relname FROM pg_class c
        JOIN information_schema.columns col ON col.table_name = c.relname
        WHERE col.column_name = 'professional_id' AND c.relkind = 'r'
          AND (NOT c.relrowsecurity OR NOT c.relforcerowsecurity)
    """)).scalars().all()
    assert not faltando
```

### Matriz de configuração (T-044)

```python
CONFIGS = {
    "taxa_dela_split_bruto":     ProfitParams(..., PROFESSIONAL, GROSS),
    "taxa_dela_split_liquido":   ProfitParams(..., PROFESSIONAL, NET),
    "taxa_clinica_split_bruto":  ProfitParams(..., CLINIC, GROSS),
    "taxa_clinica_split_liquido":ProfitParams(..., CLINIC, NET),
    "sem_taxa":                  ProfitParams(fee_rate=D("0"), ...),
}

pytestmark = pytest.mark.parametrize("params", CONFIGS.values(), ids=list(CONFIGS))

class TestInvariantesUniversais:
    """Valem em TODAS as configs. Rodam 5x, sem banco — milissegundos."""

    def test_soma_dos_itens_fecha_com_o_total(self, params): ...
    def test_identidade_contabil(self, params): ...

    @pytest.mark.parametrize("desconto", ["0.01", "0.10", "33.33", "99.99"])
    def test_rateio_indivisivel_sempre_fecha(self, params, desconto): ...

    def test_tudo_tem_duas_casas(self, params): ...
    def test_determinismo(self, params):
        """Mesma entrada → mesma saída. Recálculo tem que reproduzir."""
```

Property test para o que ninguém pensa em escrever:

```python
@given(
    valores=st.lists(st.decimals(min_value=D("0.01"), places=2), min_size=1),
    frac=st.decimals(min_value=D("0"), max_value=D("1"), places=4),
)
def test_rateio_sempre_fecha(valores, frac):
    """Hypothesis acha os casos de arredondamento que a gente não imagina."""
    desconto = money(sum(valores) * frac)
    assert sum(allocate(desconto, valores)) == desconto
```

### Arquitetura

```python
def test_dominio_nao_importa_infraestrutura():
    """O valor de domain/ é ser testável sem banco. Um `from app.models`
    destrói isso silenciosamente — só se percebe quando o suite fica lento."""
    proibidos = ("sqlalchemy", "fastapi", "app.models", "app.repositories")


def test_dominio_nao_usa_float():
    for py in (ROOT / "domain").rglob("*.py"):
        assert "float(" not in py.read_text()
```

---

## Ordem sugerida

1. **T-001c** — decidir sync destrava tudo mais
2. **T-001a/T-001d** — `core/money.py` com `allocate()` e property tests. É puro, não depende de banco, e é o núcleo do produto
3. **T-006/T-006a** — auth com JWKS
4. **T-058/T-058a** — role de app, policies, `TenantRepository`
5. **T-046** — teste genérico **antes** das rotas de negócio, para que cada rota nova nasça validada

> Os itens 2 e 5 são os que mais compensam antecipar: `allocate()` errado gera inconsistência **não-retrofitável** (valores congelados não podem ser recalculados), e o teste de isolamento perde quase todo o valor se entrar depois das rotas.

---

## Dois pedidos do frontend

1. **Idempotência do `POST /sales`** (T-015) — mesma chave + mesmo corpo → 200 com a venda existente, não 409. Chave diferente com mesmo corpo → nova venda. TTL 24h.
2. **`hasAnyData` no `GET /dashboard`** (T-022) — 1 booleano que distingue "primeira vez" de "mês sem venda" nos empty states.

---

## Checklist de PR

- [ ] Nenhum `float` em caminho monetário
- [ ] `Decimal` serializado como string no JSON
- [ ] Rateio usa `allocate` e a soma fecha
- [ ] Query nova passa por `TenantRepository`
- [ ] Tabela nova tem RLS + `FORCE` + `USING` + `WITH CHECK`
- [ ] Índice novo lidera por `professional_id`
- [ ] Campo de snapshot está em `FROZEN_FIELDS`
- [ ] Status novo está em `SALE_TRANSITIONS`
- [ ] Recurso não encontrado devolve 404, nunca 403
- [ ] Se toca cálculo: matriz de 5 configurações passa
