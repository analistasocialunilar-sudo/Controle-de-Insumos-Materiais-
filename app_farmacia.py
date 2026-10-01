import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import urllib.parse

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E BANCO DE DADOS (SQLite)
# ==============================================================================
st.set_page_config(
    page_title="Gestão de Farmácia - Assistência Domiciliar",
    page_icon="💊",
    layout="wide"
)

# Conexão com o Banco de Dados SQLite
DB_NAME = "estoque_farmacia.db"

def init_db():
    """Cria as tabelas do sistema se ainda não existirem."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de Produtos (Medicamentos, Insumos, Equipamentos)
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

    # Tabela de Pacientes e Enfermeiros
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_paciente TEXT NOT NULL,
            enfermeiro_referencia TEXT NOT NULL,
            responsavel_familia TEXT
        )
    ''')

    # Tabela de Movimentações (Entradas, Saídas/Dispensações e Contagens)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            tipo_movimentacao TEXT NOT NULL, -- Entrada ou Saída
            produto_id INTEGER NOT NULL,
            produto_nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            paciente_nome TEXT,
            enfermeiro_referencia TEXT,
            responsavel_retirada TEXT,
            observacao TEXT,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')

    conn.commit()
    conn.close()

# Inicializa as tabelas ao carregar a aplicação
init_db()

# ==============================================================================
# 2. SISTEMA DE AUTENTICAÇÃO E PERFIS DE ACESSO
# ==============================================================================
# Usuários cadastrados (Podem ser expandidos no banco futuramente)
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

# Tela de Login se não estiver autenticado
if not st.session_state["autenticado"]:
    st.title("💊 Gestão de Farmácia e Insumos - Assistência Domiciliar")
    st.subheader("🔐 Acesso ao Sistema")
    
    with st.form("form_login"):
        u_input = st.text_input("Utilizador").strip().lower()
        p_input = st.text_input("Palavra-passe", type="password")
        btn_login = st.form_submit_button("Entrar")
        
        if btn_login:
            realizar_login(u_input, p_input)
            
    st.info("💡 **Perfis de Teste:**\n- **Farmácia/Admin:** `farmacia` (Senha: `123`) ou `admin` (Senha: `admin`)\n- **Família/Cuidador:** `familia` (Senha: `789`) | **Enfermeiro:** `enfermeiro` (Senha: `456`)")
    st.stop()

# ==============================================================================
# 3. CABEÇALHO DO SISTEMA E NAVEGAÇÃO POR PERFIL
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

# Definição das abas por perfil de acesso
perfil = st.session_state["usuario_perfil"]

if perfil in ["Equipa da Farmácia", "Administrador"]:
    abas_nomes = [
        "📊 1. Painel & Alertas", 
        "📦 2. Entradas & Lista de Compras", 
        "🤝 3. Dispensação (Saídas)", 
        "📋 4. Histórico & Pacientes"
    ]
elif perfil == "Enfermeiro de Referência":
    abas_nomes = [
        "📊 1. Painel & Alertas", 
        "🤝 3. Dispensação (Saídas)", 
        "📋 4. Histórico & Pacientes"
    ]
else:  # Cuidador / Família
    abas_nomes = [
        "📋 Consulta & Dispensações do Paciente"
    ]

abas = st.tabs(abas_nomes)

# Helper para conectar ao BD
def get_connection():
    return sqlite3.connect(DB_NAME)

# ==============================================================================
# ABA 1: PAINEL GERAL & ALERTAS DE ESTOQUE MÍNIMO
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
            # Produtos com estoque crítico (Abaixo ou igual ao mínimo)
            df_criticos = df_produtos[df_produtos["quantidade_atual"] <= df_produtos["quantidade_minima"]]

            # Indicadores Topo
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total de Itens Cadastrados", len(df_produtos))
            col2.metric("Itens com Estoque OK", len(df_produtos) - len(df_criticos))
            col3.metric("⚠️ Itens Críticos (Repor)", len(df_criticos), delta_color="inverse")
            col4.metric("Total de Dispensações", len(df_mov[df_mov["tipo_movimentacao"] == "Saída"]))

            st.divider()

            # Alerta de Estoque Crítico
            if not df_criticos.empty:
                st.error("🚨 **ALERTAS DE ESTOQUE MÍNIMO ATINGIDO / NECESSIDADE DE COMPRA:**")
                st.dataframe(
                    df_criticos[["nome", "categoria", "quantidade_atual", "quantidade_minima", "unidade_medida"]],
                    use_container_width=True
                )
            else:
                st.success("✅ Todos os itens estão com níveis de estoque adequados!")

            st.subheader("📦 Lista Completa de Saldo Atual")
            st.dataframe(df_produtos, use_container_width=True)

# ==============================================================================
# ABA 2: ENTRADAS NO ESTOQUE & GERAÇÃO DE LISTA DE COMPRAS
# ==============================================================================
if "📦 2. Entradas & Lista de Compras" in abas_nomes:
    idx = abas_nomes.index("📦 2. Entradas & Lista de Compras")
    with abas[idx]:
        st.header("📦 Gestão de Entradas e Compras")
        
        col_cad, col_ent = st.columns(2)

        conn = get_connection()
        df_produtos = pd.read_sql_query("SELECT * FROM produtos", conn)
        
        # Formulário 1: Cadastrar Novo Item no Estoque
        with col_cad:
            st.subheader("➕ Cadastrar Novo Medicamento / Insumo")
            with st.form("form_novo_produto"):
                nome_p = st.text_input("Nome do Item / Medicamento *", placeholder="Ex: Soro Fisiológico 0,9% 500ml")
                cat_p = st.selectbox("Categoria *", ["Medicamento", "Insumo / Curativo", "Equipamento", "Dieta / Nutrição", "Outros"])
                qtd_ini = st.number_input("Quantidade Inicial em Estoque", min_value=0, value=0)
                qtd_min = st.number_input("Quantidade Mínima (Estoque Crítico) *", min_value=1, value=10)
                unidade = st.selectbox("Unidade de Medida *", ["Frasco", "Caixa", "Unidade", "Ampola", "Pacote", "Rolo"])
                
                btn_cad_prod = st.form_submit_button("💾 Cadastrar Produto")

            if btn_cad_prod:
                if not nome_p.strip():
                    st.error("O nome do item é obrigatório.")
                else:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO produtos (nome, categoria, quantidade_atual, quantidade_minima, unidade_medida) VALUES (?, ?, ?, ?, ?)",
                        (nome_p.strip(), cat_p, qtd_ini, qtd_min, unidade)
                    )
                    conn.commit()
                    st.success(f"✅ '{nome_p}' cadastrado com sucesso!")
                    st.rerun()

        # Formulário 2: Registrar Entrada de Lote/Compra
        with col_ent:
            st.subheader("📥 Registrar Entrada de Nota / Reposição")
            if df_produtos.empty:
                st.info("Cadastre pelo menos um produto ao lado primeiro.")
            else:
                with st.form("form_entrada_estoque"):
                    prod_sel = st.selectbox("Selecione o Item para Dar Entrada", df_produtos["nome"].tolist())
                    qtd_entrada = st.number_input("Quantidade Recebida", min_value=1, value=1)
                    obs_entrada = st.text_input("Observação / Nº da Nota / Fornecedor", placeholder="Ex: NF 1234 - Distribuidora Health")
                    
                    btn_dar_entrada = st.form_submit_button("📥 Confirmar Entrada")

                if btn_dar_entrada:
                    p_id = df_produtos[df_produtos["nome"] == prod_sel]["id"].values[0]
                    qtd_atual = df_produtos[df_produtos["nome"] == prod_sel]["quantidade_atual"].values[0]
                    nova_qtd = qtd_atual + qtd_entrada

                    cursor = conn.cursor()
                    cursor.execute("UPDATE produtos SET quantidade_atual = ? WHERE id = ?", (nova_qtd, p_id))
                    
                    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute('''
                        INSERT INTO movimentacoes (data_hora, tipo_movimentacao, produto_id, produto_nome, quantidade, observacao)
                        VALUES (?, 'Entrada', ?, ?, ?, ?)
                    ''', (data_hoje, p_id, prod_sel, qtd_entrada, obs_entrada))

                    conn.commit()
                    st.success(f"✅ +{qtd_entrada} unidades adicionadas ao item '{prod_sel}'!")
                    st.rerun()

        conn.close()

        st.divider()

        # GERADOR DE LISTA DE COMPRAS
        st.subheader("🛒 Gerador de Lista de Compras / Pedido de Insumos")
        conn = get_connection()
        df_prod_compra = pd.read_sql_query("SELECT * FROM produtos WHERE quantidade_atual <= quantidade_minima", conn)
        conn.close()

        if df_prod_compra.empty:
            st.success("🎉 Não há necessidade de compras no momento! Todos os itens estão acima do mínimo.")
        else:
            df_prod_compra["Sugestão de Compra"] = df_prod_compra["quantidade_minima"] * 2 - df_prod_compra["quantidade_atual"]
            st.write("Abaixo estão os itens que atingiram o estoque mínimo com sugestão de quantidade para pedido:")
            st.dataframe(df_prod_compra[["nome", "categoria", "quantidade_atual", "quantidade_minima", "Sugestão de Compra", "unidade_medida"]], use_container_width=True)

            # Exportação formatada para Excel/CSV (separado por ';')
            csv_compras = df_prod_compra.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar Lista de Compras em Excel/CSV Organizado",
                data=csv_compras,
                file_name=f"lista_de_compras_farmacia_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# ==============================================================================
# ABA 3: DISPENSAÇÃO / RETIRADA POR PACIENTE E ENFERMEIRO DE REFERÊNCIA
# ==============================================================================
if "🤝 3. Dispensação (Saídas)" in abas_nomes:
    idx = abas_nomes.index("🤝 3. Dispensação (Saídas)")
    with abas[idx]:
        st.header("🤝 Registro de Saída / Dispensação Mensal para Domicílio")

        conn = get_connection()
        df_produtos = pd.read_sql_query("SELECT * FROM produtos WHERE quantidade_atual > 0", conn)
        df_pacientes = pd.read_sql_query("SELECT * FROM pacientes", conn)
        
        # Cadastro rápido de pacientes se a lista estiver vazia
        with st.expander("👤 Gerenciar / Cadastrar Paciente & Enfermeiro de Referência"):
            with st.form("form_cad_paciente"):
                c_p1, c_p2, c_p3 = st.columns(3)
                nome_pac = c_p1.text_input("Nome Completo do Paciente *")
                enf_ref = c_p2.selectbox("Enfermeiro(a) de Referência *", ["Enfª. Juliana Costa", "Enf. Rodrigo Alves", "Enfª. Camila Lima", "Enf. Marcelo Silva"])
                resp_fam = c_p3.text_input("Cuidador / Responsável Principal", placeholder="Ex: Maria (Esposa)")
                
                btn_pac = st.form_submit_button("💾 Salvar Paciente")
                if btn_pac:
                    if nome_pac.strip():
                        c_pac = conn.cursor()
                        c_pac.execute("INSERT INTO pacientes (nome_paciente, enfermeiro_referencia, responsavel_familia) VALUES (?, ?, ?)",
                                      (nome_pac.strip(), enf_ref, resp_fam))
                        conn.commit()
                        st.success("Paciente cadastrado com sucesso!")
                        st.rerun()

        st.divider()

        if df_produtos.empty:
            st.error("⚠️ Não há produtos disponíveis em estoque para saída.")
        else:
            lista_pacientes = df_pacientes["nome_paciente"].tolist() if not df_pacientes.empty else ["➕ Cadastrar na opção acima"]
            
            with st.form("form_dispensacao"):
                st.subheader("📋 Formulario de Saída de Insumos")
                col1, col2 = st.columns(2)

                with col1:
                    pac_selecionado = st.selectbox("Paciente *", lista_pacientes)
                    
                    # Identifica o enfermeiro associado automaticamente
                    enf_associado = "Não especificado"
                    if not df_pacientes.empty and pac_selecionado in df_pacientes["nome_paciente"].values:
                        enf_associado = df_pacientes[df_pacientes["nome_paciente"] == pac_selecionado]["enfermeiro_referencia"].values[0]
                    
                    st.info(f"👨‍⚕️ **Enfermeiro de Referência:** {enf_associado}")

                    item_disp = st.selectbox("Medicamento / Insumo Solicitado *", df_produtos["nome"].tolist())
                    
                    # Pega a quantidade disponível
                    qtd_disp = df_produtos[df_produtos["nome"] == item_disp]["quantidade_atual"].values[0]
                    unid_disp = df_produtos[df_produtos["nome"] == item_disp]["unidade_medida"].values[0]
                    st.caption(f"Saldo atual em farmácia: **{qtd_disp} {unid_disp}**")

                with col2:
                    qtd_retirada = st.number_input(f"Quantidade Entregue ({unid_disp}) *", min_value=1, max_value=int(qtd_disp), value=1)
                    nome_retirou = st.text_input("Nome de Quem Retirou (Cuidador/Familiar) *", placeholder="Ex: Carlos (Filho do paciente)")
                    obs_disp = st.text_area("Observações da Contagem / Domicílio", placeholder="Ex: Entregue referente ao mês de Outubro. Família relatou ter 2 unidades em casa.")

                btn_confirmar_saida = st.form_submit_button("✅ Salvar e Registar Saída")

            if btn_confirmar_saida:
                if not nome_retirou.strip():
                    st.error("⚠️ Digite o nome do responsável que retirou o material.")
                else:
                    p_id = df_produtos[df_produtos["nome"] == item_disp]["id"].values[0]
                    nova_qtd = qtd_disp - qtd_retirada

                    cursor = conn.cursor()
                    # 1. Atualiza estoque na farmácia
                    cursor.execute("UPDATE produtos SET quantidade_atual = ? WHERE id = ?", (nova_qtd, p_id))
                    
                    # 2. Regista movimentação detalhada
                    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute('''
                        INSERT INTO movimentacoes (
                            data_hora, tipo_movimentacao, produto_id, produto_nome, quantidade,
                            paciente_nome, enfermeiro_referencia, responsavel_retirada, observacao
                        ) VALUES (?, 'Saída', ?, ?, ?, ?, ?, ?, ?)
                    ''', (data_hoje, p_id, item_disp, qtd_retirada, pac_selecionado, enf_associado, nome_retirou.strip(), obs_disp))

                    conn.commit()
                    st.success(f"✅ Saída de {qtd_retirada}x {item_disp} registrada para o paciente {pac_selecionado} com sucesso!")
                    st.rerun()

        conn.close()

# ==============================================================================
# ABA 4: HISTÓRICO COMPLETO & CONSULTA FAMILIAR
# ==============================================================================
if "📋 4. Histórico & Pacientes" in abas_nomes or "📋 Consulta & Dispensações do Paciente" in abas_nomes:
    # Seleção da aba ativa
    aba_idx = 0 if perfil == "Cuidador / Família" else abas_nomes.index("📋 4. Histórico & Pacientes")
    
    with abas[aba_idx]:
        st.header("📋 Histórico de Movimentações e Relatórios")

        conn = get_connection()
        df_mov = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY id DESC", conn)
        df_pac = pd.read_sql_query("SELECT * FROM pacientes", conn)
        conn.close()

        if df_mov.empty:
            st.info("Nenhuma movimentação realizada até o momento.")
        else:
            # Se for perfil de família, permite filtrar apenas o seu paciente
            if perfil == "Cuidador / Família":
                st.subheader("🔍 Consultar Medicamentos/Insumos Entregues ao Paciente")
                lista_p = df_pac["nome_paciente"].tolist() if not df_pac.empty else []
                pac_filtro = st.selectbox("Selecione o Paciente:", lista_p)
                
                df_filtrado = df_mov[df_mov["paciente_nome"] == pac_filtro]
                st.dataframe(df_filtrado[["data_hora", "produto_nome", "quantidade", "responsavel_retirada", "observacao"]], use_container_width=True)

            else:
                st.subheader("🔍 Filtros Globais")
                f1, f2, f3 = st.columns(3)
                
                with f1:
                    tipo_f = st.selectbox("Tipo de Movimentação:", ["Todos", "Entrada", "Saída"])
                with f2:
                    pacs_unicos = ["Todos"] + sorted(list(df_mov["paciente_nome"].dropna().unique()))
                    pac_f = st.selectbox("Filtrar por Paciente:", pacs_unicos)
                with f3:
                    enfs_unicos = ["Todos"] + sorted(list(df_mov["enfermeiro_referencia"].dropna().unique()))
                    enf_f = st.selectbox("Filtrar por Enfermeiro de Referência:", enfs_unicos)

                df_filtrado = df_mov.copy()

                if tipo_f != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["tipo_movimentacao"] == tipo_f]
                if pac_f != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["paciente_nome"] == pac_f]
                if enf_f != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["enfermeiro_referencia"] == enf_f]

                st.write(f"Exibindo **{len(df_filtrado)}** registo(s):")
                st.dataframe(df_filtrado, use_container_width=True)

                # Exportação para Excel/CSV Organizado por ';'
                csv_mov = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 Baixar Histórico Filtrado (Excel / CSV Organizado)",
                    data=csv_mov,
                    file_name=f"historico_farmacia_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
