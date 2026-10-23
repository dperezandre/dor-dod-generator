# ⚙️ Gerador DoR/DoD - Azure DevOps

Painel Streamlit que transforma relatos de dores do time, retrospectivas e bugs de produção em critérios acionáveis de **DoR** e **DoD**, com um bloco pronto para colar no Azure DevOps. Sem banco de dados: tudo em tempo real e em memória.

## Recursos
- Análise de causa raiz (Refinamento/DoR vs. Execução/DoD)
- Checklists de DoR e DoD com papéis (`[PO]`, `[Tech Lead]`, `[QA]`...)
- Bloco copia-e-cola com botão de copiar
- Seletor de tipo de relato e camadas envolvidas
- Download do resultado em `.md`
- Histórico da sessão (somente em memória)

## Rodando localmente
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=sua-chave   # PowerShell: $env:GEMINI_API_KEY = "sua-chave"
streamlit run app.py
```
Chave gratuita: https://aistudio.google.com/apikey

## Deploy (Streamlit Community Cloud)
1. Acesse https://share.streamlit.io e faça login com o GitHub.
2. **Create app** → repositório `dor-dod-generator`, branch `main`, arquivo `app.py`.
3. Em **Advanced settings → Secrets**, adicione:
   ```toml
   GEMINI_API_KEY = "sua-chave"
   ```
4. **Deploy**. A cada `git push` o app atualiza sozinho.

> A chave nunca vai para o repositório (`.streamlit/secrets.toml` está no `.gitignore`).
