import os
import re
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
Você é um consultor especialista para Tech Leads e Product Owners atuando em arquiteturas modernas (Front-end, BFF, APIs .NET/Node, SQL Server/Oracle, Microsserviços e Azure DevOps).
Sua tarefa é analisar dores do time, bugs de produção e relatos de retrospectivas para gerar atualizações acionáveis para o Definition of Ready (DoR) e Definition of Done (DoD).

Contexto técnico a considerar:
- Arquitetura: Front-end + BFF + APIs .NET/Node + SQL/Oracle + Microsserviços.
- Ferramenta de gestão: Azure DevOps (PBIs / User Stories).
- Dores comuns a combater: Histórias mal especificadas, quebra de contratos de API, bugs de regressão em produção e falta de testes adequados.

Sua resposta DEVE seguir rigorosamente esta estrutura em Markdown:

### 1. 🔍 Análise de Causa Raiz
Breve diagnóstico da falha no fluxo (Refinamento/DoR vs. Execução/DoD).

### 2. 📋 Itens Sugeridos para o DoR (Definition of Ready)
Checklist Markdown com atribuição de papéis entre colchetes (ex: [PO], [Tech Lead], [Front-end]).

### 3. ⚙️ Itens Sugeridos para o DoD (Definition of Done)
Checklist Markdown com atribuição de papéis entre colchetes (ex: [Dev], [QA], [Tech Lead]).

### 4. 📌 Bloco Copia-e-Cola para o Azure DevOps
Bloco de código Markdown isolado (code block) contendo o DoR e DoD limpos e prontos para serem colados direto no Azure DevOps.
""".strip()

TIPOS_RELATO = [
    "Retrospectiva",
    "Bug de produção",
    "Dor de refinamento / histórias mal especificadas",
    "Quebra de contrato de API",
    "Outro",
]

STACKS = ["Front-end", "BFF", "API .NET", "API Node", "SQL Server", "Oracle", "Microsserviços"]


def get_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def build_user_prompt(relato: str, tipo: str, stacks: list[str]) -> str:
    partes = [f"Tipo do relato: {tipo}"]
    if stacks:
        partes.append(f"Camadas/tecnologias envolvidas: {', '.join(stacks)}")
    partes.append(f"Relato:\n{relato.strip()}")
    return "\n\n".join(partes)


def extract_copy_block(markdown: str) -> str | None:
    """Retorna o conteúdo do último bloco de código da resposta (seção 4)."""
    blocos = re.findall(r"```[^\n]*\n(.*?)```", markdown, flags=re.DOTALL)
    return blocos[-1].strip() if blocos else None


def generate(api_key: str, relato: str, tipo: str, stacks: list[str]) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL,
        contents=build_user_prompt(relato, tipo, stacks),
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    if not response.text:
        raise RuntimeError("O Gemini retornou uma resposta vazia. Tente reformular o relato.")
    return response.text


def render_result(markdown: str, key: str) -> None:
    st.markdown(markdown)
    bloco = extract_copy_block(markdown)
    if bloco:
        st.caption("📋 Use o ícone de copiar no canto do bloco abaixo para colar no Azure DevOps:")
        st.code(bloco, language="markdown")
    st.download_button(
        "⬇️ Baixar resultado (.md)",
        data=markdown,
        file_name="dor-dod.md",
        mime="text/markdown",
        key=f"dl_{key}",
    )


st.set_page_config(page_title="Gerador DoR/DoD - Azure DevOps", page_icon="⚙️", layout="wide")

st.title("⚙️ Gerador DoR/DoD - Azure DevOps")
st.markdown(
    "Cole abaixo relatos de **dores do time**, **problemas de retrospectiva** ou **bugs de produção**. "
    "A ferramenta analisa a causa raiz e gera critérios acionáveis de **DoR (Definition of Ready)** e "
    "**DoD (Definition of Done)**, prontos para copiar e colar nos PBIs / User Stories do Azure DevOps."
)

api_key = get_api_key()
if not api_key:
    st.error(
        "🔑 A variável de ambiente `GEMINI_API_KEY` não foi encontrada.\n\n"
        "**Local (PowerShell):** `$env:GEMINI_API_KEY = \"sua-chave\"` e rode `streamlit run app.py`.\n\n"
        "**Local (Linux/macOS):** `export GEMINI_API_KEY=sua-chave`.\n\n"
        "**Streamlit Community Cloud:** em *App settings → Secrets* adicione `GEMINI_API_KEY = \"sua-chave\"`.\n\n"
        "Gere uma chave gratuita em https://aistudio.google.com/apikey."
    )
    st.stop()

if "historico" not in st.session_state:
    st.session_state.historico = []

col_tipo, col_stack = st.columns([1, 2])
with col_tipo:
    tipo = st.selectbox("Tipo de relato", TIPOS_RELATO)
with col_stack:
    stacks = st.multiselect("Camadas envolvidas (opcional)", STACKS)

relato = st.text_area(
    "Relato das dores",
    height=280,
    placeholder="Ex.: Na última sprint, a mudança no contrato da API de pedidos quebrou o BFF em produção "
    "porque o front não foi avisado e não havia teste de contrato...",
)

if st.button("Gerar DoR / DoD", type="primary"):
    if not relato.strip():
        st.warning("Cole ao menos um relato antes de gerar.")
    else:
        try:
            with st.spinner("Analisando o relato com o Gemini..."):
                resultado = generate(api_key, relato, tipo, stacks)
            st.session_state.historico.insert(
                0,
                {
                    "hora": datetime.now().strftime("%H:%M:%S"),
                    "tipo": tipo,
                    "relato": relato.strip(),
                    "resultado": resultado,
                },
            )
            st.session_state.atual = resultado
        except Exception as e:
            st.error(f"Falha ao chamar a API do Gemini: {e}")

if st.session_state.get("atual"):
    st.divider()
    render_result(st.session_state.atual, "atual")

if st.session_state.historico:
    with st.sidebar:
        st.subheader("🕘 Histórico da sessão")
        st.caption("Apenas em memória: some ao recarregar a página.")
        for i, item in enumerate(st.session_state.historico):
            resumo = item["relato"][:45] + ("…" if len(item["relato"]) > 45 else "")
            if st.button(f"{item['hora']} · {item['tipo']}\n{resumo}", key=f"hist_{i}", use_container_width=True):
                st.session_state.atual = item["resultado"]
                st.rerun()
        if st.button("🗑️ Limpar histórico", use_container_width=True):
            st.session_state.historico = []
            st.session_state.pop("atual", None)
            st.rerun()
