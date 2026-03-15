# 📁 Pasta .streamlit

Esta pasta contém configurações específicas do Streamlit.

## 🔐 secrets.toml

**IMPORTANTE:** Este arquivo contém credenciais sensíveis e **NÃO deve ser commitado** no repositório.

O arquivo `secrets.toml` deve conter:
- `GROQ_API_KEY`: Chave da API Groq para fallback
- `TUNNEL_URL`: URL do túnel Ngrok para LM Studio
- `SUPABASE_URL`: URL do projeto Supabase (opcional)
- `SUPABASE_ANON_KEY`: Chave anônima do Supabase (opcional)

### Como configurar:
1. Copie `secrets.example.toml` para `.streamlit/secrets.toml`
2. Preencha com suas credenciais reais
3. O arquivo será automaticamente ignorado pelo `.gitignore`

### Segurança:
- ✅ O `.gitignore` protege este arquivo
- ✅ Nunca commite credenciais reais
- ✅ Use sempre o arquivo de exemplo como template