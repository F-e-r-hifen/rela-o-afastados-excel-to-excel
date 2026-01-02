# 💰 Sistema de Cálculo de Benefícios

Sistema web para cálculo automático de benefícios (V.A e V.T) baseado em dias de trabalho e afastamentos.

## 🚀 Como usar localmente

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute o aplicativo:
```bash
streamlit run app.py
```

3. Acesse no navegador: `http://localhost:8501`

## 📦 Deploy no Streamlit Cloud

1. Faça upload dos arquivos `app.py` e `requirements.txt` para um repositório GitHub
2. Acesse [Streamlit Cloud](https://streamlit.io/cloud)
3. Conecte seu repositório GitHub
4. Selecione o arquivo `app.py` como main file
5. Clique em "Deploy"

## 📋 Funcionalidades

- ✅ Upload de planilha Excel com dados de afastamentos
- ✅ Configuração de dias de trabalho do mês
- ✅ Adição de múltiplos feriados
- ✅ Cálculo automático de dias úteis (excluindo sábados, domingos e feriados)
- ✅ Agrupamento de múltiplos afastamentos por funcionário
- ✅ Filtros por nome e matrícula
- ✅ Visualização de estatísticas
- ✅ Detalhes individuais por funcionário
- ✅ Download da planilha processada em Excel

## 📊 Formato da Planilha de Entrada

A planilha deve conter as seguintes colunas:

- `FUNCIONÁRIO`: Nome do colaborador
- `MAT.`: Matrícula (código único de 3 ou 4 dígitos)
- `DIA DO AFASTAMENTO`: Data de início do afastamento
- `DATA DO RETORNO`: Data de retorno ao trabalho
- `CID/MOTIVO`: Motivo do afastamento (CID, TRE, Licença Nojo, etc.)

## 📤 Saída

O sistema gera uma planilha com:

- `MATRICULA`: Código do funcionário
- `NOME`: Nome do funcionário
- `DIAS_DE_DIREITO`: Quantidade de dias de benefício a pagar
- `JUSTIFICATIVA_DESCONTO`: Descrição detalhada dos afastamentos

## ⚠️ Observações

- Sábados e domingos **não** são contados como dias de desconto
- Feriados informados **não** são contados como dias de desconto
- Declarações de comparecimento (mesmo dia) não geram desconto
- Funcionários com múltiplos afastamentos terão os descontos somados automaticamente

## 🛠️ Tecnologias

- Python 3.8+
- Streamlit
- Pandas
- OpenPyXL
- NumPy

## 📝 Licença

Este projeto é de uso interno.
