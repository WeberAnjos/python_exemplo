import streamlit as st
import importlib.util
import os
import sys

st.set_page_config(page_title="Dashboard Integrado IBGE", layout="wide")

# Caminho base da pasta onde o main.py está
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mapeamento exato baseado na sua estrutura de pastas
PROJETOS = {
    "Antônio - Indígenas": os.path.join(BASE_DIR, "antonio", "Projeto-Integrado-Individual", "app.py"),
    "Josué": os.path.join(BASE_DIR, "josue", "josue.py"),
    "Lucas A - Mulheres": os.path.join(BASE_DIR, "lucasA", "Projeto-Integrado", "modulo_mulheres.py"),
    "Lucas R - Alfabetização": os.path.join(BASE_DIR, "lucasR", "Projeto-Integrado", "app.py"),
    "Weber - População": os.path.join(BASE_DIR, "weber", "dashboard.py"),
}

def carregar_e_executar(caminho_arquivo):
    pasta_projeto = os.path.dirname(caminho_arquivo)
    
    # Adiciona a pasta do aluno ao sistema para que imports internos (como a pasta 'src' do Lucas R) funcionem
    if pasta_projeto not in sys.path:
        sys.path.insert(0, pasta_projeto)
    
    # Muda temporariamente o diretório de trabalho para a pasta do aluno (resolve problemas com caminhos de CSV)
    diretorio_original = os.getcwd()
    os.chdir(pasta_projeto)
    
    try:
        spec = importlib.util.spec_from_file_location("modulo_aluno", caminho_arquivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        
        # Se o aluno criou uma função principal, ela será chamada. Se o código estiver solto, ele já rodou acima.
        if hasattr(modulo, "main"):
            modulo.main()
        elif hasattr(modulo, "rodar_dashboard"):
            modulo.rodar_dashboard()
            
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
    finally:
        # Volta para a pasta raiz para não quebrar o próximo projeto selecionado
        os.chdir(diretorio_original)

# --- MENU LATERAL ---
st.sidebar.title("📊 Projetos IBGE")
escolha = st.sidebar.radio("Selecione o dashboard:", list(PROJETOS.keys()))

st.sidebar.divider()
st.sidebar.info("Navegue pelos módulos individuais acima.")

# Executa o projeto escolhido
carregar_e_executar(PROJETOS[escolha])
