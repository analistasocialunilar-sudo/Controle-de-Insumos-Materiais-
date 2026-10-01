importar fluxo de luz como rua
import sqlite3
import pandas as pd
de data e hora importar data e hora
# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E BANCO DE DADOS (SQLite)
# ==============================================================================
st.set_page_config(
    page_title="Gestão de Farmácia - Assistência Domiciliar",
    page_icon="💊",
    layout="wide"
)

DB_NAME = "estoque_farmacia.db"

# Lista de Pacientes extraída da imagem e atualizada com as enfermeiras responsáveis
PACIENTES_RAW = [
    {"nome": "MARCIA RODRIGUES RIBEIRO", "telefone": "(74)991-984-281", "programa": "PCP"},
    {"nome": "SILVANA APARECIDA SILVA DE MELO", "telefone": "(87)8174-0027", "programa": "PCP"},
    {"nome": "VIRGINIA FERNANDES DE MEDEIROS DINIZ", "telefone": "(87)988-261-915", "programa": "PCP"},
    {"nome": "JULIO VINICIUS DA CRUZ", "telefone": "(74)8863-1920", "programa": "PCP"},
    {"nome": "ANA VITORIA SOARES ALVES", "telefone": "(87)981-355-610", "programa": "PCP"},
    {"nome": "ARISTON OLIVEIRA MARTINS", "telefone": "(74)988-127-404", "programa": "PCP"},
    {"nome": "ASTOR MOLLER", "telefone": "(74)988-372-718", "programa": "PCP"},
    {"nome": "ANTONIA MARIA SANDES GOMES", "telefone": "(87)3866-0679", "programa": "PCP"},
    {"nome": "FRANCISCO MUNIZ BARRETTO", "telefone": "(87)988-239-169", "programa": "PCP"},
    {"nome": "ZILDA GONDIM DE MENDONCA", "telefone": "(87)8826-2357", "programa": "PCP"},
    {"nome": "TEREZINHA TELES DA SILVA", "telefone": "(74)8866-1963", "programa": "PCP"},
    {"nome": "ALMIRA COELHO ASSIS", "telefone": "(74)3611-2226", "programa": "PCP"},
    {"nome": "REGINA LUCIA DE AZEVEDO", "telefone": "(87)8118-5975", "programa": "PCP"},
    {"nome": "PEROLA JASMIN VIANA", "telefone": "(87)8868-7707", "programa": "PCP"},
    {"nome": "OLINDA CELINA CARDOSO", "telefone": "(74)8809-0018", "programa": "PCP"},
    {"nome": "GABRIEL FRANCISCO ALVES", "telefone": "(87)38618469", "programa": "PCP"},
    {"nome": "FELIX RODRIGUES DE ANDRADE", "telefone": "(87)38643655", "programa": "PCP"},
    {"nome": "RUTE CORREIA MOREIRA", "telefone": "(81)981-011-560", "programa": "PCP"},
    {"nome": "ISABEL AMORIM GOMES SOUZA", "telefone": "(87)8829-8523", "programa": "PCP"},
    {"nome": "ARTUR GAEL BARBOSA VIEIRA DA SILVA CRUZ", "telefone": "(87)8836-2329", "programa": "PCP"}
]

# Monta a lista final com atribuição automática das Enfermeiras de Referência
PACIENTES_INICIAIS = []
for p in PACIENTES_RAW:
    # Regra: Se for Perolla Jasmin Viana -> Nara Armentano, caso contrário -> Amanda Ellen Bezerra dos Santos
    if "PEROLA JASMIN" in p["nome"].upper():
        enfermeira = "Nara Armentano"
    else:
        enfermeira = "Amanda Ellen Bezerra dos Santos"
        
    PACIENTES_INICIAIS.append({
        "nome": p["nome"],
        "telefone": p["telefone"],
        "programa": p["programa"],
        "enfermeiro": enfermeira,
        "responsavel": "Família"
    })

def init_db():
    """Inicializa as tabelas do SQLite e carrega os pacientes no banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de Produtos (Medicamentos/Insumos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            quantidade_atual INTEGER NOT NULL DEFAULT 0,
            quantidade_minima INTEGER NOT NULL DEFAULT 10,
            unidade_medida TEXT NOT NULL
        )
    ''')

    # Tabela de Pacientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_paciente TEXT NOT NULL,
            telefone TEXT,
            programa TEXT NOT NULL,
            enfermeiro_referencia TEXT NOT NULL,
            responsavel_familia TEXT
        )
    ''')

    # Tabela de Movimentações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            tipo_movimentacao TEXT NOT NULL,
            produto_id INTEGER NOT NULL,
            produto_nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            paciente_nome TEXT,
            enfermeiro_referencia TEXT,
            responsavel_retirada TEXT,
            observacao TEXT
        )
    ''')

    # Carrega ou atualiza os pacientes no banco de dados
    cursor.execute("SELECT COUNT(*) FROM pacientes")
    if cursor.fetchone()[0] == 0:
        for p in PACIENTES_INICIAIS:
            cursor.execute('''
                INSERT INTO pacientes (nome_paciente, telefone, programa, enfermeiro_referencia, responsavel_familia)
                VALUES (?, ?, ?, ?, ?)
            ''', (p["nome"], p["telefone"], p["programa"], p["enfermeiro"], p["responsavel"]))
    
    conn.commit()
    conn.close()

init_db()

# ==============================================================================
# 2. AUTENTICAÇÃO E LOGIN
# ==============================================================================
USUARIOS = {
    "farmacia": {"senha": "123", "perfil": "Equipa da Farmácia", "nome": "Farmácia Central"},
    "enfermeiro": {"senha": "456", "perfil": "Enfermeiro de Referência", "nome": "Equipe de Enfermagem"},
    "familia": {"senha": "789", "perfil": "Cuidador / Família", "nome": "Acesso Familiar / Domiciliar"},
    "admin": {"senha": "admin", "perfil": "Administrador", "nome": "Gestão Geral"}
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario_nome"] = ""
    st.session_state["usuario_perfil"] = ""

def realizar_login(usuario, senha):
    if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
        st.session_state["autenticado"] = True
        st.session_state["usuario_nome"] = USUARIOS[usuario]["nome"]
        st.session_state["usuario_perfil"] = USUARIOS[usuario]["perfil"]
        st.success("Login efetuado com sucesso!")
        st.rerun()
    else:
        st.error("Utilizador ou palavra-passe incorretos.")

def realizar_logout():
    st.session_state["autenticado"] = False
    st.session_state["usuario_nome"] = ""
    st.session_state["usuario_perfil"] = ""
    st.rerun()

if not st.session_state["autenticado"]:
    st.title("💊 Gestão de Farmácia e Insumos - Assistência Domiciliar")
    st.subheader("🔐 Acesso ao Sistema")
    
    with st.form("form_login"):
        u_input = st.text_input("Utilizador").strip().lower()
        p_input = st.text_input("Palavra-passe", type="password")
        btn_login = st.form_submit_button("Entrar")
        
        if btn_login:
            realizar_login(u_input, p_input)
            
    st.info("💡 **Perfis de Acesso:**\n- **Farmácia/Admin:** `farmacia` (123) / `admin` (admin)\n- **Enfermeiro:** `enfermeiro` (456)\n- **Família:** `familia` (789)")
    st.stop()

# ==============================================================================
# 3. CABEÇALHO E ABAS DA APLICAÇÃO
# ==============================================================================
col_tit, col_user = st.columns([3, 1])
with col_tit:
    st.title("💊 Farmácia - Assistência Domiciliar")
    st.caption("Controle de Estoque, Dispensação por Paciente e Alertas de Compras")

with col_user:
    st.write(f"👤 **{st.session_state['usuario_nome']}**")
    st.caption(f"Perfil: {st.session_state['usuario_perfil']}")
    if st.button("🚪 Sair"):
        realizar_logout()

st.divider()

perfil = st.session_state["usuario_perfil"]

if perfil in ["Equipa da Farmácia", "Administrador"]:
    abas_nomes = ["📊 1. Painel & Alertas", "📦 2. Entradas & Lista de Compras", "🤝 3. Dispensação (Saídas)", "📋 4. Histórico & Pacientes"]
elif perfil == "Enfermeiro de Referência":
    abas_nomes = ["📊 1. Painel & Alertas", "🤝 3. Dispensação (Saídas)", "📋 4. Histórico & Pacientes"]
else:
    abas_nomes = ["📋 Consulta & Dispensações do Paciente"]

abas = st.tabs(abas_nomes)

def get_connection():
    return sqlite3.connect(DB_NAME)

# ==============================================================================
# ABA 1: PAINEL GERAL & ALERTAS
# ==============================================================================
if "📊 1. Painel & Alertas" in abas_nomes:
    idx = abas_nomes.index("📊 1. Painel & Alertas")
    with abas[idx]:
        st.header("📊 Painel Geral de Estoque")
        
        conn = get_connection()
        df_produtos = pd.read_sql_query("SELECT * FROM produtos", conn)
        df_mov = pd.read_sql_query("SELECT * FROM movimentacoes", conn)
        conn.close()

        if df_produtos.empty:
            st.warning("Nenhum produto cadastrado até o momento. Cadastre itens na Aba 2.")
        else:
            df_criticos = df_produtos[df_produtos["quantidade_atual"] <= df_produtos["quantidade_minima"]]

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total de Itens Cadastrados", len(df_produtos))
            col2.metric("Itens com Estoque OK", len(df_produtos) - len(df_criticos))
            col3.metric("⚠️ Itens Críticos (Repor)", len(df_criticos), delta_color="inverse")
            col4.metric("Total de Dispensações", len(df_mov[df_mov["tipo_movimentacao"] == "Saída"]))

            st.divider()

            if not df_criticos.empty:
                st.error("🚨 **ALERTAS DE ESTOQUE MÍNIMO ATINGIDO / COMPRA NECESSÁRIA:**")
                st.dataframe(df_criticos[["nome", "categoria", "quantidade_atual", "quantidade_minima", "unidade_medida"]], use_container_width=True)
            else:
                st.success("✅ Todos os itens estão com estoque adequado!")

            st.subheader("📦 Saldo Atual da Farmácia")
            st.dataframe(df_produtos, use_container_width=True)

# ==============================================================================
# ABA 2: ENTRADAS & COMPRAS
# ==============================================================================
if "📦 2. Entradas & Lista de Compras" in abas_nomes:
    idx = abas_nomes.index("📦 2. Entradas & Lista de Compras")
    with abas[idx]:
        st.header("📦 Gestão de Entradas e Compras")
        col_cad, col_ent = st.columns(2)

        conn = get_connection()
        df_produtos = pd.read_sql_query("SELECT * FROM produtos", conn)
        
        with col_cad:
            st.subheader("➕ Cadastrar Novo Medicamento / Insumo")
            with st.form("form_novo_produto"):
                nome_p = st.text_input("Nome do Item / Medicamento *", placeholder="Ex: Soro Fisiológico 0,9% 500ml")
                cat_p = st.selectbox("Categoria *", ["Medicamento", "Insumo / Curativo", "Equipamento", "Dieta / Nutrição", "Outros"])
                qtd_ini = st.number_input("Quantidade Inicial", min_value=0, value=0)
                qtd_min = st.number_input("Estoque Mínimo (Crítico) *", min_value=1, value=10)
                unidade = st.selectbox("Unidade *", ["Frasco", "Caixa", "Unidade", "Ampola", "Pacote", "Rolo"])
                btn_cad = st.form_submit_button("💾 Cadastrar Produto")

            if btn_cad:
                if nome_p.strip():
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO produtos (nome, categoria, quantidade_atual, quantidade_minima, unidade_medida) VALUES (?, ?, ?, ?, ?)",
                                   (nome_p.strip(), cat_p, qtd_ini, qtd_min, unidade))
                    conn.commit()
                    st.success(f"Item '{nome_p}' cadastrado!")
                    st.rerun()

        with col_ent:
            st.subheader("📥 Registrar Entrada de Nota / Reposição")
            if not df_produtos.empty:
                with st.form("form_entrada"):
                    prod_sel = st.selectbox("Selecione o Item", df_produtos["nome"].tolist())
                    qtd_in = st.number_input("Quantidade Recebida", min_value=1, value=1)
                    obs_in = st.text_input("Observação / Nº da Nota", placeholder="Ex: NF 9876")
                    btn_in = st.form_submit_button("📥 Confirmar Entrada")

                if btn_in:
                    p_id = df_produtos[df_produtos["nome"] == prod_sel]["id"].values[0]
                    qtd_at = df_produtos[df_produtos["nome"] == prod_sel]["quantidade_atual"].values[0]
                    
                    cursor = conn.cursor()
                    cursor.execute("UPDATE produtos SET quantidade_atual = ? WHERE id = ?", (qtd_at + qtd_in, p_id))
                    cursor.execute("INSERT INTO movimentacoes (data_hora, tipo_movimentacao, produto_id, produto_nome, quantidade, observacao) VALUES (?, 'Entrada', ?, ?, ?, ?)",
                                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), p_id, prod_sel, qtd_in, obs_in))
                    conn.commit()
                    st.success(f"+{qtd_in} unidades adicionadas!")
                    st.rerun()

        conn.close()

        st.divider()

        # Lista de Compras Automática
        st.subheader("🛒 Lista de Compras Automática")
        conn = get_connection()
        df_compras = pd.read_sql_query("SELECT * FROM produtos WHERE quantidade_atual <= quantidade_minima", conn)
        conn.close()

        if df_compras.empty:
            st.success("Nenhum item precisa de compra no momento.")
        else:
            df_compras["Sugestão de Compra"] = df_compras["quantidade_minima"] * 2 - df_compras["quantidade_atual"]
            st.dataframe(df_compras[["nome", "categoria", "quantidade_atual", "quantidade_minima", "Sugestão de Compra", "unidade_medida"]], use_container_width=True)
            
            csv_c = df_compras.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Baixar Lista de Compras (Excel/CSV)", data=csv_c, file_name="lista_compras.csv", mime="text/csv")

# ==============================================================================
# ABA 3: DISPENSAÇÃO (SAÍDAS PARA OS PACIENTES E ENFERMEIRAS)
# ==============================================================================
if "🤝 3. Dispensação (Saídas)" in abas_nomes:
    idx = abas_nomes.index("🤝 3. Dispensação (Saídas)")
    with abas[idx]:
        st.header("🤝 Registro de Saída / Dispensação Mensal")

        conn = get_connection()
        df_produtos = pd.read_sql_query("SELECT * FROM produtos WHERE quantidade_atual > 0", conn)
        df_pacientes = pd.read_sql_query("SELECT * FROM pacientes ORDER BY nome_paciente ASC", conn)

        if df_produtos.empty:
            st.error("⚠️️ Sem estoque disponível na farmácia para dispensação.")
        elif df_pacientes.empty:
            st.warning("Nenhum paciente cadastrado.")
        else:
            lista_nomes_pacientes = df_pacientes["nome_paciente"].tolist()

            with st.form("form_dispensacao"):
                st.subheader("📋 Formulário de Saída de Insumos")
                c1, c2 = st.columns(2)

                with c1:
                    pac_sel = st.selectbox("Selecione o Paciente *", lista_nomes_pacientes)
                    
                    # Recupera Enfermeira, Telefone e Programa associados ao paciente
                    dados_pac = df_pacientes[df_pacientes["nome_paciente"] == pac_sel].iloc[0]
                    enf_ref = dados_pac["enfermeiro_referencia"]
                    prog_pac = dados_pac["programa"]
                    tel_pac = dados_pac.get("telefone", "Não informado")

                    st.info(f"👩‍⚕️ **Enfermeira de Referência:** {enf_ref}\n\n📌 **Programa:** {prog_pac} | 📞 **Telefone:** {tel_pac}")

                    item_disp = st.selectbox("Medicamento / Insumo Solicitado *", df_produtos["nome"].tolist())
                    qtd_disp = df_produtos[df_produtos["nome"] == item_disp]["quantidade_atual"].values[0]
                    unid_disp = df_produtos[df_produtos["nome"] == item_disp]["unidade_medida"].values[0]
                    st.caption(f"Saldo atual em estoque: **{qtd_disp} {unid_disp}**")

                with c2:
                    qtd_retirada = st.number_input(f"Quantidade Entregue ({unid_disp}) *", min_value=1, max_value=int(qtd_disp), value=1)
                    nome_retirou = st.text_input("Nome do Responsável pela Retirada (Cuidador/Familiar) *", placeholder="Ex: Maria (Esposa)")
                    obs_disp = st.text_area("Contagem / Observações do Domicílio", placeholder="Ex: Entregue lote referente ao mês. Contagem inicial em domicílio realizada.")

                btn_disp = st.form_submit_button("✅ Salvar e Registrar Saída")

            if btn_disp:
                if not nome_retirou.strip():
                    st.error("⚠️ Digite o nome do responsável pela retirada.")
                else:
                    p_id = df_produtos[df_produtos["nome"] == item_disp]["id"].values[0]
                    nova_qtd = qtd_disp - qtd_retirada

                    cursor = conn.cursor()
                    cursor.execute("UPDATE produtos SET quantidade_atual = ? WHERE id = ?", (nova_qtd, p_id))
                    
                    data_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute('''
                        INSERT INTO movimentacoes (
                            data_hora, tipo_movimentacao, produto_id, produto_nome, quantidade,
                            paciente_nome, enfermeiro_referencia, responsavel_retirada, observacao
                        ) VALUES (?, 'Saída', ?, ?, ?, ?, ?, ?, ?)
                    ''', (data_agora, p_id, item_disp, qtd_retirada, pac_sel, enf_ref, nome_retirou.strip(), obs_disp))

                    conn.commit()
                    st.success(f"✅ Saída de {qtd_retirada}x {item_disp} registrada com sucesso para o paciente {pac_sel}!")
                    st.rerun()

        conn.close()

# ==============================================================================
# ABA 4: HISTÓRICO COMPLETO & PACIENTES
# ==============================================================================
if "📋 4. Histórico & Pacientes" in abas_nomes or "📋 Consulta & Dispensações do Paciente" in abas_nomes:
    aba_idx = 0 if perfil == "Cuidador / Família" else abas_nomes.index("📋 4. Histórico & Pacientes")
    
    with abas[aba_idx]:
        st.header("📋 Histórico de Movimentações")

        conn = get_connection()
        df_mov = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY id DESC", conn)
        df_pac = pd.read_sql_query("SELECT * FROM pacientes ORDER BY nome_paciente ASC", conn)
        conn.close()

        if df_mov.empty:
            st.info("Nenhuma movimentação registrada.")
        else:
            if perfil == "Cuidador / Família":
                st.subheader("🔍 Consultar Dispensações do Paciente")
                pac_filtro = st.selectbox("Selecione o Paciente:", df_pac["nome_paciente"].tolist())
                df_f = df_mov[df_mov["paciente_nome"] == pac_filtro]
                st.dataframe(df_f[["data_hora", "produto_nome", "quantidade", "responsavel_retirada", "observacao"]], use_container_width=True)
            else:
                st.subheader("🔍 Filtros de Consulta")
                f1, f2, f3 = st.columns(3)
                with f1:
                    t_f = st.selectbox("Tipo:", ["Todos", "Entrada", "Saída"])
                with f2:
                    p_f = st.selectbox("Paciente:", ["Todos"] + df_pac["nome_paciente"].tolist())
                with f3:
                    e_f = st.selectbox("Enfermeiro de Referência:", ["Todos"] + sorted(list(df_pac["enfermeiro_referencia"].unique())))

                df_f = df_mov.copy()
                if t_f != "Todos":
                    df_f = df_f[df_f["tipo_movimentacao"] == t_f]
                if p_f != "Todos":
                    df_f = df_f[df_f["paciente_nome"] == p_f]
                if e_f != "Todos":
                    df_f = df_f[df_f["enfermeiro_referencia"] == e_f]

                st.write(f"Exibindo **{len(df_f)}** registro(s):")
                st.dataframe(df_f, use_container_width=True)

                csv_hist = df_f.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Baixar Histórico Filtrado (Excel/CSV)", data=csv_hist, file_name="historico_farmacia.csv", mime="text/csv")
