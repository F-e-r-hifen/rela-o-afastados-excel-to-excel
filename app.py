import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Cálculo de Benefícios",
    page_icon="💰",
    layout="wide"
)

# Título
st.title("💰 Sistema de Cálculo de Benefícios")
st.markdown("---")

# Função para contar dias úteis
def contar_dias_uteis(data_inicio, data_fim, feriados=[]):
    """
    Conta dias úteis entre duas datas, excluindo sábados, domingos e feriados
    A data de retorno NÃO é contada (pessoa retorna nesse dia)
    """
    if pd.isna(data_inicio) or pd.isna(data_fim):
        return 0

    # Se data_inicio == data_fim, é declaração de comparecimento (0 dias)
    if data_inicio.date() == data_fim.date():
        return 0

    dias_uteis = 0
    data_atual = data_inicio

    # Contar até o dia ANTERIOR ao retorno
    while data_atual < data_fim:
        # Verificar se não é sábado (5) nem domingo (6)
        if data_atual.weekday() < 5:  # 0=segunda, 4=sexta
            # Verificar se não é feriado
            if data_atual.date() not in feriados:
                dias_uteis += 1
        data_atual += timedelta(days=1)

    return dias_uteis

# Criar descrição do afastamento
def criar_descricao_afastamento(row):
    """Cria a descrição do afastamento"""
    if row['DIAS_UTEIS_DESCONTO'] == 0:
        tipo = "DECLARAÇÃO DE COMPARECIMENTO"
    elif 'TRE' in str(row['CID/MOTIVO']).upper():
        tipo = "TRE"
    elif 'NOJO' in str(row['CID/MOTIVO']).upper():
        tipo = "LICENÇA NOJO"
    elif 'ALEITAMENTO' in str(row['CID/MOTIVO']).upper():
        tipo = "ALEITAMENTO MATERNO"
    else:
        tipo = "ATESTADO MÉDICO"

    data_inicio = row['DIA DO AFASTAMENTO'].strftime('%d/%m')
    data_fim = (row['DATA DO RETORNO'] - timedelta(days=1)).strftime('%d/%m/%Y')

    if row['DIAS_UTEIS_DESCONTO'] == 0:
        return f"{tipo} - {data_inicio}"
    else:
        return f"{tipo} DE {row['DIAS_UTEIS_DESCONTO']} DIAS - {data_inicio} A {data_fim}"

# Função para converter DataFrame para Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Benefícios')
    return output.getvalue()

# Sidebar para inputs
st.sidebar.header("⚙️ Configurações")

# Upload do arquivo
uploaded_file = st.sidebar.file_uploader(
    "📁 Carregar planilha de afastamentos",
    type=['xlsx', 'xls'],
    help="Faça upload da planilha com os dados de afastamentos"
)

# Dias de trabalho do mês
dias_trabalho = st.sidebar.number_input(
    "📅 Dias de trabalho no mês",
    min_value=1,
    max_value=31,
    value=21,
    help="Informe a quantidade de dias úteis de trabalho no próximo mês"
)

# Quantidade de feriados
num_feriados = st.sidebar.number_input(
    "🎉 Quantidade de feriados no mês",
    min_value=0,
    max_value=10,
    value=0,
    help="Informe quantos feriados existem no mês"
)

# Lista para armazenar feriados
feriados_list = []

if num_feriados > 0:
    st.sidebar.markdown("### 📆 Datas dos Feriados")
    for i in range(num_feriados):
        feriado = st.sidebar.date_input(
            f"Feriado {i+1}",
            key=f"feriado_{i}",
            help=f"Selecione a data do feriado {i+1}"
        )
        feriados_list.append(feriado)

# Botão de processar
processar = st.sidebar.button("🚀 Processar Dados", type="primary", use_container_width=True)

# Área principal
if uploaded_file is not None:
    if processar:
        try:
            # Carregar a planilha
            df = pd.read_excel(uploaded_file)

            # Limpar nomes das colunas
            df.columns = df.columns.str.strip()

            # Verificar se as colunas necessárias existem
            colunas_necessarias = ['FUNCIONÁRIO', 'MAT.', 'DIA DO AFASTAMENTO', 'DATA DO RETORNO', 'CID/MOTIVO']
            colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]

            if colunas_faltantes:
                st.error(f"❌ Colunas faltantes na planilha: {', '.join(colunas_faltantes)}")
            else:
                # Converter colunas de data
                df['DIA DO AFASTAMENTO'] = pd.to_datetime(df['DIA DO AFASTAMENTO'])
                df['DATA DO RETORNO'] = pd.to_datetime(df['DATA DO RETORNO'])

                # Processar cada afastamento
                df['DIAS_UTEIS_DESCONTO'] = df.apply(
                    lambda row: contar_dias_uteis(
                        row['DIA DO AFASTAMENTO'], 
                        row['DATA DO RETORNO'], 
                        feriados_list
                    ), 
                    axis=1
                )

                # Criar descrição
                df['DESCRICAO'] = df.apply(criar_descricao_afastamento, axis=1)

                # Agrupar por matrícula
                resultado = df.groupby('MAT.').agg({
                    'FUNCIONÁRIO': 'first',
                    'DIAS_UTEIS_DESCONTO': 'sum',
                    'DESCRICAO': lambda x: ' & '.join(x)
                }).reset_index()

                resultado.columns = ['MATRICULA', 'NOME', 'TOTAL_DIAS_DESCONTO', 'JUSTIFICATIVA_DESCONTO']

                # Calcular dias de direito
                resultado['DIAS_DE_DIREITO'] = dias_trabalho - resultado['TOTAL_DIAS_DESCONTO']
                resultado['DIAS_DE_DIREITO'] = resultado['DIAS_DE_DIREITO'].clip(lower=0)

                # Criar DataFrame para exibição (sem TOTAL_DIAS_DESCONTO)
                resultado_exibicao = resultado[['MATRICULA', 'NOME', 'DIAS_DE_DIREITO', 'JUSTIFICATIVA_DESCONTO']].copy()

                # Exibir resultados
                st.success(f"✅ Processamento concluído! Total de funcionários: {len(resultado)}")

                # Métricas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("👥 Total de Funcionários", len(resultado))
                with col2:
                    st.metric("📅 Dias de Trabalho", dias_trabalho)
                with col3:
                    st.metric("🎉 Feriados", num_feriados)
                with col4:
                    media_dias = resultado['DIAS_DE_DIREITO'].mean()
                    st.metric("📊 Média Dias de Direito", f"{media_dias:.1f}")

                st.markdown("---")

                # Tabs para visualização
                tab1, tab2, tab3 = st.tabs(["📋 Resultado Final", "📊 Estatísticas", "🔍 Detalhes"])

                with tab1:
                    st.subheader("Planilha de Benefícios")

                    # Filtros
                    col_filtro1, col_filtro2 = st.columns(2)
                    with col_filtro1:
                        filtro_nome = st.text_input("🔍 Filtrar por nome", "")
                    with col_filtro2:
                        filtro_mat = st.text_input("🔍 Filtrar por matrícula", "")

                    # Aplicar filtros
                    resultado_filtrado = resultado_exibicao.copy()
                    if filtro_nome:
                        resultado_filtrado = resultado_filtrado[
                            resultado_filtrado['NOME'].str.contains(filtro_nome, case=False, na=False)
                        ]
                    if filtro_mat:
                        resultado_filtrado = resultado_filtrado[
                            resultado_filtrado['MATRICULA'].astype(str).str.contains(filtro_mat, na=False)
                        ]

                    # Exibir tabela
                    st.dataframe(
                        resultado_filtrado,
                        use_container_width=True,
                        height=500
                    )

                    # Botão de download
                    excel_data = to_excel(resultado_filtrado)
                    st.download_button(
                        label="📥 Baixar Planilha (Excel)",
                        data=excel_data,
                        file_name=f"beneficios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                with tab2:
                    st.subheader("Estatísticas dos Benefícios")

                    col_stat1, col_stat2 = st.columns(2)

                    with col_stat1:
                        st.markdown("### 📊 Distribuição de Dias de Direito")
                        dist_dias = resultado['DIAS_DE_DIREITO'].value_counts().sort_index()
                        st.bar_chart(dist_dias)

                    with col_stat2:
                        st.markdown("### 📈 Estatísticas Gerais")
                        st.write(f"**Mínimo:** {resultado['DIAS_DE_DIREITO'].min()} dias")
                        st.write(f"**Máximo:** {resultado['DIAS_DE_DIREITO'].max()} dias")
                        st.write(f"**Média:** {resultado['DIAS_DE_DIREITO'].mean():.2f} dias")
                        st.write(f"**Mediana:** {resultado['DIAS_DE_DIREITO'].median():.0f} dias")

                        # Funcionários com dias completos
                        completos = len(resultado[resultado['DIAS_DE_DIREITO'] == dias_trabalho])
                        st.write(f"**Funcionários com {dias_trabalho} dias:** {completos} ({completos/len(resultado)*100:.1f}%)")

                with tab3:
                    st.subheader("Detalhes dos Afastamentos")

                    # Selecionar funcionário
                    funcionario_selecionado = st.selectbox(
                        "Selecione um funcionário para ver detalhes:",
                        options=resultado['NOME'].unique()
                    )

                    if funcionario_selecionado:
                        mat_selecionada = resultado[resultado['NOME'] == funcionario_selecionado]['MATRICULA'].iloc[0]
                        detalhes = df[df['MAT.'] == mat_selecionada]

                        st.markdown(f"### 👤 {funcionario_selecionado}")
                        st.markdown(f"**Matrícula:** {mat_selecionada}")

                        info_func = resultado[resultado['MATRICULA'] == mat_selecionada].iloc[0]
                        st.markdown(f"**Dias de Direito:** {info_func['DIAS_DE_DIREITO']}")
                        st.markdown(f"**Total de Dias Descontados:** {info_func['TOTAL_DIAS_DESCONTO']}")

                        st.markdown("---")
                        st.markdown("#### 📋 Afastamentos:")

                        for idx, row in detalhes.iterrows():
                            with st.expander(f"📅 {row['DIA DO AFASTAMENTO'].strftime('%d/%m/%Y')} - {row['DESCRICAO']}"):
                                col_det1, col_det2 = st.columns(2)
                                with col_det1:
                                    st.write(f"**Início:** {row['DIA DO AFASTAMENTO'].strftime('%d/%m/%Y')}")
                                    st.write(f"**Retorno:** {row['DATA DO RETORNO'].strftime('%d/%m/%Y')}")
                                with col_det2:
                                    st.write(f"**Dias Úteis:** {row['DIAS_UTEIS_DESCONTO']}")
                                    st.write(f"**Motivo:** {row['CID/MOTIVO']}")

        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")
            st.exception(e)
else:
    # Tela inicial
    st.info("👈 Faça upload da planilha de afastamentos na barra lateral para começar")

    st.markdown("""
    ### 📖 Como usar:

    1. **Faça upload** da planilha de afastamentos (formato Excel)
    2. **Informe** a quantidade de dias de trabalho do próximo mês
    3. **Adicione** os feriados do mês (se houver)
    4. **Clique** em "Processar Dados"
    5. **Visualize** os resultados e **baixe** a planilha final

    ### 📋 Colunas necessárias na planilha:
    - `FUNCIONÁRIO`: Nome do colaborador
    - `MAT.`: Matrícula (código único)
    - `DIA DO AFASTAMENTO`: Data de início do afastamento
    - `DATA DO RETORNO`: Data de retorno ao trabalho
    - `CID/MOTIVO`: Motivo do afastamento

    ### ⚠️ Observações importantes:
    - Sábados e domingos **não** são contados como dias de desconto
    - Feriados informados **não** são contados como dias de desconto
    - Declarações de comparecimento (mesmo dia) não geram desconto
    - Funcionários com múltiplos afastamentos terão os descontos somados
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Sistema de Cálculo de Benefícios v1.0</div>",
    unsafe_allow_html=True
)
