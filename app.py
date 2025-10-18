import streamlit as st
import os
import json
from pathlib import Path
import base64
from datetime import datetime
import PyPDF2
import io

# Configuração da página
st.set_page_config(
    page_title="Assistente de Leitura",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Diretórios para armazenamento
BASE_DIR = Path("data")
USERS_DIR = BASE_DIR / "users"
DOCS_DIR = BASE_DIR / "documents"
VOICE_DIR = BASE_DIR / "voices"

# Criar diretórios se não existirem
for dir_path in [USERS_DIR, DOCS_DIR, VOICE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# CSS personalizado para design responsivo e limpo
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .file-card {
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    
    .word-tooltip {
        background: #fff3cd;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 3px solid #ffc107;
    }
    
    .stButton>button {
        width: 100%;
        background: #667eea;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    
    .stButton>button:hover {
        background: #764ba2;
    }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares
def load_users():
    """Carrega usuários do arquivo JSON"""
    users_file = USERS_DIR / "users.json"
    if users_file.exists():
        with open(users_file, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Salva usuários no arquivo JSON"""
    users_file = USERS_DIR / "users.json"
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=4)

def authenticate(username, password):
    """Autentica usuário"""
    users = load_users()
    if username in users and users[username]['password'] == password:
        return True
    return False

def register_user(username, password, email):
    """Registra novo usuário"""
    users = load_users()
    if username in users:
        return False, "Usuário já existe"
    
    users[username] = {
        'password': password,
        'email': email,
        'created_at': datetime.now().isoformat(),
        'has_voice': False
    }
    save_users(users)
    
    # Criar pasta do usuário
    user_dir = DOCS_DIR / username
    user_dir.mkdir(exist_ok=True)
    
    return True, "Usuário registrado com sucesso!"

def get_user_documents(username):
    """Retorna lista de documentos do usuário"""
    user_dir = DOCS_DIR / username
    if not user_dir.exists():
        return []
    
    docs = []
    for file_path in user_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in ['.pdf', '.docx', '.txt']:
            docs.append({
                'name': file_path.name,
                'path': str(file_path),
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%d/%m/%Y %H:%M')
            })
    return docs

def extract_text_from_pdf(pdf_file):
    """Extrai texto de um arquivo PDF"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def get_word_definition_link(word):
    """Retorna link para dicionário online"""
    return f"https://www.dicio.com.br/{word.lower()}"

# Inicializar session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'
if 'selected_doc' not in st.session_state:
    st.session_state.selected_doc = None

# ============================================
# PÁGINA 1: LOGIN E CADASTRO
# ============================================
def login_page():
    st.markdown('<div class="main-header"><h1>📚 Assistente de Leitura</h1><p>Suporte personalizado para leitura</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Cadastro"])
        
        with tab1:
            st.subheader("Fazer Login")
            username = st.text_input("Usuário", key="login_user")
            password = st.text_input("Senha", type="password", key="login_pass")
            
            if st.button("Entrar", key="login_btn"):
                if authenticate(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.current_page = 'home'
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos")
        
        with tab2:
            st.subheader("Criar Conta")
            new_username = st.text_input("Usuário", key="reg_user")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Senha", type="password", key="reg_pass")
            new_password_confirm = st.text_input("Confirmar Senha", type="password", key="reg_pass_confirm")
            
            if st.button("Cadastrar", key="register_btn"):
                if not new_username or not new_password:
                    st.error("❌ Preencha todos os campos")
                elif new_password != new_password_confirm:
                    st.error("❌ As senhas não coincidem")
                elif len(new_password) < 6:
                    st.error("❌ A senha deve ter pelo menos 6 caracteres")
                else:
                    success, message = register_user(new_username, new_password, new_email)
                    if success:
                        st.success(f"✅ {message}")
                        st.info("Agora você pode fazer login!")
                    else:
                        st.error(f"❌ {message}")

# ============================================
# PÁGINA 2: CADASTRO DE VOZ
# ============================================
def voice_setup_page():
    st.title("🎤 Configuração de Voz")
    st.write("Grave sua voz para personalizar a experiência de leitura")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Gravar Amostra de Voz")
        st.info("📝 Leia o texto abaixo em voz alta para criar sua amostra de voz:")
        
        st.markdown("""
        > *"A leitura é uma fonte inesgotável de conhecimento e prazer. 
        > Cada livro é uma nova aventura, cada página uma descoberta."*
        """)
        
        # Simulação de gravação (em produção, use uma biblioteca de áudio)
        audio_file = st.file_uploader("Ou faça upload de um arquivo de áudio", type=['mp3', 'wav', 'ogg'])
        
        if audio_file:
            st.audio(audio_file)
            
            if st.button("💾 Salvar Amostra de Voz"):
                # Salvar arquivo de áudio
                voice_path = VOICE_DIR / f"{st.session_state.username}_voice.wav"
                with open(voice_path, 'wb') as f:
                    f.write(audio_file.getbuffer())
                
                # Atualizar usuário
                users = load_users()
                users[st.session_state.username]['has_voice'] = True
                save_users(users)
                
                st.success("✅ Voz cadastrada com sucesso!")
                st.balloons()
    
    with col2:
        st.subheader("Status")
        users = load_users()
        has_voice = users.get(st.session_state.username, {}).get('has_voice', False)
        
        if has_voice:
            st.success("✅ Voz cadastrada")
            if st.button("🔄 Gravar novamente"):
                users[st.session_state.username]['has_voice'] = False
                save_users(users)
                st.rerun()
        else:
            st.warning("⚠️ Voz não cadastrada")

# ============================================
# PÁGINA 3: GERENCIAMENTO DE DOCUMENTOS
# ============================================
def documents_page():
    st.title("📁 Meus Documentos")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Upload de Arquivos")
        
        uploaded_files = st.file_uploader(
            "Selecione documentos (PDF, DOCX, TXT)",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                user_dir = DOCS_DIR / st.session_state.username
                file_path = user_dir / uploaded_file.name
                
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ {len(uploaded_files)} arquivo(s) enviado(s) com sucesso!")
            st.rerun()
    
    with col2:
        st.subheader("Ações")
        if st.button("🔄 Atualizar Lista"):
            st.rerun()
    
    st.divider()
    
    # Lista de documentos
    st.subheader("📚 Biblioteca")
    docs = get_user_documents(st.session_state.username)
    
    if not docs:
        st.info("Nenhum documento encontrado. Faça upload de seus arquivos!")
    else:
        for doc in docs:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**📄 {doc['name']}**")
                    st.caption(f"Modificado: {doc['modified']} | Tamanho: {doc['size'] / 1024:.1f} KB")
                
                with col2:
                    if st.button("📖 Ler", key=f"read_{doc['name']}"):
                        st.session_state.selected_doc = doc
                        st.session_state.current_page = 'reading'
                        st.rerun()
                
                with col3:
                    if st.button("🗑️", key=f"del_{doc['name']}"):
                        os.remove(doc['path'])
                        st.rerun()
                
                st.divider()

# ============================================
# PÁGINA 4 e 5: MODO DE LEITURA COM NARRAÇÃO
# ============================================
def reading_mode_page():
    if not st.session_state.selected_doc:
        st.warning("Nenhum documento selecionado")
        if st.button("← Voltar"):
            st.session_state.current_page = 'documents'
            st.rerun()
        return
    
    # Inicializar estado da leitura
    if 'reading_speed' not in st.session_state:
        st.session_state.reading_speed = 1.0
    if 'is_playing' not in st.session_state:
        st.session_state.is_playing = False
    if 'current_word_index' not in st.session_state:
        st.session_state.current_word_index = 0
    
    doc = st.session_state.selected_doc
    
    # Cabeçalho
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"📖 {doc['name']}")
    with col2:
        if st.button("← Voltar"):
            st.session_state.current_page = 'documents'
            st.session_state.selected_doc = None
            st.rerun()
    
    st.divider()
    
    # Verificar se usuário tem voz cadastrada
    users = load_users()
    has_voice = users.get(st.session_state.username, {}).get('has_voice', False)
    
    if not has_voice:
        st.warning("⚠️ Configure sua voz primeiro para usar a narração personalizada!")
        if st.button("🎤 Ir para Configuração de Voz"):
            st.session_state.current_page = 'voice'
            st.rerun()
        st.divider()
    
    # Carregar conteúdo do documento
    file_path = Path(doc['path'])
    text_content = ""
    
    if file_path.suffix == '.pdf':
        with open(file_path, 'rb') as f:
            text_content = extract_text_from_pdf(f)
    elif file_path.suffix == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
    
    # Layout principal
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_sidebar:
        st.subheader("🎙️ Controles de Narração")
        
        # Controles de reprodução
        col_play, col_pause, col_stop = st.columns(3)
        
        with col_play:
            if st.button("▶️", help="Reproduzir", use_container_width=True):
                st.session_state.is_playing = True
        
        with col_pause:
            if st.button("⏸️", help="Pausar", use_container_width=True):
                st.session_state.is_playing = False
        
        with col_stop:
            if st.button("⏹️", help="Parar", use_container_width=True):
                st.session_state.is_playing = False
                st.session_state.current_word_index = 0
        
        st.divider()
        
        # Controle de velocidade
        st.subheader("⚡ Velocidade da Narração")
        
        speed_options = {
            "0.5x - Muito Lenta": 0.5,
            "0.75x - Lenta": 0.75,
            "1.0x - Normal": 1.0,
            "1.25x - Rápida": 1.25,
            "1.5x - Muito Rápida": 1.5,
            "2.0x - Super Rápida": 2.0
        }
        
        selected_speed = st.select_slider(
            "Escolha a velocidade:",
            options=list(speed_options.keys()),
            value="1.0x - Normal"
        )
        
        st.session_state.reading_speed = speed_options[selected_speed]
        
        # Indicador visual de velocidade
        speed_value = st.session_state.reading_speed
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background: #f0f2f6; border-radius: 10px; margin: 1rem 0;'>
            <h2 style='margin: 0; color: #667eea;'>{speed_value}x</h2>
            <p style='margin: 0.5rem 0 0 0; color: #666;'>Velocidade Atual</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Status da leitura
        st.subheader("📊 Progresso")
        
        if text_content:
            total_words = len(text_content.split())
            current_progress = (st.session_state.current_word_index / total_words) * 100 if total_words > 0 else 0
            
            st.progress(current_progress / 100)
            st.write(f"**{st.session_state.current_word_index}** de **{total_words}** palavras")
            st.write(f"**{current_progress:.1f}%** concluído")
        
        st.divider()
        
        # Ferramentas adicionais
        st.subheader("🔍 Buscar Palavra")
        search_word = st.text_input("Digite uma palavra", key="word_search")
        
        if search_word and text_content:
            st.markdown(f'<div class="word-tooltip">', unsafe_allow_html=True)
            st.write(f"**Palavra:** {search_word}")
            
            dict_link = get_word_definition_link(search_word)
            st.markdown(f"[📖 Ver no Dicionário]({dict_link})")
            
            count = text_content.lower().count(search_word.lower())
            st.write(f"**Ocorrências:** {count}x")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Configurações visuais
        st.subheader("⚙️ Configurações")
        font_size = st.slider("Tamanho da Fonte", 14, 28, 18)
    
    with col_main:
        st.subheader("📄 Leitura com Destaque Progressivo")
        
        if has_voice and st.session_state.is_playing:
            st.success("🎧 Narração ativa com sua voz personalizada")
        
        # Renderizar texto com destaque
        if text_content:
            # Dividir texto em palavras
            words = text_content.split()
            
            # Criar HTML com destaque progressivo
            html_content = f"""
            <div style='background: white; padding: 2rem; border-radius: 10px; 
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1); line-height: 1.8;
                        font-size: {font_size}px; max-height: 600px; overflow-y: auto;'>
            """
            
            for i, word in enumerate(words):
                # Destacar palavra atual em amarelo
                if st.session_state.is_playing and i == st.session_state.current_word_index:
                    html_content += f'<span style="background-color: #ffeb3b; padding: 2px 4px; border-radius: 3px; font-weight: bold; transition: all 0.3s ease;">{word}</span> '
                # Palavras já lidas em amarelo mais claro
                elif i < st.session_state.current_word_index:
                    html_content += f'<span style="background-color: #fff9c4; padding: 1px 2px;">{word}</span> '
                # Palavras não lidas ainda
                else:
                    html_content += f'<span>{word}</span> '
            
            html_content += "</div>"
            
            # JavaScript para animação automática
            if st.session_state.is_playing:
                # Calcular velocidade de palavras por segundo
                words_per_minute = 150 * st.session_state.reading_speed
                ms_per_word = (60000 / words_per_minute)
                
                html_content += f"""
                <script>
                    let currentIndex = {st.session_state.current_word_index};
                    let totalWords = {len(words)};
                    let speed = {ms_per_word};
                    
                    function updateReading() {{
                        if (currentIndex < totalWords) {{
                            currentIndex++;
                            setTimeout(updateReading, speed);
                        }}
                    }}
                    
                    updateReading();
                </script>
                """
            
            st.markdown(html_content, unsafe_allow_html=True)
            
            # Simular progressão da leitura
            if st.session_state.is_playing:
                import time
                time.sleep(0.1)
                st.session_state.current_word_index += 1
                
                if st.session_state.current_word_index >= len(words):
                    st.session_state.is_playing = False
                    st.session_state.current_word_index = 0
                    st.success("✅ Leitura concluída!")
                else:
                    st.rerun()
        
        else:
            st.info("Não foi possível extrair texto deste documento.")
        
        st.divider()
        
        # Player de áudio simulado (em produção, usaria TTS real)
        st.subheader("🎵 Player de Áudio")
        
        if has_voice:
            voice_file = VOICE_DIR / f"{st.session_state.username}_voice.wav"
            if voice_file.exists():
                st.audio(str(voice_file))
                st.caption("📌 Sua amostra de voz cadastrada será usada para narração")
        
        st.info("""
        💡 **Nota de Desenvolvimento:**
        Em produção, esta funcionalidade utilizaria:
        - **TTS (Text-to-Speech)** com clonagem de voz (Coqui TTS, ElevenLabs, etc)
        - **Sincronização em tempo real** entre áudio e destaque visual
        - **Controle de velocidade** aplicado ao áudio sintetizado
        """)
        
        # Visualização alternativa para PDF
        if file_path.suffix == '.pdf':
            with st.expander("📑 Visualizar PDF Original"):
                with open(file_path, 'rb') as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)

# ============================================
# NAVEGAÇÃO PRINCIPAL
# ============================================
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar com navegação
        with st.sidebar:
            st.title(f"👤 {st.session_state.username}")
            st.divider()
            
            if st.button("🏠 Início"):
                st.session_state.current_page = 'home'
                st.rerun()
            
            if st.button("🎤 Configurar Voz"):
                st.session_state.current_page = 'voice'
                st.rerun()
            
            if st.button("📁 Meus Documentos"):
                st.session_state.current_page = 'documents'
                st.rerun()
            
            st.divider()
            
            if st.button("🚪 Sair"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.current_page = 'login'
                st.session_state.selected_doc = None
                st.rerun()
        
        # Renderizar página atual
        if st.session_state.current_page == 'home':
            st.title("🏠 Bem-vindo ao Assistente de Leitura!")
            st.write(f"Olá, **{st.session_state.username}**!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info("### 🎤 Voz\nConfigure sua voz para leitura personalizada")
                if st.button("Configurar", key="home_voice"):
                    st.session_state.current_page = 'voice'
                    st.rerun()
            
            with col2:
                st.info("### 📁 Documentos\nGerencie seus arquivos de leitura")
                if st.button("Acessar", key="home_docs"):
                    st.session_state.current_page = 'documents'
                    st.rerun()
            
            with col3:
                docs_count = len(get_user_documents(st.session_state.username))
                st.success(f"### 📊 Estatísticas\nDocumentos: {docs_count}")
        
        elif st.session_state.current_page == 'voice':
            voice_setup_page()
        
        elif st.session_state.current_page == 'documents':
            documents_page()
        
        elif st.session_state.current_page == 'reading':
            reading_mode_page()

if __name__ == "__main__":
    main()