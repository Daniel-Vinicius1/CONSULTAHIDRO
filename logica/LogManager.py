# scripts/logica/LogManager.py - SISTEMA DE LOG MELHORADO COM EMOJIS PNG CORRIGIDO
import os
from datetime import datetime
from pathlib import Path
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Optional, Callable, List

class LogManager:
    """Gerenciador de logs melhorado com emojis PNG visuais e organização"""
    
    def __init__(self):
        self.mensagens = []
        self.widget_log = None
        self.emojis_cache = {}
        self.processo_atual = ""
        self.callback_scroll = None
        
        # Carregar emojis dos addons
        self.carregar_emojis()
        
        # Tipos de log com cores
        self.cores_tipos = {
            'inicio': '#00ff00',      # Verde brilhante
            'processo': '#3498db',    # Azul
            'sucesso': '#2ecc71',     # Verde
            'aviso': '#f39c12',       # Laranja
            'erro': '#e74c3c',        # Vermelho
            'info': '#9b59b6',        # Roxo
            'banco': '#1abc9c',       # Turquesa
            'zip': '#f1c40f',         # Amarelo
            'concluido': '#27ae60'    # Verde escuro
        }
    
    def carregar_emojis(self):
        """Carrega todos os emojis dos addons - VERSÃO MELHORADA COM DEBUG"""
        try:
            # Caminho para os emojis
            emoji_path = Path("C:/Users/Samsung/Downloads/Estações_Hidroweb/Scripts/Addons")
            
            print(f"🔍 Procurando emojis em: {emoji_path}")
            print(f"📁 Pasta existe: {emoji_path.exists()}")
            
            # Mapeamento dos emojis
            emojis_map = {
                'start': 'start.png',
                'processando': 'processando.png', 
                'zip': 'zip.png',
                'database': 'DataBase.png',  # Note o D maiúsculo
                'info': 'info.png',
                'error': 'error.png',
                'correto': 'correto.png'
            }
            
            # Listar todos os arquivos na pasta para debug
            if emoji_path.exists():
                arquivos_encontrados = list(emoji_path.glob("*.png"))
                print(f"📋 Arquivos PNG encontrados na pasta: {[f.name for f in arquivos_encontrados]}")
            
            for nome, arquivo in emojis_map.items():
                caminho_emoji = emoji_path / arquivo
                print(f"📁 Verificando: {caminho_emoji}")
                
                if caminho_emoji.exists():
                    try:
                        image = Image.open(caminho_emoji)
                        self.emojis_cache[nome] = ctk.CTkImage(image, size=(16, 16))
                        print(f"✅ Emoji carregado: {nome} -> {arquivo}")
                    except Exception as e:
                        print(f"❌ Erro ao carregar emoji {arquivo}: {e}")
                        self.emojis_cache[nome] = None
                else:
                    print(f"⚠️ Emoji não encontrado: {caminho_emoji}")
                    self.emojis_cache[nome] = None
            
            # Mostrar resumo
            emojis_carregados = sum(1 for emoji in self.emojis_cache.values() if emoji is not None)
            print(f"📊 Resumo: {emojis_carregados}/{len(emojis_map)} emojis PNG carregados com sucesso")
            print(f"🧪 Emojis disponíveis: {list(self.emojis_cache.keys())}")
                    
        except Exception as e:
            print(f"❌ Erro geral ao carregar emojis: {e}")
    
    def set_widget(self, widget):
        """Define o widget de log"""
        self.widget_log = widget
        if self.widget_log:
            self.widget_log.configure(state="disabled")
    
    def set_callback_scroll(self, callback):
        """Define callback para scroll automático"""
        self.callback_scroll = callback
    
    def iniciar_processo(self, nome_processo: str):
        """Inicia um novo processo com separação visual"""
        self.processo_atual = nome_processo
        
        # Adicionar linha em branco se já houver mensagens
        if self.mensagens:
            self._adicionar_linha_vazia()
        
        # Adicionar cabeçalho do processo
        timestamp = datetime.now().strftime("%H:%M:%S")
        separador = "=" * 50
        
        texto_cabecalho = f"\n[{timestamp}] {'🚀' if nome_processo.startswith('DOWNLOAD') else '⚡'} {nome_processo.upper()}\n{separador}"
        
        self._adicionar_mensagem_direta(texto_cabecalho, '#ffffff', emoji_tipo='start')
    
    def log_download_inicio(self, total_estacoes: int):
        """Log do início do download"""
        self.iniciar_processo(f"DOWNLOAD DE {total_estacoes} ESTAÇÕES")
        self.adicionar('processo', 'Download', f'Iniciando download de {total_estacoes} estações', emoji_tipo='processando')
    
    def log_download_estacao(self, codigo: str, atual: int, total: int, sucesso: bool = True):
        """Log do download de uma estação específica"""
        if sucesso:
            self.adicionar('sucesso', 'Download', f'[{atual}/{total}] Estação {codigo} baixada', emoji_tipo='correto')
        else:
            self.adicionar('erro', 'Download', f'[{atual}/{total}] Falha ao baixar estação {codigo}', emoji_tipo='error')
    
    def log_download_final(self, baixadas: List[str], falharam: List[str], inexistentes: List[str]):
        """Log final do download com resumo"""
        total = len(baixadas) + len(falharam) + len(inexistentes)
        
        self.adicionar('info', 'Download', f'RESUMO: {len(baixadas)}/{total} estações baixadas', emoji_tipo='info')
        
        if falharam:
            self.adicionar('aviso', 'Download', f'Falharam: {", ".join(falharam)}', emoji_tipo='error')
        
        if inexistentes:
            self.adicionar('aviso', 'Download', f'Inexistentes: {", ".join(inexistentes)}', emoji_tipo='error')
        
        if len(baixadas) == total:
            self.adicionar('concluido', 'Download', 'Todas as estações foram baixadas com sucesso!', emoji_tipo='correto')
    
    def log_extracao_inicio(self):
        """Log do início da extração"""
        self.iniciar_processo("EXTRAÇÃO E CONSOLIDAÇÃO")
        self.adicionar('processo', 'Extração', 'Iniciando processamento dos arquivos ZIP', emoji_tipo='zip')
    
    def log_extracao_progresso(self, arquivo: str, atual: int, total: int):
        """Log do progresso da extração"""
        self.adicionar('processo', 'Extração', f'[{atual}/{total}] Processando {arquivo}', emoji_tipo='zip')
    
    def log_extracao_final(self, arquivo_final: str, total_registros: int):
        """Log final da extração"""
        nome_arquivo = os.path.basename(arquivo_final)
        self.adicionar('sucesso', 'Extração', f'Arquivo consolidado: {nome_arquivo}', emoji_tipo='correto')
        self.adicionar('info', 'Extração', f'Total de registros: {total_registros:,}', emoji_tipo='info')
        self.adicionar('concluido', 'Extração', 'Consolidação concluída com sucesso!', emoji_tipo='correto')
    
    def log_banco_inicio(self, host: str, database: str, tabela: str = None):
        """Log do início da conexão com banco"""
        self.iniciar_processo("CONEXÃO COM BANCO DE DADOS")
        self.adicionar('processo', 'Banco', f'Conectando: {host}/{database}', emoji_tipo='database')
        if tabela:
            self.adicionar('info', 'Banco', f'Tabela: {tabela}', emoji_tipo='info')
    
    def log_banco_conexao_sucesso(self, total_registros_existentes: int):
        """Log de conexão bem-sucedida"""
        self.adicionar('sucesso', 'Banco', 'Conexão estabelecida com sucesso', emoji_tipo='correto')
        self.adicionar('info', 'Banco', f'Registros na tabela: {total_registros_existentes:,}', emoji_tipo='info')
    
    def log_banco_insercao_inicio(self, total_registros: int):
        """Log do início da inserção"""
        self.adicionar('processo', 'Banco', f'Iniciando inserção de {total_registros:,} registros', emoji_tipo='database')
    
    def log_banco_insercao_progresso(self, lote: int, total_lotes: int, registros_lote: int):
        """Log do progresso da inserção"""
        self.adicionar('processo', 'Banco', f'Lote {lote}/{total_lotes}: {registros_lote} registros', emoji_tipo='database')
    
    def log_banco_duplicatas(self, duplicatas_encontradas: int, novos_inseridos: int):
        """Log de duplicatas encontradas"""
        self.adicionar('info', 'Banco', f'Duplicatas ignoradas: {duplicatas_encontradas:,}', emoji_tipo='info')
        self.adicionar('info', 'Banco', f'Novos registros inseridos: {novos_inseridos:,}', emoji_tipo='info')
    
    def log_banco_final(self, total_final: int, tempo_execucao: str):
        """Log final da inserção no banco"""
        self.adicionar('info', 'Banco', f'Total de registros na tabela: {total_final:,}', emoji_tipo='info')
        self.adicionar('info', 'Banco', f'Tempo de execução: {tempo_execucao}', emoji_tipo='info')
        self.adicionar('concluido', 'Banco', 'Inserção no banco concluída com sucesso!', emoji_tipo='correto')
    
    def log_erro_geral(self, etapa: str, erro: str):
        """Log de erro geral"""
        self.adicionar('erro', etapa, f'ERRO: {erro}', emoji_tipo='error')
    
    def adicionar(self, tipo: str, etapa: str, mensagem: str, emoji_tipo: str = None):
        """
        Adiciona uma mensagem ao log - VERSÃO CORRIGIDA PARA EMOJIS PNG
        
        Args:
            tipo: 'inicio', 'processo', 'sucesso', 'aviso', 'erro', 'info', 'banco', 'zip', 'concluido'
            etapa: Nome da etapa (ex: 'Download', 'Extração', 'Banco')
            mensagem: Texto da mensagem
            emoji_tipo: Tipo do emoji a usar ('start', 'processando', 'zip', 'database', 'info', 'error', 'correto')
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Usar emojis PNG se disponíveis, senão usar emojis melhorados
        emoji_visual = self._obter_emoji_visual(emoji_tipo or tipo)
        
        # Formatar mensagem
        texto_formatado = f"[{timestamp}] {emoji_visual} {etapa}: {mensagem}"
        
        # Cor baseada no tipo
        cor = self.cores_tipos.get(tipo, '#ffffff')
        
        # Adicionar à lista
        self.mensagens.append({
            'timestamp': timestamp,
            'tipo': tipo,
            'etapa': etapa,
            'mensagem': mensagem,
            'texto_formatado': texto_formatado,
            'cor': cor,
            'emoji_tipo': emoji_tipo
        })
        
        # Manter apenas as últimas 100 mensagens
        if len(self.mensagens) > 100:
            self.mensagens = self.mensagens[-100:]
        
        # Atualizar widget
        self._atualizar_widget()
    
    def _obter_emoji_visual(self, emoji_tipo: str) -> str:
        """Obtém o emoji visual - PRIORIZA PNGs MAS USA FALLBACK MELHORADO"""
        
        # Emojis melhorados e mais visuais como fallback
        emojis_melhorados = {
            'start': '🚀',        # Foguete para início
            'processando': '⚙️',   # Engrenagem para processamento  
            'zip': '📦',          # Caixa para zip
            'database': '💾',     # Disquete para banco de dados
            'info': '💡',         # Lâmpada para informação
            'error': '🔴',        # Círculo vermelho para erro
            'correto': '✅',      # Check verde para sucesso
            'inicio': '🟢',       # Círculo verde
            'processo': '🔵',     # Círculo azul
            'sucesso': '✅',      # Check verde
            'aviso': '⚠️',        # Triângulo de aviso
            'erro': '❌',         # X vermelho
            'banco': '🗄️',       # Arquivo de banco
            'concluido': '🎉'     # Festa para conclusão
        }
        
        # VERIFICAR SE TEMOS O PNG DISPONÍVEL
        if emoji_tipo in self.emojis_cache and self.emojis_cache[emoji_tipo] is not None:
            # Se temos PNG, usar um emoji especial + descrição para debug
            emoji_base = emojis_melhorados.get(emoji_tipo, '📝')
            return f"{emoji_base}"  # Por enquanto usar o emoji melhorado
            # TODO: No futuro, implementar inserção real de PNG inline
        
        # Se não tem PNG, usar emoji melhorado
        return emojis_melhorados.get(emoji_tipo, '📝')
    
    def _adicionar_linha_vazia(self):
        """Adiciona uma linha vazia para separação"""
        if self.widget_log:
            self.widget_log.configure(state="normal")
            self.widget_log.insert("end", "\n")
            self.widget_log.configure(state="disabled")
    
    def _adicionar_mensagem_direta(self, texto: str, cor: str, emoji_tipo: str = None):
        """Adiciona uma mensagem diretamente ao widget"""
        if self.widget_log:
            self.widget_log.configure(state="normal")
            self.widget_log.insert("end", texto + "\n")
            self.widget_log.configure(state="disabled")
            self._scroll_para_fim()
    
    def _atualizar_widget(self):
        """Atualiza o widget de log com as mensagens"""
        if not self.widget_log:
            return
        
        # Habilitar temporariamente para edição
        self.widget_log.configure(state="normal")
        
        # Adicionar apenas a última mensagem (mais eficiente)
        if self.mensagens:
            ultima_msg = self.mensagens[-1]
            texto_formatado = ultima_msg['texto_formatado']
            
            # Log de debug para verificar emoji
            emoji_tipo = ultima_msg.get('emoji_tipo')
            if emoji_tipo:
                png_disponivel = emoji_tipo in self.emojis_cache and self.emojis_cache[emoji_tipo] is not None
                print(f"🎨 Emoji {emoji_tipo}: PNG disponível = {png_disponivel}")
            
            self.widget_log.insert("end", texto_formatado + "\n")
        
        # Scroll para o final
        self._scroll_para_fim()
        
        # Desabilitar novamente
        self.widget_log.configure(state="disabled")
    
    def _scroll_para_fim(self):
        """Faz scroll para o final do log"""
        if self.widget_log:
            self.widget_log.see("end")
            if self.callback_scroll:
                self.callback_scroll()
    
    def limpar(self):
        """Limpa todas as mensagens do log"""
        self.mensagens = []
        self.processo_atual = ""
        if self.widget_log:
            self.widget_log.configure(state="normal")
            self.widget_log.delete("1.0", "end")
            self.widget_log.configure(state="disabled")
    
    def obter_resumo_download(self, baixadas: List[str], falharam: List[str], inexistentes: List[str]) -> str:
        """Gera resumo do download para exibição"""
        total = len(baixadas) + len(falharam) + len(inexistentes)
        
        resumo = f"📊 RELATÓRIO DE DOWNLOAD\n\n"
        resumo += f"✅ Total baixadas: {len(baixadas)}/{total}\n"
        
        if len(baixadas) == total:
            resumo += f"\n🎉 Todas as estações foram baixadas com sucesso!"
        else:
            if falharam:
                resumo += f"\n❌ Estações com falha ({len(falharam)}):\n"
                for estacao in falharam:
                    resumo += f"   • {estacao} - Erro técnico/timeout\n"
            
            if inexistentes:
                resumo += f"\n🚫 Estações não encontradas ({len(inexistentes)}):\n"
                for estacao in inexistentes:
                    resumo += f"   • {estacao} - Código inexistente\n"
        
        return resumo


class DialogManager:
    """Gerenciador de diálogos para feedback do usuário"""
    
    @staticmethod
    def mostrar_relatorio_download_consulta(baixadas: List[str], falharam: List[str], inexistentes: List[str]) -> bool:
        """
        Mostra relatório de download para consulta simples
        Retorna True se deve tentar novamente as falhas, False caso contrário
        """
        total = len(baixadas) + len(falharam) + len(inexistentes)
        
        if len(baixadas) == total:
            # Tudo OK
            msg = f"🎉 DOWNLOAD CONCLUÍDO COM SUCESSO!\n\n"
            msg += f"📊 Estatísticas:\n"
            msg += f"   ✅ Baixadas: {len(baixadas)}\n"
            msg += f"   📁 Local: Pasta 'Consultadas'\n\n"
            msg += f"Todas as estações foram baixadas com sucesso!"
            
            messagebox.showinfo("✅ Download Concluído", msg)
            return False
        else:
            # Houve problemas
            msg = f"⚠️ DOWNLOAD PARCIALMENTE CONCLUÍDO\n\n"
            msg += f"📊 Estatísticas:\n"
            msg += f"   ✅ Baixadas: {len(baixadas)}/{total}\n"
            msg += f"   ❌ Com problemas: {len(falharam) + len(inexistentes)}\n\n"
            
            if falharam:
                msg += f"🔴 Estações com falha técnica:\n"
                for estacao in falharam[:5]:  # Mostrar apenas as primeiras 5
                    msg += f"   • {estacao}\n"
                if len(falharam) > 5:
                    msg += f"   • ... e mais {len(falharam) - 5} estações\n"
                msg += f"\n"
            
            if inexistentes:
                msg += f"🚫 Estações não encontradas:\n"
                for estacao in inexistentes[:5]:  # Mostrar apenas as primeiras 5
                    msg += f"   • {estacao}\n"
                if len(inexistentes) > 5:
                    msg += f"   • ... e mais {len(inexistentes) - 5} estações\n"
                msg += f"\n"
            
            msg += f"Deseja tentar o download dos itens com falha?"
            
            return messagebox.askyesno("⚠️ Download Parcial", msg)
    
    @staticmethod
    def mostrar_confirmacao_banco_com_falhas(falharam: List[str], inexistentes: List[str]) -> str:
        """
        Mostra confirmação para continuar para o banco mesmo com falhas
        Retorna 'tentar', 'prosseguir' ou 'cancelar'
        """
        estacoes_problema = falharam + inexistentes
        
        msg = f"⚠️ ALGUMAS ESTAÇÕES NÃO FORAM BAIXADAS\n\n"
        msg += f"❌ As seguintes estações não foram baixadas:\n"
        
        for estacao in estacoes_problema[:8]:  # Mostrar apenas as primeiras 8
            msg += f"   • {estacao}\n"
        
        if len(estacoes_problema) > 8:
            msg += f"   • ... e mais {len(estacoes_problema) - 8} estações\n"
        
        msg += f"\n🤔 O que deseja fazer?"
        
        # Usar um diálogo customizado com 3 opções
        return DialogManager._mostrar_dialogo_tres_opcoes(
            "⚠️ Estações Não Baixadas",
            msg,
            "Tentar Novamente",
            "Prosseguir para Banco",
            "Cancelar"
        )
    
    @staticmethod
    def _mostrar_dialogo_tres_opcoes(titulo: str, mensagem: str, opcao1: str, opcao2: str, opcao3: str) -> Optional[str]:
        """
        Cria um diálogo customizado com três opções
        Retorna: 'tentar', 'prosseguir', 'cancelar' ou None se cancelado
        """
        # Criar janela customizada
        dialogo = ctk.CTkToplevel()
        dialogo.title(titulo)
        dialogo.geometry("500x350")
        dialogo.resizable(False, False)
        dialogo.configure(fg_color="#0f172a")
        dialogo.transient()
        dialogo.grab_set()
        
        # Centralizar
        dialogo.update_idletasks()
        x = (dialogo.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialogo.winfo_screenheight() // 2) - (350 // 2)
        dialogo.geometry(f"+{x}+{y}")
        
        resultado = None
        
        # Título
        titulo_label = ctk.CTkLabel(
            dialogo,
            text=titulo,
            font=("Lato", 18, "bold"),
            text_color="#f8fafc"
        )
        titulo_label.pack(pady=(20, 15))
        
        # Mensagem
        msg_label = ctk.CTkLabel(
            dialogo,
            text=mensagem,
            font=("Lato", 12, "normal"),
            text_color="#94a3b8",
            wraplength=450,
            justify="left"
        )
        msg_label.pack(pady=(0, 30), padx=20)
        
        # Frame para botões
        frame_botoes = ctk.CTkFrame(dialogo, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=40, pady=(0, 20))
        
        def definir_resultado(valor):
            nonlocal resultado
            resultado = valor
            dialogo.destroy()
        
        # Botão 1 - Tentar Novamente
        btn1 = ctk.CTkButton(
            frame_botoes,
            text=opcao1,
            command=lambda: definir_resultado("tentar"),
            width=120,
            height=35,
            fg_color="#3498db",
            hover_color="#2980b9",
            font=("Lato", 12, "bold"),
            corner_radius=15
        )
        btn1.pack(pady=5, fill="x")
        
        # Botão 2 - Prosseguir
        btn2 = ctk.CTkButton(
            frame_botoes,
            text=opcao2,
            command=lambda: definir_resultado("prosseguir"),
            width=120,
            height=35,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            font=("Lato", 12, "bold"),
            corner_radius=15
        )
        btn2.pack(pady=5, fill="x")
        
        # Botão 3 - Cancelar
        btn3 = ctk.CTkButton(
            frame_botoes,
            text=opcao3,
            command=lambda: definir_resultado("cancelar"),
            width=120,
            height=35,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=("Lato", 12, "bold"),
            corner_radius=15
        )
        btn3.pack(pady=5, fill="x")
        
        # Aguardar resultado
        dialogo.wait_window()
        
        return resultado


# Instância global do log manager
log_manager = LogManager()

# Função de conveniência para usar nos outros módulos
def get_log_manager():
    """Retorna a instância do log manager"""
    return log_manager