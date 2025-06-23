# scripts/interfaces/loginBanco.py - VERSÃO ATUALIZADA COM CAMPO TABLE
import customtkinter as ctk
from tkinter import messagebox
import threading
import json
import os
import getpass
from pathlib import Path
from typing import Callable, Optional, Dict
from PIL import Image
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import DbConnect




class LoginBanco:
    """Interface de login para banco de dados PostgreSQL - Design Moderno com Campo Table"""
    
    def __init__(self, callback_sucesso: Callable[[Dict[str, str]], None]):
        """
        Inicializa a interface de login.
        
        Args:
            callback_sucesso: Função chamada quando login é bem-sucedido
                            Recebe dict com as credenciais: {'host', 'port', 'database', 'user', 'password', 'table'}
        """
        self.callback_sucesso = callback_sucesso
        self.janela_login = None
        self.campos = {}
        self.conectando = False
        self.senha_visivel = False
        
       # Arquivo para salvar credenciais
        usuario = getpass.getuser()
        self.arquivo_credenciais = Path(f"C:\\Users\\{usuario}\\Downloads\\Estações_Hidroweb\\Scripts\\dados\\credenciais_banco.json")        
        # Cores modernas inspiradas no Warp.dev
        self.CORES = {
            "primary": "#6366f1",      # Indigo vibrante
            "secondary": "#10b981",    # Verde esmeralda
            "accent": "#f59e0b",       # Âmbar brilhante
            "danger": "#ef4444",       # Vermelho coral
            "success": "#22c55e",      # Verde lima
            "warning": "#f97316",      # Laranja vibrante
            "background": "#000",   # Azul escuro profundo
            "surface": "#000",      # Cinza azulado
            "border": "#334155",       # Cinza médio
            "text": "#f8fafc",         # Branco suave
            "text_muted": "#94a3b8"    # Cinza claro
        }
        
        # Carregar ícones
        self.icones = self.carregar_icones()
        
    def carregar_icones(self):
        """Carrega ícones necessários"""
        try:
            addons_dir = Path(__file__).parent.parent / "Addons"
            icones = {}
            
            # Ícone de olho para mostrar/ocultar senha
            try:
                eye_path = addons_dir / "eye.png"
                if eye_path.exists():
                    eye_image = Image.open(eye_path)
                    icones["eye"] = ctk.CTkImage(eye_image, size=(16, 16))
                else:
                    icones["eye"] = None
            except:
                icones["eye"] = None
                
            # Ícone de olho fechado
            try:
                eye_closed_path = addons_dir / "eye_closed.png"
                if eye_closed_path.exists():
                    eye_closed_image = Image.open(eye_closed_path)
                    icones["eye_closed"] = ctk.CTkImage(eye_closed_image, size=(16, 16))
                else:
                    icones["eye_closed"] = None
            except:
                icones["eye_closed"] = None
                
            return icones
        except Exception as e:
            print(f"⚠️ Erro ao carregar ícones: {e}")
            return {"eye": None, "eye_closed": None}
    
    def salvar_credenciais(self, credenciais: Dict[str, str]):
        """Salva as credenciais (exceto senha) em arquivo JSON"""
        try:
            # Criar diretório se não existir
            self.arquivo_credenciais.parent.mkdir(parents=True, exist_ok=True)
            
            # Salvar apenas dados não sensíveis
            dados_para_salvar = {
                "host": credenciais.get("host", ""),
                "port": credenciais.get("port", ""),
                "database": credenciais.get("database", ""),
                "user": credenciais.get("user", ""),
                "table": credenciais.get("table", "")
                # Não salvar a senha por segurança
            }
            
            with open(self.arquivo_credenciais, 'w') as f:
                json.dump(dados_para_salvar, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Erro ao salvar credenciais: {e}")
    
    def carregar_credenciais(self) -> Dict[str, str]:
        """Carrega as credenciais salvas"""
        try:
            if self.arquivo_credenciais.exists():
                with open(self.arquivo_credenciais, 'r') as f:
                    dados = json.load(f)
                    # Adicionar valores padrão se não existirem
                    if 'table' not in dados:
                        dados['table'] = ""
                    return dados
            else:
                return {
                    "host": "localhost",
                    "port": "5432", 
                    "database": "sipam_hidro",
                    "user": "postgres",
                    "table": ""
                }
        except Exception as e:
            print(f"⚠️ Erro ao carregar credenciais: {e}")
            return {
                "host": "localhost",
                "port": "5432",
                "database": "sipam_hidro", 
                "user": "postgres",
                "table": ""
            }
        
    def criar_interface(self):
        """Cria a interface de login do banco de dados"""
        self.janela_login = ctk.CTkToplevel()
        self.janela_login.title("Conexão com Banco PostgreSQL")
        self.janela_login.geometry("520x900")  # Aumentei a altura para o novo campo
        self.janela_login.resizable(False, False)
        self.janela_login.configure(fg_color=self.CORES["background"])
        
        # Centralizar janela na tela
        self.janela_login.transient()
        self.janela_login.grab_set()
        
        # Centralizar a janela na tela
        self.janela_login.update_idletasks()
        x = (self.janela_login.winfo_screenwidth() // 2) - (520 // 2)
        y = (self.janela_login.winfo_screenheight() // 2) - (800 // 2)
        self.janela_login.geometry(f"+{x}+{y}")
        
        # Frame principal
        self.frame_principal = ctk.CTkFrame(
            self.janela_login,
            fg_color=self.CORES["surface"],
            corner_radius=20,
            border_width=1,
            border_color=self.CORES["border"]
        )
        self.frame_principal.pack(expand=True, fill="both", padx=30, pady=30)
        
        # Título moderno
        titulo = ctk.CTkLabel(
            self.frame_principal,
            text="🗄️ Configuração do Banco",
            font=("Lato", 22, "bold"),
            text_color=self.CORES["text"]
        )
        titulo.pack(pady=(20, 15))
        
        # Label de status dinâmica (mostra status da conexão)
        self.label_status_conexao = ctk.CTkLabel(
            self.frame_principal,
            text="Digite as informações de conexão do PostgreSQL:",
            font=("Lato", 13, "normal"),
            text_color=self.CORES["text_muted"],
            wraplength=400
        )
        self.label_status_conexao.pack(pady=(0, 25))
        
        # Container para os campos
        self.container_campos = ctk.CTkFrame(
            self.frame_principal,
            fg_color="transparent"
        )
        self.container_campos.pack(fill="x", padx=20)
        
        # Carregar credenciais salvas
        credenciais_salvas = self.carregar_credenciais()
        
        # Campos de entrada
        self.criar_campo("Host/Servidor:", "host", credenciais_salvas.get("host", "localhost"), self.container_campos)
        self.criar_campo("Porta:", "port", credenciais_salvas.get("port", "5432"), self.container_campos)
        self.criar_campo("Nome do Banco:", "database", credenciais_salvas.get("database", "sipam_hidro"), self.container_campos)
        self.criar_campo("Usuário:", "user", credenciais_salvas.get("user", "postgres"), self.container_campos)
        self.criar_campo_senha("Senha:", "password", "", self.container_campos)
        
        # NOVO CAMPO: Table
        self.criar_campo_table("Table (opcional):", "table", credenciais_salvas.get("table", ""), self.container_campos)
        
        # Frame para botões com design moderno
        frame_botoes = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=20, pady=(30, 20))
        
        # Primeira linha - Botão Testar Conexão (centralizado)
        frame_linha1 = ctk.CTkFrame(frame_botoes, fg_color="transparent")
        frame_linha1.pack(fill="x", pady=(0, 10))
        
        self.botao_testar = ctk.CTkButton(
            frame_linha1,
            text="Testar Conexão",
            command=self.testar_conexao,
            width=200,
            height=40,
            fg_color="transparent",
            hover_color=("#E67E22", "#D35400"),
            font=("Segoe UI", 14, "bold"),
            corner_radius=22,
            border_width=2,
            border_color=self.CORES["warning"],
            text_color=self.CORES["text"]
        )
        self.botao_testar.pack(expand=True)
        
        # Segunda linha - Botões Cancelar e Enviar
        frame_linha2 = ctk.CTkFrame(frame_botoes, fg_color="transparent")
        frame_linha2.pack(fill="x")
        
        # Botão Cancelar - Vermelho coral
        botao_cancelar = ctk.CTkButton(
            frame_linha2,
            text="Cancelar",
            command=self.cancelar,
            width=140,
            height=40,
            fg_color="transparent",
            hover_color=self.CORES["danger"],
            font=("Segoe UI", 14, "bold"),
            corner_radius=22,
            border_width=2,
            border_color=self.CORES["danger"],
            text_color=self.CORES["text"]
        )
        botao_cancelar.pack(side="left", expand=True, fill="x", padx=(0, 8))
        
        # Botão Enviar - Verde esmeralda
        self.botao_conectar = ctk.CTkButton(
            frame_linha2,
            text="Enviar",
            command=self.conectar,
            width=140,
            height=40,
            font=("Segoe UI", 14, "bold"),
            fg_color="transparent",
            hover_color=self.CORES["secondary"],
            corner_radius=22,
            border_width=2,
            border_color=self.CORES["secondary"],
            text_color=self.CORES["text"]
        )
        self.botao_conectar.pack(side="right", expand=True, fill="x", padx=(8, 0))
        
        # Bind Enter para conectar
        self.janela_login.bind("<Return>", lambda e: self.conectar())
        
        # Focar no primeiro campo vazio
        self.janela_login.after(100, self.focar_primeiro_campo_vazio)
        
    def criar_campo(self, label_text: str, campo_nome: str, valor_padrao: str, parent):
        """Cria um campo de entrada com label - Design moderno"""
        frame_campo = ctk.CTkFrame(parent, fg_color="transparent", height=75)
        frame_campo.pack(fill="x", pady=8)
        frame_campo.pack_propagate(False)
        
        # Label moderno
        label = ctk.CTkLabel(
            frame_campo,
            text=label_text,
            font=("Lato", 14, "bold"),
            text_color=self.CORES["text"],
            anchor="w"
        )
        label.pack(anchor="w", pady=(0, 6))
        
        # Campo de entrada moderno
        campo = ctk.CTkEntry(
            frame_campo,
            placeholder_text=f"Ex: {valor_padrao}" if valor_padrao else "Digite aqui...",
            height=42,
            font=("Lato", 13, "normal"),
            corner_radius=12,
            border_width=2,
            border_color=self.CORES["border"],
            fg_color=self.CORES["background"],
            text_color=self.CORES["text"],
            placeholder_text_color=self.CORES["text_muted"]
        )
        
        if valor_padrao:
            campo.insert(0, valor_padrao)
        
        campo.pack(fill="x", pady=(0, 4))
        self.campos[campo_nome] = campo
        
    def criar_campo_senha(self, label_text: str, campo_nome: str, valor_padrao: str, parent):
        """Cria um campo de senha com botão para mostrar/ocultar"""
        frame_campo = ctk.CTkFrame(parent, fg_color="transparent", height=75)
        frame_campo.pack(fill="x", pady=8)
        frame_campo.pack_propagate(False)
        
        # Label moderno
        label = ctk.CTkLabel(
            frame_campo,
            text=label_text,
            font=("Lato", 14, "bold"),
            text_color=self.CORES["text"],
            anchor="w"
        )
        label.pack(anchor="w", pady=(0, 6))
        
        # Frame para campo de senha + botão de olho
        frame_senha = ctk.CTkFrame(frame_campo, fg_color="transparent")
        frame_senha.pack(fill="x", pady=(0, 4))
        
        # Campo de senha
        self.campo_senha = ctk.CTkEntry(
            frame_senha,
            placeholder_text="Digite a senha...",
            show="*",
            height=42,
            font=("Lato", 13, "normal"),
            corner_radius=12,
            border_width=2,
            border_color=self.CORES["border"],
            fg_color=self.CORES["background"],
            text_color=self.CORES["text"],
            placeholder_text_color=self.CORES["text_muted"]
        )
        self.campo_senha.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        # Botão para mostrar/ocultar senha
        self.botao_olho = ctk.CTkButton(
            frame_senha,
            text="👁️",
            width=20,
            height=30,
            font=("Arial", 14),
            command=self.alternar_visibilidade_senha,
            fg_color=self.CORES["surface"],
            hover_color=self.CORES["border"],
            corner_radius=12,
            border_width=2,
            border_color=self.CORES["border"],
            text_color=self.CORES["text_muted"]
        )
        self.botao_olho.pack(side="right")
        
        if valor_padrao:
            self.campo_senha.insert(0, valor_padrao)
        
        self.campos[campo_nome] = self.campo_senha
        
    def criar_campo_table(self, label_text: str, campo_nome: str, valor_padrao: str, parent):
        """Cria um campo específico para tabela com explicação"""
        frame_campo = ctk.CTkFrame(parent, fg_color="transparent", height=90)
        frame_campo.pack(fill="x", pady=8)
        frame_campo.pack_propagate(False)
        
        # Label moderno
        label = ctk.CTkLabel(
            frame_campo,
            text=label_text,
            font=("Lato", 14, "bold"),
            text_color=self.CORES["text"],
            anchor="w"
        )
        label.pack(anchor="w", pady=(0, 6))
        
        # Campo de entrada moderno
        campo = ctk.CTkEntry(
            frame_campo,
            placeholder_text="Ex: origem.ana_cota_dia ou ana.ana_cota_diaria",
            height=42,
            font=("Lato", 13, "normal"),
            corner_radius=12,
            border_width=2,
            border_color=self.CORES["border"],
            fg_color=self.CORES["background"],
            text_color=self.CORES["text"],
            placeholder_text_color=self.CORES["text_muted"]
        )
        
        if valor_padrao:
            campo.insert(0, valor_padrao)
        
        campo.pack(fill="x", pady=(0, 4))
        
        # Explicação
        explicacao = ctk.CTkLabel(
            frame_campo,
            text="💡 Deixe vazio para detectar automaticamente",
            font=("Lato", 10, "normal"),
            text_color=self.CORES["text_muted"],
            anchor="w"
        )
        explicacao.pack(anchor="w", pady=(2, 0))
        
        self.campos[campo_nome] = campo
        
    def alternar_visibilidade_senha(self):
        """Alterna entre mostrar e ocultar a senha"""
        if self.senha_visivel:
            # Ocultar senha
            self.campo_senha.configure(show="*")
            self.botao_olho.configure(text="👁️", text_color=self.CORES["text_muted"])
            self.senha_visivel = False
        else:
            # Mostrar senha
            self.campo_senha.configure(show="")
            self.botao_olho.configure(text="🙈", text_color=self.CORES["primary"])
            self.senha_visivel = True
    
    def focar_primeiro_campo_vazio(self):
        """Foca no primeiro campo que estiver vazio"""
        for nome, campo in self.campos.items():
            if nome != 'table' and not campo.get().strip():  # Table é opcional
                campo.focus()
                break
    
    def obter_credenciais(self) -> Dict[str, str]:
        """Obtém as credenciais dos campos de entrada"""
        credenciais = {}
        for nome, campo in self.campos.items():
            valor = campo.get().strip()
            if not valor and nome in ['host', 'port', 'database', 'user']:
                # Usa valores padrão para campos obrigatórios se estiverem vazios
                valores_padrao = {
                    'host': 'localhost',
                    'port': '5432',
                    'database': 'sipam_hidro',
                    'user': 'postgres'
                }
                valor = valores_padrao.get(nome, '')
            credenciais[nome] = valor
        return credenciais
    
    def validar_credenciais(self, credenciais: Dict[str, str]) -> bool:
        """Valida se as credenciais estão completas"""
        campos_obrigatorios = ['host', 'port', 'database', 'user', 'password']
        
        for campo in campos_obrigatorios:
            if not credenciais.get(campo, '').strip():
                messagebox.showerror(
                    "Erro de Validação",
                    f"O campo '{self.traduzir_nome_campo(campo)}' é obrigatório!"
                )
                if campo in self.campos:
                    self.campos[campo].focus()
                return False
        
        # Validar porta
        try:
            port = int(credenciais['port'])
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                "Erro de Validação",
                "A porta deve ser um número entre 1 e 65535!"
            )
            self.campos['port'].focus()
            return False
        
        return True
    
    def traduzir_nome_campo(self, campo):
        """Traduz nomes de campos para português"""
        traducoes = {
            'host': 'Host/Servidor',
            'port': 'Porta',
            'database': 'Nome do Banco',
            'user': 'Usuário',
            'password': 'Senha',
            'table': 'Table'
        }
        return traducoes.get(campo, campo.capitalize())
    
    def mostrar_status_conexao(self, texto: str, cor: str):
        """Mostra status da conexão"""
        self.label_status_conexao.configure(
            text=texto,
            text_color=cor,
            font=("Lato", 13, "bold")
        )
        
    def testar_conexao(self):
        """Testa a conexão com o banco de dados"""
        if self.conectando:
            return
            
        credenciais = self.obter_credenciais()
        if not self.validar_credenciais(credenciais):
            return
        
        self.conectando = True
        self.mostrar_status_conexao("🔄 Conectando-se...", self.CORES["warning"])
        self.botao_testar.configure(state="disabled", text="Testando...")
        self.botao_conectar.configure(state="disabled")
        
        def testar():
            try:
                # Importar a classe de conexão
                import sys
                from pathlib import Path
                
                # Adicionar caminho do DbConnect ao sys.path se necessário
                logica_dir = Path(__file__).parent.parent / "logica"
                if str(logica_dir) not in sys.path:
                    sys.path.insert(0, str(logica_dir))
                
                from DbConnect import testar_conexao_completa
                
                # Testar conexão real (incluindo nome da tabela se especificado)
                nome_tabela = credenciais.get('table') if credenciais.get('table') else None
                sucesso = testar_conexao_completa(credenciais, nome_tabela)
                
                if sucesso:
                    self.janela_login.after(0, self.teste_sucesso)
                else:
                    self.janela_login.after(0, lambda: self.teste_erro("Falha na conexão com o banco PostgreSQL"))
                
            except ImportError as e:
                erro_msg = f"Erro ao importar DbConnect: {e}"
                self.janela_login.after(0, lambda: self.teste_erro(erro_msg))
            except Exception as e:
                erro_msg = str(e)
                self.janela_login.after(0, lambda: self.teste_erro(erro_msg))
        
        threading.Thread(target=testar, daemon=True).start()
    
    def teste_sucesso(self):
        """Chamado quando o teste de conexão é bem-sucedido"""
        self.conectando = False
        self.mostrar_status_conexao("✅ Conexão realizada com sucesso!", self.CORES["success"])
        self.botao_testar.configure(state="normal", text="Testar Conexão")
        self.botao_conectar.configure(state="normal")
        
        # Salvar credenciais quando conexão for bem-sucedida
        credenciais = self.obter_credenciais()
        self.salvar_credenciais(credenciais)
    
    def teste_erro(self, erro_msg: str):
        """Chamado quando o teste de conexão falha"""
        self.conectando = False
        self.mostrar_status_conexao("❌ Conexão falhou!", self.CORES["danger"])
        self.botao_testar.configure(state="normal", text="Testar Conexão")
        self.botao_conectar.configure(state="normal")
        
        messagebox.showerror(
            "Erro de Conexão",
            f"Não foi possível conectar ao banco de dados:\n\n{erro_msg}\n\nVerifique:\n• Se o PostgreSQL está rodando\n• Se os dados estão corretos\n• Se há permissão de acesso\n• Se a tabela especificada existe"
        )
    
    def conectar(self):
        """Conecta ao banco e inicia o processo"""
        if self.conectando:
            return
            
        credenciais = self.obter_credenciais()
        if not self.validar_credenciais(credenciais):
            return
        
        # Salvar credenciais
        self.salvar_credenciais(credenciais)
        
        # Mostrar confirmação
        msg = f"Iniciar processamento com:\n\n"
        msg += f"🏠 Host: {credenciais['host']}:{credenciais['port']}\n"
        msg += f"🗄️ Banco: {credenciais['database']}\n"
        msg += f"👤 Usuário: {credenciais['user']}\n"
        
        # Mostrar informação da tabela
        if credenciais.get('table'):
            msg += f"📋 Tabela: {credenciais['table']}\n"
        else:
            msg += f"📋 Tabela: Detectar automaticamente\n"
        
        msg += f"\nEste processo irá:\n"
        msg += f"• Baixar estações para pasta principal\n"
        msg += f"• Extrair arquivos *_Cotas.csv\n"
        msg += f"• Consolidar dados em arquivo único\n"
        msg += f"• Inserir dados na tabela especificada\n"
        msg += f"\nConfirma?"
        
        if messagebox.askyesno("Confirmar Processamento", msg):
            # Fechar janela de login
            self.janela_login.destroy()
            
            # Chamar callback de sucesso
            if self.callback_sucesso:
                self.callback_sucesso(credenciais)
    
    def cancelar(self):
        """Cancela o login"""
        self.janela_login.destroy()
    
    def mostrar(self):
        """Exibe a janela de login"""
        self.criar_interface()

def teste_login():
    """Função de teste para a interface de login"""
    def ao_conectar(credenciais):
        print("🔗 Credenciais recebidas:")
        for chave, valor in credenciais.items():
            if chave == 'password':
                print(f"  {chave}: {'*' * len(valor)}")
            else:
                print(f"  {chave}: {valor}")
        
        messagebox.showinfo("Sucesso", "Processamento iniciado!\nVerifique o console para acompanhar o progresso.")
    
    # Configurar tema
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Criar janela principal (só para teste)
    root = ctk.CTk()
    root.geometry("450x300")
    root.title("Teste Login Banco")
    root.configure(fg_color="#0f172a")
    
    # Título
    titulo = ctk.CTkLabel(
        root, 
        text="🧪 Teste da Interface de Login", 
        font=("Lato", 18, "bold"),
        text_color="#6366f1"
    )
    titulo.pack(pady=30)
    
    # Botão para abrir login
    botao_teste = ctk.CTkButton(
        root,
        text="🗄️ Abrir Login do Banco",
        command=lambda: LoginBanco(ao_conectar).mostrar(),
        width=220,
        height=50,
        hover_color=("#E67E22", "#D35400"),
        font=("Segoe UI", 14, "bold"),
        corner_radius=22,
    )
    botao_teste.pack(expand=True)
    
    # Instruções
    instrucoes = ctk.CTkLabel(
        root, 
        text="Clique no botão para testar a interface de login",
        font=("Lato", 12, "normal"),
        text_color="#94a3b8"
    )
    instrucoes.pack(pady=(0, 30))
    
    root.mainloop()

if __name__ == "__main__":
    teste_login()