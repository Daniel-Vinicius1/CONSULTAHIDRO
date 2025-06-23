# scripts/interfaces/interface.py - VERSÃO ATUALIZADA COM SISTEMA DE LOG MELHORADO

import customtkinter as ctk  
from tkinter import messagebox
import os
import sys
import subprocess
import platform
import getpass
from threading import Thread
from pathlib import Path
import re
import json
from PIL import Image
from datetime import datetime

# Configuração de caminhos para importações
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent
scripts_dir = current_dir.parent
logica_dir = scripts_dir / "logica"
addons_dir = scripts_dir / "Addons"

# Adicionar caminhos ao sys.path
sys.path.insert(0, str(logica_dir))
sys.path.insert(0, str(current_dir))

# Importações dos módulos do projeto
try:
    from play import baixar_estacoes
    from consumo import criar_pasta_base, criar_estrutura_pastas
    from extracaoZip import processar_estacoes_completo, limpar_arquivos_temporarios
    from loginBanco import LoginBanco
    from LogManager import log_manager, DialogManager  # NOVO IMPORT
    print("✅ Todos os módulos importados com sucesso!")
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    messagebox.showerror("Erro de Importação", f"Erro ao carregar módulos:\n{e}")
    sys.exit(1)

# Variáveis globais
processo_ativo = False
parar_flag = False
progresso_atual = {"etapa": "", "atual": 0, "total": 0, "tipo": "contagem"}

# Histórico para Ctrl+Z
historico_texto = []
posicao_historico = -1

# Histórico de estações consultadas
historico_estacoes = []
usuario = getpass.getuser()
ARQUIVO_HISTORICO = f"C:\\Users\\{usuario}\\Downloads\\Estações_Hidroweb\\Scripts\\dados\\historico_estacoes.json"

# Variável para controlar seleção no histórico
botoes_historico = {}
estacao_selecionada = None
botao_selecionado = None

# TEMA MODERNO
ctk.set_appearance_mode("dark")

# Sistema de cores
class CoresTema:
    def __init__(self):
        self.primary = "#f8fafc"
        self.secondary = "#10b981"
        self.accent = "#f59e0b"
        self.danger = "#ef4444"
        self.success = "#02ff00"
        self.warning = "#f97316"
        self.purple = "#a7adc2"
        self.cyan = "#06b6d4"
        self.pink = "#ec4899" 
        self.sty = "#0b57d0"
        self.background = "#000"
        self.surface = "#00061c"
        self.border = "#334155"
        self.text = "#f8fafc"
        self.text_muted = "#94a3b8"

CORES = CoresTema()

# Função para carregar ícones
def carregar_icone(nome_arquivo, tamanho=(20, 20)):
    try:
        caminho_icone = addons_dir / nome_arquivo
        if caminho_icone.exists():
            image = Image.open(caminho_icone)
            return ctk.CTkImage(image, size=tamanho)
        else:
            print(f"⚠️ Ícone não encontrado: {caminho_icone}")
            return None
    except Exception as e:
        print(f"⚠️ Erro ao carregar ícone {nome_arquivo}: {e}")
        return None

# Carregar ícones
icones = {
    "relatorio": carregar_icone("jornal.png", (18, 18)),
    "search": carregar_icone("icons8-pesquisar-48.png", (18, 18)),
    "stop": carregar_icone("icons8-parar-64.png", (16, 16)),
    "folder": carregar_icone("icons8-pasta-48.png", (18, 18)),
    "database": carregar_icone("icons8-aceitar-banco-de-dados-50.png", (20, 20)),
    "trash_orange": carregar_icone("excluir.png", (16, 16)),
    "trash_red": carregar_icone("excluir (1).png", (16, 16))
}

janela = ctk.CTk()
janela.title("Consulta de Estação - SIPAMHIDRO")
janela.geometry("1100x700")
janela.resizable(False, False)
janela.configure(fg_color=CORES.background)

def carregar_historico():
    global historico_estacoes
    try:
        pasta_dados = Path(ARQUIVO_HISTORICO).parent
        pasta_dados.mkdir(parents=True, exist_ok=True)
        
        if os.path.exists(ARQUIVO_HISTORICO):
            with open(ARQUIVO_HISTORICO, 'r') as f:
                historico_estacoes = json.load(f)
        else:
            historico_estacoes = []
    except Exception:
        historico_estacoes = []

def salvar_historico():
    try:
        pasta_dados = Path(ARQUIVO_HISTORICO).parent
        pasta_dados.mkdir(exist_ok=True)
        
        with open(ARQUIVO_HISTORICO, 'w') as f:
            json.dump(historico_estacoes, f)
    except Exception as e:
        print(f"⚠️ Erro ao salvar histórico: {e}")

def adicionar_ao_historico(codigos_lista):
    global historico_estacoes
    for codigo in codigos_lista:
        if codigo not in historico_estacoes:
            historico_estacoes.insert(0, codigo)
    
    if len(historico_estacoes) > 50:
        historico_estacoes = historico_estacoes[:50]
    
    salvar_historico()
    atualizar_lista_historico()

def atualizar_progresso_adaptativo(etapa, atual, total, texto="", tipo="contagem"):
    global progresso_atual
    
    progresso_atual = {
        "etapa": etapa,
        "atual": atual,
        "total": total,
        "tipo": tipo
    }
    
    if total > 0:
        progresso = atual / total
        barra_progresso.set(progresso)
        
        if tipo == "contagem":
            label_status.configure(
                text=f"{etapa}: {atual}/{total} estações",
                font=("Lato", 12, "bold"),
                text_color=CORES.text
            )
        else:
            porcentagem = int(progresso * 100)
            label_status.configure(
                text=f"{etapa}: {porcentagem}%",
                font=("Lato", 12, "bold"),
                text_color=CORES.text
            )
        
        janela.after_idle(lambda: None)

def executar_consulta(tipo_consulta="consultadas"):
    """Executa consulta simples (apenas salva arquivos ZIP) - VERSÃO MELHORADA"""
    global processo_ativo, parar_flag
    if processo_ativo:
        return
    parar_flag = False
    
    codigos = obter_codigos_validos()
    if not codigos:
        return
    
    adicionar_ao_historico(codigos)
    
    processo_ativo = True
    barra_progresso.pack(pady=10)
    barra_progresso.set(0)
    
    # Limpar log e inicializar
    log_manager.limpar()
    log_manager.log_download_inicio(len(codigos))
    
    def tarefa():
        global processo_ativo
        try:
            estacoes_baixadas = []
            estacoes_falharam = []
            estacoes_inexistentes = []
            
            def callback_progresso_personalizado(atual, total, texto=""):
                atualizar_progresso_adaptativo("Download", atual, total, tipo="contagem")
                
                # Log específico por estação
                if atual <= total:
                    # Extrair código da estação do texto se disponível
                    codigo = texto.split()[-1] if texto else f"estação_{atual}"
                    if "Baixando" in texto:
                        codigo = texto.replace("Baixando ", "").replace(" - Retry", "")
                    log_manager.log_download_estacao(codigo, atual, total, True)
            
            resultado = baixar_estacoes(
                codigos, 
                callback_progresso=callback_progresso_personalizado, 
                parar_callback=lambda: parar_flag,
                tipo_consulta=tipo_consulta
            )
            
            if not parar_flag:
                # Organizar resultados
                estacoes_baixadas = resultado.get('baixadas', [])
                estacoes_falharam = resultado.get('falharam', [])
                estacoes_inexistentes = resultado.get('inexistentes', [])
                
                # Log final detalhado
                log_manager.log_download_final(estacoes_baixadas, estacoes_falharam, estacoes_inexistentes)
                
                # Mostrar relatório interativo
                if estacoes_falharam or estacoes_inexistentes:
                    # Há problemas - mostrar opções
                    tentar_novamente = DialogManager.mostrar_relatorio_download_consulta(
                        estacoes_baixadas, estacoes_falharam, estacoes_inexistentes
                    )
                    
                    if tentar_novamente:
                        # Usuário quer tentar novamente
                        estacoes_retry = estacoes_falharam + estacoes_inexistentes
                        log_manager.adicionar('processo', 'Download', f'Tentando novamente {len(estacoes_retry)} estações', 'processando')
                        
                        # Executar nova tentativa
                        resultado_retry = baixar_estacoes(
                            estacoes_retry,
                            callback_progresso=callback_progresso_personalizado,
                            parar_callback=lambda: parar_flag,
                            tipo_consulta=tipo_consulta
                        )
                        
                        # Atualizar resultados
                        estacoes_baixadas.extend(resultado_retry.get('baixadas', []))
                        estacoes_falharam = resultado_retry.get('falharam', [])
                        estacoes_inexistentes = resultado_retry.get('inexistentes', [])
                        
                        # Log da segunda tentativa
                        log_manager.log_download_final(estacoes_baixadas, estacoes_falharam, estacoes_inexistentes)
                        
                        # Mostrar resultado final
                        if not estacoes_falharam and not estacoes_inexistentes:
                            messagebox.showinfo("✅ Sucesso", "Todas as estações foram baixadas na segunda tentativa!")
                        else:
                            msg = f"Segunda tentativa concluída:\n"
                            msg += f"✅ Total baixadas: {len(estacoes_baixadas)}\n"
                            if estacoes_falharam:
                                msg += f"❌ Ainda com problemas: {len(estacoes_falharam + estacoes_inexistentes)}"
                            messagebox.showinfo("Resultado da Segunda Tentativa", msg)
                else:
                    # Tudo OK - sucesso total
                    DialogManager.mostrar_relatorio_download_consulta(
                        estacoes_baixadas, estacoes_falharam, estacoes_inexistentes
                    )
                    
        except Exception as e:
            log_manager.log_erro_geral('Sistema', f'Erro durante download: {str(e)}')
            messagebox.showerror("Erro", f"Erro durante o download: {e}")
        finally:
            barra_progresso.pack_forget()
            label_status.configure(text="")
            processo_ativo = False
            if parar_flag:
                log_manager.adicionar('aviso', 'Sistema', 'Consulta interrompida pelo usuário', 'error')
                messagebox.showinfo("Cancelado", "Consulta interrompida pelo usuário.")
    
    Thread(target=tarefa, daemon=True).start()

def executar_consulta_e_banco():
    """Executa consulta completa com processamento para banco de dados - VERSÃO MELHORADA"""
    def ao_conectar_banco(credenciais):
        log_manager.log_banco_inicio(
            credenciais["host"], 
            credenciais["database"], 
            credenciais.get("table")
        )
        
        global processo_ativo, parar_flag
        if processo_ativo:
            return
        parar_flag = False
        
        codigos = obter_codigos_validos()
        if not codigos:
            return
        
        adicionar_ao_historico(codigos)
        
        processo_ativo = True
        barra_progresso.pack(pady=10)
        barra_progresso.set(0)
        
        # Limpar log e iniciar processo
        log_manager.limpar()
        log_manager.log_download_inicio(len(codigos))
        
        def tarefa_completa():
            global processo_ativo
            try:
                total_estacoes = len(codigos)
                
                # Etapa 1: Download das estações
                log_manager.adicionar('processo', 'Download', 'Iniciando download das estações', 'start')
                atualizar_progresso_adaptativo("Download", 0, total_estacoes, tipo="contagem")
                
                def callback_download(atual, total, texto=""):
                    atualizar_progresso_adaptativo("Download", atual, total, tipo="contagem")
                    if atual <= total and texto:
                        codigo = texto.replace("Baixando ", "").split(" -")[0].strip()
                        log_manager.log_download_estacao(codigo, atual, total, True)
                
                resultado = baixar_estacoes(
                    codigos, 
                    callback_progresso=callback_download, 
                    parar_callback=lambda: parar_flag,
                    tipo_consulta="normal"  # Para pasta principal
                )
                
                if parar_flag:
                    return
                
                estacoes_baixadas = resultado.get('baixadas', [])
                estacoes_falharam = resultado.get('falharam', [])
                estacoes_inexistentes = resultado.get('inexistentes', [])
                
                # Log final do download
                log_manager.log_download_final(estacoes_baixadas, estacoes_falharam, estacoes_inexistentes)
                
                # Verificar se há falhas
                if estacoes_falharam or estacoes_inexistentes:
                    # Perguntar se quer tentar novamente ou prosseguir
                    acao = DialogManager.mostrar_confirmacao_banco_com_falhas(
                        estacoes_falharam, estacoes_inexistentes
                    )
                    
                    if acao == "tentar":
                        # Tentar novamente as estações com problema
                        estacoes_retry = estacoes_falharam + estacoes_inexistentes
                        log_manager.adicionar('processo', 'Download', f'Nova tentativa: {len(estacoes_retry)} estações', 'processando')
                        
                        resultado_retry = baixar_estacoes(
                            estacoes_retry,
                            callback_progresso=callback_download,
                            parar_callback=lambda: parar_flag,
                            tipo_consulta="normal"
                        )
                        
                        # Atualizar resultados
                        estacoes_baixadas.extend(resultado_retry.get('baixadas', []))
                        estacoes_falharam = resultado_retry.get('falharam', [])
                        estacoes_inexistentes = resultado_retry.get('inexistentes', [])
                        
                        log_manager.log_download_final(estacoes_baixadas, estacoes_falharam, estacoes_inexistentes)
                    
                    elif acao == "cancelar":
                        log_manager.adicionar('aviso', 'Sistema', 'Processamento cancelado pelo usuário', 'error')
                        return
                    
                    # Se acao == "prosseguir", continua para o banco
                
                if not estacoes_baixadas:
                    log_manager.log_erro_geral('Download', 'Nenhuma estação foi baixada')
                    messagebox.showerror("Erro", "Nenhuma estação foi baixada com sucesso!")
                    return
                
                # Etapa 2: Processamento dos arquivos
                log_manager.log_extracao_inicio()
                atualizar_progresso_adaptativo("Extração", 50, 100, tipo="porcentagem")
                
                def callback_extracao(etapa, progresso, total, tipo="porcentagem"):
                    atualizar_progresso_adaptativo("Extração", progresso, total, tipo=tipo)
                    if "Processando" in etapa:
                        arquivo = etapa.split("Processando ")[-1] if "Processando" in etapa else "arquivo"
                        log_manager.log_extracao_progresso(arquivo, progresso, total)
                
                arquivo_final = processar_estacoes_completo(
                    resultado['pasta_destino'], 
                    callback_progresso=callback_extracao
                )
                
                if not arquivo_final:
                    log_manager.log_erro_geral('Extração', 'Falha no processamento dos arquivos')
                    messagebox.showerror("Erro", "Falha no processamento dos arquivos!")
                    return
                
                # Contar registros do arquivo final
                try:
                    with open(arquivo_final, 'r', encoding='utf-8') as f:
                        total_registros = sum(1 for _ in f) - 1  # -1 para excluir cabeçalho
                except:
                    total_registros = 0
                
                nome_arquivo = os.path.basename(arquivo_final)
                log_manager.log_extracao_final(arquivo_final, total_registros)
                
                # Etapa 3: Inserção no banco
                log_manager.log_banco_inicio(
                    credenciais['host'], 
                    credenciais['database'], 
                    credenciais.get('table')
                )
                atualizar_progresso_adaptativo("Banco", 75, 100, tipo="porcentagem")
                
                # Importar e usar o DbConnect
                import sys
                from pathlib import Path
                logica_dir = Path(__file__).parent.parent / "logica"
                if str(logica_dir) not in sys.path:
                    sys.path.insert(0, str(logica_dir))
                
                from DbConnect import processar_dados_completo
                
                # Inserção no banco com logs detalhados
                log_manager.log_banco_insercao_inicio(total_registros)
                
                inicio_tempo = datetime.now()
                sucesso_banco = processar_dados_completo(
                    credenciais=credenciais,
                    caminho_csv=arquivo_final,
                    nome_tabela=credenciais.get('table') if credenciais.get('table') else None
                )
                fim_tempo = datetime.now()
                
                tempo_execucao = str(fim_tempo - inicio_tempo).split('.')[0]  # Remove microssegundos
                
                # Finalização
                atualizar_progresso_adaptativo("Concluído", 100, 100, tipo="porcentagem")
                
                if sucesso_banco:
                    # Log de sucesso com detalhes
                    log_manager.log_banco_final(total_registros, tempo_execucao)
                    
                    # Limpar arquivos temporários
                    limpar_arquivos_temporarios(resultado['pasta_destino'])
                    log_manager.adicionar('info', 'Sistema', 'Arquivos temporários removidos', 'correto')
                    
                    # Mensagem de sucesso completo
                    msg = f"🎉 PROCESSAMENTO CONCLUÍDO COM SUCESSO!\n\n"
                    msg += f"📊 Estações processadas: {len(estacoes_baixadas)}\n"
                    msg += f"📋 Registros inseridos: {total_registros:,}\n"
                    msg += f"🗄️ Banco: {credenciais['host']}/{credenciais['database']}\n"
                    msg += f"⏱️ Tempo total: {tempo_execucao}\n"
                    
                    if credenciais.get('table'):
                        msg += f"📋 Tabela: {credenciais['table']}\n"
                    
                    messagebox.showinfo("✅ Processamento Concluído", msg)
                else:
                    log_manager.log_erro_geral('Banco', 'Falha na inserção dos dados')
                    
                    msg = f"❌ ERRO NA INSERÇÃO NO BANCO!\n\n"
                    msg += f"✅ Download e extração: OK\n"
                    msg += f"❌ Inserção no banco: FALHOU\n\n"
                    msg += f"📁 Arquivo consolidado disponível:\n{nome_arquivo}\n\n"
                    msg += f"Verifique o log para mais detalhes."
                    
                    messagebox.showerror("❌ Erro na Inserção", msg)
                    
            except Exception as e:
                log_manager.log_erro_geral('Sistema', f'Erro crítico: {str(e)}')
                messagebox.showerror("Erro Crítico", f"Erro durante o processamento:\n\n{str(e)}")
            finally:
                barra_progresso.pack_forget()
                label_status.configure(text="")
                processo_ativo = False
                if parar_flag:
                    log_manager.adicionar('aviso', 'Sistema', 'Processamento interrompido', 'error')
                    messagebox.showinfo("Cancelado", "Processamento interrompido pelo usuário.")
        
        Thread(target=tarefa_completa, daemon=True).start()
    
    login_banco = LoginBanco(ao_conectar_banco)
    login_banco.mostrar()

def obter_codigos_validos():
    """Obtém e valida os códigos inseridos pelo usuário"""
    texto_completo = entrada_codigo.get("1.0", "end-1c").strip()
    codigos = texto_completo.split(",")
    codigos = [c.strip() for c in codigos if c.strip().isdigit()]
    
    if not codigos:
        messagebox.showerror("Erro", "Digite um ou mais códigos de estação válidos, separados por vírgula.")
        return None
    
    return codigos

def parar_consulta():
    global parar_flag
    parar_flag = True
    log_manager.adicionar('aviso', 'Sistema', 'Solicitação de parada enviada', 'error')
    def reiniciar_apos_parar():
        import time
        time.sleep(1)
        texto_atual = entrada_codigo.get("1.0", "end-1c")
        janela.after(0, lambda: reiniciar_com_texto(texto_atual))
    Thread(target=reiniciar_apos_parar, daemon=True).start()

def reiniciar_com_texto(texto):
    os.environ['TEXTO_MANTIDO'] = texto
    reiniciar_interface(manter_texto=True)

def reiniciar_interface(manter_texto=True):
    texto_atual = entrada_codigo.get("1.0", "end-1c") if manter_texto else ""
    janela.destroy()
    if manter_texto and texto_atual:
        os.environ['TEXTO_MANTIDO'] = texto_atual
    os.execv(sys.executable, ['python'] + sys.argv)

def reiniciar_f5(event=None):
    reiniciar_interface(manter_texto=False)

def abrir_pasta():
    pasta_destino = criar_pasta_base()
    try:
        if platform.system() == "Windows":
            os.startfile(pasta_destino)
        elif platform.system() == "Darwin":
            subprocess.run(["open", pasta_destino])
        else:
            subprocess.run(["xdg-open", pasta_destino])
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir a pasta: {e}")

# [Continuar com o resto das funções da interface...]
# (selecionar_estacao, apagar_estacao_selecionada, atualizar_lista_historico, etc.)

def selecionar_estacao(codigo, botao):
    global estacao_selecionada, botao_selecionado
    
    if estacao_selecionada == codigo:
        estacao_selecionada = None
        if botao_selecionado:
            botao_selecionado.configure(
                fg_color="transparent", 
                border_color=CORES.border,
                text_color=CORES.text
            )
        botao_selecionado = None
        botao_apagar_codigo.configure(text="Selecione uma estação")
        return
    
    if botao_selecionado:
        botao_selecionado.configure(
            fg_color="transparent", 
            border_color=CORES.border,
            text_color=CORES.text
        )
    
    estacao_selecionada = codigo
    botao_selecionado = botao
    botao.configure(
        fg_color="transparent", 
        border_color=CORES.primary,
        text_color=CORES.text
    )
    botao_apagar_codigo.configure(text=f"Apagar {codigo}")
    
    adicionar_codigo_ao_input(codigo)

def apagar_estacao_selecionada():
    global estacao_selecionada, botao_selecionado, historico_estacoes
    
    if not estacao_selecionada:
        messagebox.showwarning("Aviso", "Selecione uma estação do histórico para apagar.")
        return
    
    try:
        codigo_removido = estacao_selecionada
        historico_estacoes.remove(estacao_selecionada)
        salvar_historico()
        atualizar_lista_historico()
        
        estacao_selecionada = None
        botao_selecionado = None
        botao_apagar_codigo.configure(text="Selecione uma estação")
        
        messagebox.showinfo("Sucesso", f"Estação {codigo_removido} removida do histórico.")
    except ValueError:
        messagebox.showerror("Erro", "Estação não encontrada no histórico.")

def atualizar_lista_historico():
    global estacao_selecionada, botao_selecionado, botoes_historico

    codigos_existentes = list(botoes_historico.keys())
    for codigo in codigos_existentes:
        if codigo not in historico_estacoes:
            botoes_historico[codigo].destroy()
            del botoes_historico[codigo]

    if estacao_selecionada and estacao_selecionada not in historico_estacoes:
        estacao_selecionada = None
        botao_selecionado = None
        botao_apagar_codigo.configure(text="Selecione uma estação")

    for i, codigo in enumerate(historico_estacoes):
        if codigo not in botoes_historico:
            botao_codigo = ctk.CTkButton(
                frame_scroll_historico,
                text=codigo,
                width=100,
                height=42,
                font=("Lato", 14, "bold"),
                text_color=CORES.surface,
                fg_color="transparent",
                hover_color=CORES.text_muted,
                corner_radius=15,
                border_width=2,
                border_color=CORES.text,
                command=lambda c=codigo: None
            )
            botao_codigo.configure(command=lambda c=codigo, b=botao_codigo: selecionar_estacao(c, b))
            botoes_historico[codigo] = botao_codigo

        selecionado = (codigo == estacao_selecionada)
        border_color = CORES.text if selecionado else CORES.border
        text_color = CORES.primary if selecionado else CORES.text
        
        botoes_historico[codigo].configure(
            border_color=border_color,
            text_color=text_color,
            fg_color="transparent"
        )
        botoes_historico[codigo].grid(row=i // 2, column=i % 2, padx=8, pady=6, sticky="ew")

        if selecionado:
            botao_selecionado = botoes_historico[codigo]

    for col in range(2):
        frame_scroll_historico.grid_columnconfigure(col, weight=1)

    frame_scroll_historico.update_idletasks()
    scrollable_historico._parent_canvas.yview_moveto(0.0)

def adicionar_codigo_ao_input(codigo):
    texto_atual = entrada_codigo.get("1.0", "end-1c").strip()
    
    if texto_atual == "Ex: 12345678, 87654321, 11223344":
        novo_texto = codigo
        entrada_codigo.configure(text_color=CORES.text)
    else:
        if texto_atual:
            novo_texto = texto_atual + ", " + codigo
        else:
            novo_texto = codigo
    
    salvar_no_historico(texto_atual if texto_atual != "Ex: 12345678, 87654321, 11223344" else "")
    
    entrada_codigo.delete("1.0", "end")
    entrada_codigo.insert("1.0", novo_texto)
    ajustar_altura_textbox()

def limpar_historico():
    global historico_estacoes, estacao_selecionada, botao_selecionado
    
    result = messagebox.askyesno("Confirmar", "Deseja realmente limpar todo o histórico?")
    if result:
        historico_estacoes = []
        estacao_selecionada = None
        botao_selecionado = None
        salvar_historico()
        atualizar_lista_historico()
        botao_apagar_codigo.configure(text="Selecione uma estação")

# [Funções de formatação e entrada de texto...]
def salvar_no_historico(texto):
    global historico_texto, posicao_historico
    if not historico_texto or historico_texto[-1] != texto:
        historico_texto.append(texto)
        if len(historico_texto) > 20:
            historico_texto.pop(0)
    posicao_historico = len(historico_texto)

def desfazer_ctrl_z(event=None):
    global posicao_historico
    if historico_texto and posicao_historico > 0:
        posicao_historico -= 1
        texto_anterior = historico_texto[posicao_historico]
        entrada_codigo.delete("1.0", "end")
        entrada_codigo.insert("1.0", texto_anterior)
        ajustar_altura_textbox()
    return "break"

def validar_input(char):
   return char.isdigit() or char in r", -_:;/\|"

def ajustar_altura_textbox():
    texto = entrada_codigo.get("1.0", "end-1c")
    largura_chars = 32
    linhas_por_conteudo = max(1, len(texto) // largura_chars + (1 if len(texto) % largura_chars > 0 else 0))
    linhas_quebra = texto.count('\n') + 1
    linhas_necessarias = max(linhas_por_conteudo, linhas_quebra)
    linhas_display = max(1, min(3, linhas_necessarias))
    altura_base = 40
    altura_por_linha = 22
    altura_nova = altura_base + (linhas_display - 1) * altura_por_linha
    
    if entrada_codigo.cget("height") != altura_nova:
        entrada_codigo.configure(height=altura_nova)

def converter_separadores_para_virgula(texto):
    texto_limpo = re.sub(r'[\s\-_:;/\\|]+', ', ', texto.strip())
    texto_limpo = re.sub(r',\s*,+', ', ', texto_limpo)
    texto_limpo = texto_limpo.strip(', ')
    return texto_limpo

def ao_pressionar_enter(event=None):
    if event and event.state & 0x1:
        return
    else:
        executar_consulta()
        return "break"

def ao_colar(event=None):
    try:
        texto_colado = janela.clipboard_get()
        texto_atual = entrada_codigo.get("1.0", "end-1c")
        
        if texto_atual.strip() != "Ex: 12345678, 87654321, 11223344":
            salvar_no_historico(texto_atual)
        
        if texto_atual.strip() == "Ex: 12345678, 87654321, 11223344":
            texto_atual = ""
            entrada_codigo.configure(text_color=CORES.text)
        
        texto_colado_limpo = converter_separadores_para_virgula(texto_colado)
        
        if texto_atual.strip():
            if not texto_atual.endswith(", ") and not texto_atual.endswith(","):
                novo_texto = texto_atual + ", " + texto_colado_limpo
            else:
                novo_texto = texto_atual + texto_colado_limpo
        else:
            novo_texto = texto_colado_limpo
        
        entrada_codigo.delete("1.0", "end")
        entrada_codigo.insert("1.0", novo_texto)
        janela.after(10, ajustar_altura_textbox)
        
    except Exception:
        pass
    
    return "break"

def ao_teclar(event):
    if event.keysym in ["Delete", "BackSpace"] or (len(event.char) == 1 and event.char.isprintable()):
        texto_atual = entrada_codigo.get("1.0", "end-1c")
        if texto_atual.strip() != "Ex: 12345678, 87654321, 11223344":
            salvar_no_historico(texto_atual)
    
    if len(event.char) == 1 and event.char.isprintable():
        if not validar_input(event.char):
            return "break"
    
    janela.after(1, ajustar_altura_textbox)

def processar_separadores_tempo_real(event):
    if event.keysym in ["space", "minus", "underscore", "semicolon", "colon", "slash", "backslash", "bar"]:
        posicao_cursor = entrada_codigo.index("insert")
        texto_atual = entrada_codigo.get("1.0", "end-1c")
        
        if texto_atual.strip() == "Ex: 12345678, 87654321, 11223344":
            return
        
        linha, coluna = map(int, posicao_cursor.split('.'))
        
        if coluna > 0:
            inicio_palavra = max(0, coluna - 10)
            fim_palavra = min(len(texto_atual), coluna + 1)
            
            texto_antes = texto_atual[:inicio_palavra]
            texto_regiao = texto_atual[inicio_palavra:fim_palavra]
            texto_depois = texto_atual[fim_palavra:]
            
            texto_regiao_convertido = re.sub(r'[\s\-_:;/\\|]+', ', ', texto_regiao)
            novo_texto = texto_antes + texto_regiao_convertido + texto_depois
            novo_texto = re.sub(r',\s*,+', ', ', novo_texto)
            
            if novo_texto != texto_atual:
                entrada_codigo.delete("1.0", "end")
                entrada_codigo.insert("1.0", novo_texto)
                
                nova_posicao = f"{linha}.{coluna + len(texto_regiao_convertido) - len(texto_regiao)}"
                try:
                    entrada_codigo.mark_set("insert", nova_posicao)
                except:
                    pass

def ao_focar_entrada(event):
    """Remove o placeholder quando o campo recebe foco"""
    texto_atual = entrada_codigo.get("1.0", "end-1c")
    if texto_atual == "Ex: 12345678, 87654321, 11223344":
        entrada_codigo.delete("1.0", "end")
        entrada_codigo.configure(text_color=CORES.text)

def ao_desfocar_entrada(event):
    """Adiciona o placeholder quando o campo perde foco e está vazio"""
    texto_atual = entrada_codigo.get("1.0", "end-1c").strip()
    if not texto_atual:
        entrada_codigo.insert("1.0", "Ex: 12345678, 87654321, 11223344")
        entrada_codigo.configure(text_color=CORES.text_muted)

# LAYOUT PRINCIPAL COM DESIGN MODERNO
janela.bind("<F5>", reiniciar_f5)

frame_container = ctk.CTkFrame(janela, fg_color="transparent")
frame_container.pack(expand=True, fill="both", padx=25, pady=25)

# Frame esquerdo - Interface principal
frame_principal = ctk.CTkFrame(
    frame_container, 
    fg_color=CORES.surface,
    corner_radius=20,
    border_width=1,
    border_color=CORES.border
)
frame_principal.pack(side="left", fill="both", expand=True, padx=(0, 15))

# Frame para centralizar conteúdo verticalmente
frame_central = ctk.CTkFrame(frame_principal, fg_color="transparent")
frame_central.pack(fill="both", expand=True, padx=20, pady=20)

# Título com gradiente visual
titulo = ctk.CTkLabel(
    frame_central, 
    text="⚡ SIPAMHIDRO", 
    font=("Lato", 24, "bold"),
    text_color=CORES.primary
)
titulo.pack(pady=(0, 5))

subtitulo = ctk.CTkLabel(
    frame_central, 
    text="Consulta de Estações Hidroweb", 
    font=("Lato", 14, "normal"),
    text_color=CORES.text_muted
)
subtitulo.pack(pady=(0, 20))

# Frame de entrada
frame_entrada = ctk.CTkFrame(frame_central, fg_color="transparent")
frame_entrada.pack(pady=15)

label_instrucao = ctk.CTkLabel(
    frame_entrada,
    text="Digite os códigos das estações (separados por vírgula):",
    font=("Lato", 13, "normal"),
    text_color=CORES.text
)
label_instrucao.pack(pady=(0, 8))

# Campo de entrada moderno
entrada_codigo = ctk.CTkTextbox(
    frame_entrada, 
    width=480, 
    height=40,
    font=("Lato", 14, "normal"),
    wrap="word",
    corner_radius=15,
    border_width=2,
    border_color=CORES.border,
    fg_color=CORES.background,
    text_color=CORES.text,
    scrollbar_button_color=CORES.primary,
    scrollbar_button_hover_color=CORES.purple
)
entrada_codigo.pack(pady=8)

# Inserindo placeholder moderno
entrada_codigo.insert("1.0", "Ex: 12345678, 87654321, 11223344")
entrada_codigo.configure(text_color=CORES.text_muted)

# Bindings do campo de entrada
entrada_codigo.bind("<Return>", ao_pressionar_enter)
entrada_codigo.bind("<Control-v>", ao_colar)
entrada_codigo.bind("<Command-v>", ao_colar)
entrada_codigo.bind("<Control-z>", desfazer_ctrl_z)
entrada_codigo.bind("<Command-z>", desfazer_ctrl_z)
entrada_codigo.bind("<KeyPress>", ao_teclar)
entrada_codigo.bind("<KeyRelease>", processar_separadores_tempo_real)
entrada_codigo.bind("<FocusIn>", ao_focar_entrada)
entrada_codigo.bind("<FocusOut>", ao_desfocar_entrada)

# Frame para botões principais
frame_botoes = ctk.CTkFrame(frame_central, fg_color="transparent")
frame_botoes.pack(pady=20)

# Botão Consultar - Azul vibrante com ícone
botao_consultar = ctk.CTkButton(
    frame_botoes,
    text="CONSULTAR",
    image=icones["search"],
    compound="left",
    command=lambda: Thread(target=lambda: executar_consulta("consultadas"), daemon=True).start(),
    width=140,
    height=45,
    fg_color=("#3498DB", "#2980B9"),
    hover_color=("#1ABC9C", "#16A085"),
    font=("Segoe UI", 14, "bold"),
    corner_radius=22,
    border_width=0,
    text_color="#FFFFFF",
    anchor="center"
)
botao_consultar.pack(side="left", padx=8)

# Botão Parar - Vermelho coral com ícone
botao_parar = ctk.CTkButton(
    frame_botoes,
    text="PARAR",
    image=icones["stop"],
    compound="left",
    command=parar_consulta,
    width=130,
    height=45,
    fg_color=("#E74C3C", "#C0392B"),
    hover_color=("#F1948A", "#E8675A"),
    font=("Segoe UI", 14, "bold"),
    corner_radius=22,
    border_width=1,
    border_color=("#C0392B", "#922B21"),
    text_color="#FFFFFF",
    anchor="center"
)
botao_parar.pack(side="left", padx=8)

# Botão Abrir Pasta - Verde esmeralda com ícone
botao_abrir_pasta = ctk.CTkButton(
    frame_botoes,
    text="PASTA",
    image=icones["folder"],
    compound="left",
    command=abrir_pasta,
    width=140,
    height=45,
    fg_color=("#E67E22", "#E67E22"),
    hover_color=("#E67E22", "#D35400"),
    font=("Segoe UI", 14, "bold"),
    corner_radius=22,
    border_width=0,
    text_color="#FFFFFF",
    anchor="center"
)
botao_abrir_pasta.pack(side="left", padx=8)

# Botão Enviar para Banco
botao_enviar_banco = ctk.CTkButton(
    frame_central,
    text="Enviar para Banco",
    image=icones["database"],
    compound="left",
    command=executar_consulta_e_banco,
    width=200,
    height=50,
    font=("Lato", 14, "bold"),
    corner_radius=20,
    fg_color="transparent",
    hover_color=CORES.sty,
    border_width=2,
    border_color=CORES.success,
    text_color=CORES.text
)
botao_enviar_banco.pack(pady=(15, 0))

# Barra de progresso moderna
barra_progresso = ctk.CTkProgressBar(
    frame_central,
    width=480,
    height=6,
    progress_color=CORES.success,
    fg_color=CORES.border,
    corner_radius=3
)

label_status = ctk.CTkLabel(
    frame_central, 
    text="",
    font=("Lato", 12, "normal"),
    text_color=CORES.text
)
label_status.pack(pady=8)

# LOG VISUAL MELHORADO - CONECTADO AO LogManager
frame_log = ctk.CTkFrame(
    frame_central, 
    fg_color=CORES.surface,
    corner_radius=15,
    border_width=1,
    border_color=CORES.border
)
frame_log.pack(pady=15, fill="both", expand=True)

# Título do log
titulo_log = ctk.CTkLabel(
    frame_log,
    text=" RELATÓRIO DE PROCESSOS",
    image=icones["relatorio"],
    compound="left",
    font=("Lato", 11, "bold"),
    text_color=CORES.text,
    anchor="w"
)
titulo_log.pack(padx=15, pady=(5, 5), anchor="w")

# Textbox scrollável para o log - CONECTADO AO LogManager
log_textbox = ctk.CTkTextbox(
    frame_log,
    width=450,
    height=230,
    font=("Consolas", 13, "normal"),
    corner_radius=10,
    border_width=1,
    border_color=CORES.border,
    fg_color=CORES.background,
    text_color=CORES.text,
    scrollbar_button_color=CORES.primary,
    scrollbar_button_hover_color=CORES.purple,
    wrap="word",
    state="disabled"
)
log_textbox.pack(padx=15, pady=(0, 15), fill="both", expand=True)

# CONFIGURAR O LOG MANAGER PARA USAR O TEXTBOX
log_manager.set_widget(log_textbox)

# Adicionar mensagem inicial ao log
log_manager.adicionar('inicio', 'Sistema', 'Interface carregada - Pronto para uso', 'start')

# Frame direito - Histórico com design moderno
frame_historico = ctk.CTkFrame(
    frame_container, 
    width=340, 
    corner_radius=20, 
    border_width=1, 
    border_color=CORES.border,
    fg_color=CORES.surface
)
frame_historico.pack(side="right", fill="y", padx=(15, 0))
frame_historico.pack_propagate(False)

# Título do histórico moderno
titulo_historico = ctk.CTkLabel(
    frame_historico,
    text="📋 Histórico de Estações",
    font=("Lato", 18, "bold"),
    text_color=CORES.text
)
titulo_historico.pack(pady=(25, 20))

# Frame para o scrollable
frame_scroll_container = ctk.CTkFrame(frame_historico, fg_color="transparent")
frame_scroll_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

# Scrollable frame para o histórico
scrollable_historico = ctk.CTkScrollableFrame(
    frame_scroll_container,
    width=290,
    height=360,
    corner_radius=15,
    fg_color=CORES.background,
    border_width=1,
    border_color=CORES.border,
    scrollbar_button_color=CORES.primary,
    scrollbar_button_hover_color=CORES.purple
)
scrollable_historico.pack(fill="both", expand=True)

# Frame interno do scroll para organizar os botões
frame_scroll_historico = ctk.CTkFrame(scrollable_historico, fg_color="transparent")
frame_scroll_historico.pack(fill="both", expand=True, padx=10, pady=10)

# Frame para botões de controle do histórico
frame_controle_historico = ctk.CTkFrame(frame_historico, fg_color="transparent")
frame_controle_historico.pack(pady=(0, 20))

# Botão para apagar estação selecionada
botao_apagar_codigo = ctk.CTkButton(
    frame_controle_historico,
    text="Selecione uma estação",
    image=icones["trash_orange"],
    compound="left",
    command=apagar_estacao_selecionada,
    width=220,
    height=35,
    font=("Lato", 12, "bold"),
    fg_color="transparent",
    hover_color=CORES.accent,
    corner_radius=15,
    border_width=2,
    border_color=CORES.accent,
    text_color=CORES.text
)
botao_apagar_codigo.pack(pady=8)

# Botão para limpar todo histórico
botao_limpar_historico = ctk.CTkButton(
    frame_controle_historico,
    text="Limpar Histórico",
    image=icones["trash_red"],
    compound="left",
    command=limpar_historico,
    width=220,
    height=35,
    font=("Lato", 12, "bold"),
    fg_color="transparent",
    hover_color=CORES.danger,
    corner_radius=15,
    border_width=2,
    border_color=CORES.danger,
    text_color=CORES.text
)
botao_limpar_historico.pack(pady=8)

# INICIALIZAÇÃO
# Criar estrutura de pastas ao inicializar
criar_estrutura_pastas()

# Carrega o histórico e inicializa a interface
carregar_historico()

# Salva estado inicial no histórico
texto_mantido = os.environ.get('TEXTO_MANTIDO', '')
if texto_mantido:
    entrada_codigo.delete("1.0", "end")
    entrada_codigo.insert("1.0", texto_mantido)
    entrada_codigo.configure(text_color=CORES.text)
    salvar_no_historico(texto_mantido)
    ajustar_altura_textbox()
    os.environ.pop('TEXTO_MANTIDO', None)
else:
    salvar_no_historico("")

# Atualiza a lista do histórico
atualizar_lista_historico()

# Força atualização do layout
def forcar_atualizacao_scroll():
    scrollable_historico.update_idletasks()
    frame_scroll_historico.update_idletasks()

janela.after_idle(forcar_atualizacao_scroll)

# Inicia o loop da interface
if __name__ == "__main__":
    janela.mainloop()