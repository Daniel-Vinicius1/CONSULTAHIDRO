# scripts/logica/play.py
from playwright.sync_api import sync_playwright
import getpass
import os
import time
import shutil
from glob import glob
from consumo import criar_pasta_base, verificar_arquivo_existe
from pathlib import Path
import re
from datetime import datetime

def aguardar_download_completo(pasta_downloads, codigo_estacao, timeout=8):
    """Aguarda o download ser completado para a estação específica"""
    padrao = f'Estacao_{codigo_estacao}_CSV_*.zip'
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        arquivos = glob(os.path.join(pasta_downloads, padrao))
        if arquivos:
            arquivo = arquivos[0]
            
            if os.path.exists(arquivo) and os.path.getsize(arquivo) > 0:
                time.sleep(0.1)
                if os.path.exists(arquivo):
                    return True
                
        time.sleep(0.03)
    
    return False

def aguardar_qualquer_download_completo(pasta_downloads, timeout=8):
    """Aguarda qualquer download ser completado"""
    padrao = 'Estacao_*_CSV_*.zip'
    start_time = time.time()
    arquivos_iniciais = set(glob(os.path.join(pasta_downloads, padrao)))
    
    while time.time() - start_time < timeout:
        arquivos_atuais = set(glob(os.path.join(pasta_downloads, padrao)))
        novos_arquivos = arquivos_atuais - arquivos_iniciais
        
        if novos_arquivos:
            # Verifica se algum dos novos arquivos está completo
            for arquivo in novos_arquivos:
                if os.path.exists(arquivo) and os.path.getsize(arquivo) > 0:
                    time.sleep(0.1)  # Pequena pausa para garantir que o download terminou
                    if os.path.exists(arquivo):
                        return arquivo
                        
        time.sleep(0.03)
    
    return None

def extrair_codigo_do_arquivo(nome_arquivo):
    """Extrai o código da estação do nome do arquivo"""
    match = re.search(r'Estacao_(\d+)_CSV_', nome_arquivo)
    return match.group(1) if match else None

def obter_estacao_atual_carregada(page):
    """
    Obtém o código da estação atualmente carregada na página.
    Retorna o código da estação ou None se não conseguir obter.
    """
    try:
        # Primeiro seletor CSS
        elemento_estacao = page.locator('#mat-tab-content-0-0 > div > ana-card > mat-card > mat-card-content > ana-dados-convencionais-list > div > div.mat-elevation-z8.example-container > table > tbody > tr:nth-child(1) > td.mat-cell.cdk-column-id.mat-column-id.ng-star-inserted > a').first
        elemento_estacao.wait_for(timeout=2000, state='visible')
        codigo_carregado = elemento_estacao.text_content().strip()
        return codigo_carregado
        
    except:
        try:
            # XPath alternativo
            elemento_estacao = page.locator('xpath=//*[@id="mat-tab-content-0-0"]/div/ana-card/mat-card/mat-card-content/ana-dados-convencionais-list/div/div[1]/table/tbody/tr[1]/td[2]/a').first
            elemento_estacao.wait_for(timeout=2000, state='visible')
            codigo_carregado = elemento_estacao.text_content().strip()
            return codigo_carregado
            
        except:
            try:
                # Seletor mais genérico
                elemento_estacao = page.locator('td.mat-column-id a').first
                elemento_estacao.wait_for(timeout=2000, state='visible')
                codigo_carregado = elemento_estacao.text_content().strip()
                return codigo_carregado
                
            except:
                return None

def validar_e_corrigir_estacao_carregada_rapida(page, codigo_esperado, max_tentativas=2):
    """
    Versão mais rápida da validação - apenas 2 tentativas máximo
    Retorna True se conseguiu carregar a estação correta, False caso contrário.
    """
    print(f"    🔍 Validando estação carregada...")
    
    for tentativa in range(max_tentativas):
        try:
            # Aguarda a tabela carregar - timeout menor
            tabela = page.locator('table.mat-table').first
            tabela.wait_for(timeout=2000, state='visible')
            
            # Obtém o código da estação atual
            codigo_carregado = obter_estacao_atual_carregada(page)
            
            if codigo_carregado:
                print(f"    📋 Estação carregada: {codigo_carregado} (esperada: {codigo_esperado})")
                
                if codigo_carregado == codigo_esperado:
                    print(f"    ✅ Estação correta já carregada!")
                    return True
                else:
                    print(f"    ❌ Estação incorreta! Corrigindo para {codigo_esperado}...")
                    
                    # Corrige o campo de input
                    try:
                        campo = page.locator('#mat-input-0').first
                        campo.wait_for(timeout=1000)
                    except:
                        campo = page.locator('xpath=//*[@id="mat-input-0"]').first
                        campo.wait_for(timeout=1000)
                    
                    campo.fill("")
                    time.sleep(0.1)
                    campo.fill(codigo_esperado)
                    campo.press("Enter")
                    
                    time.sleep(0.3)  # Reduzido o tempo de espera
                    continue
            else:
                print(f"    ⚠️ Não foi possível obter código da estação carregada (tentativa {tentativa + 1})")
                if tentativa < max_tentativas - 1:
                    time.sleep(0.2)  # Reduzido o tempo de espera
                    continue
                else:
                    # MUDANÇA CRÍTICA: NÃO assume mais que está correto
                    # Se não conseguiu validar, retorna False
                    print(f"    ❌ Não foi possível validar a estação após {max_tentativas} tentativas")
                    return False
                    
        except Exception as e:
            print(f"    ❌ Erro na validação (tentativa {tentativa + 1}): {str(e)}")
            if tentativa < max_tentativas - 1:
                time.sleep(0.2)  # Reduzido o tempo de espera
                continue
            else:
                return False
    
    return True

def limpar_downloads_temp_especificos(pasta_downloads, excluir_codigo=None):
    """Remove arquivos temporários específicos da pasta de downloads"""
    padrao = 'Estacao_*_CSV_*.zip'
    arquivos = glob(os.path.join(pasta_downloads, padrao))
    
    for arquivo in arquivos:
        try:
            nome_arquivo = os.path.basename(arquivo)
            codigo_arquivo = extrair_codigo_do_arquivo(nome_arquivo)
            
            # Se excluir_codigo for especificado, só remove arquivos de outros códigos
            if excluir_codigo is None or codigo_arquivo != excluir_codigo:
                os.remove(arquivo)
                print(f"    🧹 Removido arquivo temp: {nome_arquivo}")
        except Exception as e:
            print(f"    ⚠️ Erro ao remover arquivo temp: {e}")

def verificar_se_deve_substituir(pasta_destino, codigo_estacao, novo_arquivo_temp):
    """
    Verifica se deve substituir arquivo existente baseado no tamanho.
    Retorna True se deve substituir, False caso contrário.
    """
    try:
        base_path = Path(pasta_destino)
        padrao = f'Estacao_{codigo_estacao}_CSV_*.zip'
        
        # Busca arquivos existentes da mesma estação
        arquivos_existentes = list(base_path.glob(padrao))
        
        if not arquivos_existentes:
            return True  # Não existe arquivo, pode baixar
        
        # Obter tamanho do novo arquivo
        novo_tamanho = os.path.getsize(novo_arquivo_temp)
        
        # Encontrar o arquivo mais recente
        arquivo_mais_recente = None
        data_mais_recente = None
        
        for arquivo_path in arquivos_existentes:
            nome = arquivo_path.name
            match = re.search(r'Estacao_(\d+)_CSV_(\d{4}-\d{2}-\d{2})T', nome)
            if match:
                data_str = match.group(2)
                try:
                    data_dt = datetime.strptime(data_str, "%Y-%m-%d")
                    if data_mais_recente is None or data_dt > data_mais_recente:
                        data_mais_recente = data_dt
                        arquivo_mais_recente = arquivo_path
                except ValueError:
                    continue
        
        if arquivo_mais_recente is None:
            return True  # Não conseguiu determinar arquivo mais recente, permite download
        
        # Comparar tamanhos
        tamanho_existente = arquivo_mais_recente.stat().st_size
        
        if novo_tamanho != tamanho_existente:
            print(f"    📊 Tamanhos diferentes - Existente: {tamanho_existente} bytes, Novo: {novo_tamanho} bytes")
            return True  # Tamanhos diferentes, deve substituir
        else:
            print(f"    ⚖️ Mesmo tamanho ({tamanho_existente} bytes) - Mantendo arquivo existente")
            return False  # Mesmo tamanho, não precisa substituir
            
    except Exception as e:
        print(f"    ⚠️ Erro ao verificar substituição: {e}")
        return True  # Em caso de erro, permite download

def remover_arquivos_antigos_da_estacao(pasta_destino, codigo_estacao):
    """Remove todos os arquivos antigos da estação especificada"""
    try:
        base_path = Path(pasta_destino)
        padrao = f'Estacao_{codigo_estacao}_CSV_*.zip'
        
        arquivos_existentes = list(base_path.glob(padrao))
        
        for arquivo in arquivos_existentes:
            arquivo.unlink()
            print(f"    🗑️ Removido arquivo antigo: {arquivo.name}")
            
    except Exception as e:
        print(f"    ❌ Erro ao remover arquivos antigos: {e}")

def mover_arquivo_para_destino(arquivo_origem, pasta_destino, codigo_estacao_esperado):
    """Move arquivo para destino verificando se é da estação correta"""
    
    if not os.path.exists(arquivo_origem):
        return False
    
    nome_arquivo = os.path.basename(arquivo_origem)
    codigo_arquivo = extrair_codigo_do_arquivo(nome_arquivo)
    
    # Verifica se o arquivo baixado é da estação correta
    if codigo_arquivo != codigo_estacao_esperado:
        print(f"    ⚠️ Arquivo incorreto: esperado {codigo_estacao_esperado}, obtido {codigo_arquivo}")
        # Remove o arquivo incorreto
        try:
            os.remove(arquivo_origem)
            print(f"    🗑️ Arquivo incorreto removido: {nome_arquivo}")
        except:
            pass
        return False
    
    arquivo_destino = os.path.join(pasta_destino, nome_arquivo)
    
    try:
        # Verificar se deve substituir baseado no tamanho
        if not verificar_se_deve_substituir(pasta_destino, codigo_estacao_esperado, arquivo_origem):
            # Remove o arquivo temporário e retorna True (considera como sucesso)
            os.remove(arquivo_origem)
            return True
        
        # Remove arquivos antigos da mesma estação antes de mover o novo
        remover_arquivos_antigos_da_estacao(pasta_destino, codigo_estacao_esperado)
        
        # Move o novo arquivo
        shutil.move(arquivo_origem, arquivo_destino)
        return True
        
    except Exception as e:
        print(f"    ❌ Erro ao mover: {str(e)}")
        return False

def processar_estacao_rapida(page, codigo, pasta_downloads_temp, pasta_destino, idx, total, callback_progresso=None, parar_callback=None, tentativa=1):
   if parar_callback and parar_callback():
       return False
       
   tentativa_text = f" (Retry {tentativa})" if tentativa > 1 else ""
   print(f"[{idx}/{total}] 🚀 {codigo}{tentativa_text}")
   
   if callback_progresso:
       texto_progresso = f"Baixando {codigo}" + (f" - Retry {tentativa}" if tentativa > 1 else "")
       callback_progresso(idx, total, texto_progresso)
   
   try:
       # Limpa downloads temporários antes de começar (exceto da estação atual se existir)
       limpar_downloads_temp_especificos(pasta_downloads_temp, codigo)
       
       # Preenche o campo de busca
       try:
           campo = page.locator('#mat-input-0').first
           campo.wait_for(timeout=1500)
       except:
           campo = page.locator('xpath=//*[@id="mat-input-0"]').first
           campo.wait_for(timeout=1500)
       
       campo.fill("")
       campo.fill(codigo)
       campo.press("Enter")
       
       time.sleep(0.1)
       
       # Verifica se existe algum resultado (tabela com dados)
       try:
           tabela = page.locator('table.mat-table').first
           tabela.wait_for(timeout=3000, state='visible')
       except:
           print(f"    ❌ Estação {codigo} não encontrada - não existe ou não possui dados")
           return "estacao_inexistente"
       
       # VERIFICAÇÃO RÁPIDA DO BOTÃO - SEM MÚLTIPLAS TENTATIVAS
       # Tenta encontrar o botão de download IMEDIATAMENTE
       botao_encontrado = False
       botao_download = None
       
       try:
           # Primeira tentativa - seletor principal
           botao_download = page.locator('td.mat-column-csv button').first
           botao_download.wait_for(timeout=1500, state='visible')
           if botao_download.is_visible() and botao_download.is_enabled():
               botao_encontrado = True
       except:
           try:
               # Segunda tentativa - seletor específico
               botao_download = page.locator('#mat-tab-content-0-0 > div > ana-card > mat-card > mat-card-content > ana-dados-convencionais-list > div > div.mat-elevation-z8.example-container > table > tbody > tr:nth-child(1) > td.mat-cell.cdk-column-csv.mat-column-csv.mat-table-sticky.ng-star-inserted > button').first
               botao_download.wait_for(timeout=1000, state='visible')
               if botao_download.is_visible() and botao_download.is_enabled():
                   botao_encontrado = True
           except:
               try:
                   # Terceira tentativa - seletor genérico
                   botao_download = page.locator('button[mattooltip*="CSV"], button[title*="CSV"], td.mat-column-csv button, button:has-text("CSV")').first
                   botao_download.wait_for(timeout=1000, state='visible')
                   if botao_download.is_visible() and botao_download.is_enabled():
                       botao_encontrado = True
               except:
                   pass
       
       # Se não encontrou o botão, descarta IMEDIATAMENTE
       if not botao_encontrado:
           print(f"    ❌ Estação {codigo} não possui dados para download - botão CSV não encontrado")
           return "estacao_inexistente"
       
       # VALIDAÇÃO DA ESTAÇÃO CARREGADA - APENAS SE O BOTÃO FOI ENCONTRADO
       # Valida e verifica se o botão ainda existe após correção
       if not validar_e_corrigir_estacao_carregada_rapida(page, codigo):
           print(f"    ❌ Não foi possível carregar a estação {codigo} corretamente")
           return "estacao_inexistente"
       
       # REVERIFICA O BOTÃO APÓS VALIDAÇÃO/CORREÇÃO
       # Se houve correção, precisa verificar se o botão ainda existe
       try:
           botao_download = page.locator('td.mat-column-csv button').first
           botao_download.wait_for(timeout=1000, state='visible')
           if not (botao_download.is_visible() and botao_download.is_enabled()):
               raise Exception("Botão não visível/habilitado")
       except:
           try:
               botao_download = page.locator('#mat-tab-content-0-0 > div > ana-card > mat-card > mat-card-content > ana-dados-convencionais-list > div > div.mat-elevation-z8.example-container > table > tbody > tr:nth-child(1) > td.mat-cell.cdk-column-csv.mat-column-csv.mat-table-sticky.ng-star-inserted > button').first
               botao_download.wait_for(timeout=800, state='visible')
               if not (botao_download.is_visible() and botao_download.is_enabled()):
                   raise Exception("Botão não visível/habilitado")
           except:
               print(f"    ❌ Estação {codigo} não possui botão de download após validação")
               return "estacao_inexistente"
       
       # PROCESSO DE DOWNLOAD - botão já foi encontrado e validado
       try:
           # Estratégia única e direta: usar expect_download
           with page.expect_download(timeout=8000) as download_info:
               botao_download.click()
           
           download = download_info.value
           nome_arquivo = download.suggested_filename
           caminho_temp = os.path.join(pasta_downloads_temp, nome_arquivo)
           
           print(f"    💾 {nome_arquivo}")
           
           # Verifica se o arquivo baixado é da estação correta antes mesmo de salvar
           codigo_arquivo = extrair_codigo_do_arquivo(nome_arquivo)
           if codigo_arquivo != codigo:
               print(f"    ⚠️ Download incorreto: esperado {codigo}, obtido {codigo_arquivo}")
               return False
           
           download.save_as(caminho_temp)
           
           # Aguarda o arquivo estar realmente disponível
           if aguardar_download_completo(pasta_downloads_temp, codigo, timeout=5):
               if mover_arquivo_para_destino(caminho_temp, pasta_destino, codigo):
                   print(f"    ✅ OK!")
                   return True
               else:
                   return False
           else:
               print(f"    ⏱️ Timeout no download específico")
               return False
               
       except Exception as e:
           print(f"    ❌ Erro no download: {str(e)}")
           # Se falhar no download, é problema técnico, não de estação inexistente
           return False
           
   except Exception as e:
       print(f"    ❌ Erro geral: {str(e)}")
       return False
    
def processar_lote_com_fallback(page, estacoes, pasta_downloads_temp, pasta_destino, callback_progresso=None, parar_callback=None):
    estacoes_baixadas = []
    estacoes_problematicas = []
    estacoes_inexistentes = []
    estacoes_sem_dados = []
    total_estacoes = len(estacoes)
    
    print(f"\n🚀 PROCESSAMENTO RÁPIDO - {total_estacoes} ESTAÇÕES")
    
    # PRIMEIRA TENTATIVA
    for idx, codigo in enumerate(estacoes, start=1):
        if parar_callback and parar_callback():
            print("⏹️ Interrompido")
            break
            
        resultado = processar_estacao_rapida(
            page, codigo, pasta_downloads_temp, pasta_destino, 
            idx, total_estacoes, callback_progresso, parar_callback, tentativa=1
        )
        
        if resultado == True:
            estacoes_baixadas.append(codigo)
        elif resultado == "estacao_inexistente":
            estacoes_inexistentes.append(codigo)
        elif resultado == "estacao_sem_dados":
            estacoes_sem_dados.append(codigo)
        else:  # False ou outros erros
            estacoes_problematicas.append(codigo)
        
        if idx < total_estacoes:
            time.sleep(0.02)
    
    # SEGUNDA TENTATIVA - APENAS para estações que tiveram problemas técnicos (não inexistentes)
    if estacoes_problematicas and not (parar_callback and parar_callback()):
        print(f"\n🔄 RETRY 2ª TENTATIVA - {len(estacoes_problematicas)} ESTAÇÕES")
        
        estacoes_segunda_tentativa = []
        
        for idx, codigo in enumerate(estacoes_problematicas, start=1):
            if parar_callback and parar_callback():
                break
            
            idx_progress = total_estacoes + idx
            total_progress = total_estacoes + len(estacoes_problematicas)
            
            resultado = processar_estacao_rapida(
                page, codigo, pasta_downloads_temp, pasta_destino,
                idx_progress, total_progress, callback_progresso, parar_callback, tentativa=2
            )
            
            if resultado == True:
                estacoes_baixadas.append(codigo)
                print(f"    🎉 Recuperada na 2ª tentativa!")
            elif resultado == "estacao_inexistente":
                estacoes_inexistentes.append(codigo)
                print(f"    ❌ Confirmado: estação {codigo} não existe")
            elif resultado == "estacao_sem_dados":
                estacoes_sem_dados.append(codigo)
                print(f"    ❌ Confirmado: estação {codigo} sem dados para download")
            else:  # False ou outros erros
                estacoes_segunda_tentativa.append(codigo)
            
            if idx < len(estacoes_problematicas):
                time.sleep(0.05)
        
        estacoes_problematicas = estacoes_segunda_tentativa
    
    # TERCEIRA TENTATIVA - APENAS para estações que continuaram com problemas técnicos
    if estacoes_problematicas and not (parar_callback and parar_callback()):
        print(f"\n🔄 RETRY 3ª TENTATIVA - {len(estacoes_problematicas)} ESTAÇÕES")
        
        estacoes_finalmente_falharam = []
        
        for idx, codigo in enumerate(estacoes_problematicas, start=1):
            if parar_callback and parar_callback():
                break
            
            # Ajustar o progress considerando as tentativas anteriores
            idx_progress = total_estacoes + len(estacoes) + idx
            total_progress = total_estacoes + len(estacoes) + len(estacoes_problematicas)
            
            print(f"🔁 3ª Tentativa {codigo}")
            
            resultado = processar_estacao_rapida(
                page, codigo, pasta_downloads_temp, pasta_destino,
                idx_progress, total_progress, callback_progresso, parar_callback, tentativa=3
            )
            
            if resultado == True:
                estacoes_baixadas.append(codigo)
                print(f"    🎉 Recuperada na 3ª tentativa!")
            elif resultado == "estacao_inexistente":
                estacoes_inexistentes.append(codigo)
                print(f"    ❌ Confirmado: estação {codigo} não existe")
            elif resultado == "estacao_sem_dados":
                estacoes_sem_dados.append(codigo)
                print(f"    ❌ Confirmado: estação {codigo} sem dados")
            else:  # False ou outros erros
                estacoes_finalmente_falharam.append(codigo)
            
            if idx < len(estacoes_problematicas):
                time.sleep(0.1)  # Pausa um pouco maior na 3ª tentativa
        
        estacoes_problematicas = estacoes_finalmente_falharam
    
    return estacoes_baixadas, estacoes_problematicas, estacoes_inexistentes, estacoes_sem_dados

def baixar_estacoes(estacoes, callback_progresso=None, parar_callback=None, tipo_consulta="normal"):
    """
    Baixa estações com suporte a diferentes tipos de consulta.
    
    Args:
        estacoes: Lista de códigos das estações
        callback_progresso: Função de callback para progresso
        parar_callback: Função de callback para parar
        tipo_consulta: "normal" para pasta principal, "consultadas" para pasta consultadas
    """
    pasta_destino = criar_pasta_base(tipo_consulta)
    usuario = getpass.getuser()
    pasta_temp = f"C:\\Users\\{usuario}\\Downloads"
    
    print(f"📂 Destino: {pasta_destino}")
    print(f"🎯 Total: {len(estacoes)} estações")
    print(f"📋 Tipo de consulta: {tipo_consulta}")
    
    # Limpeza inicial de arquivos temporários
    limpar_downloads_temp_especificos(pasta_temp)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-features=TranslateUI,VizDisplayCompositor',
                '--disable-ipc-flooding-protection',
                '--disable-logging',
                '--disable-default-apps',
                '--disable-component-extensions-with-background-pages',
                '--fast-start',
                '--aggressive-cache-discard',
                '--memory-pressure-off',
                '--max_old_space_size=4096'
            ]
        )
        
        context = browser.new_context(
            accept_downloads=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ignore_https_errors=True,
            bypass_csp=True,
            viewport={'width': 1280, 'height': 720}
        )
        
        page = context.new_page()
        
        page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}", lambda route: route.abort())
        page.route("**/*.css", lambda route: route.fulfill(status=200, body=""))
        page.route("**/analytics/**", lambda route: route.abort())
        page.route("**/gtag/**", lambda route: route.abort())
        page.route("**/google-analytics.**", lambda route: route.abort())
        
        print("🌐 Acessando site...")
        try:
            page.goto("https://www.snirh.gov.br/hidroweb/serieshistoricas", 
                     timeout=6000, wait_until='domcontentloaded')
        except:
            page.goto("https://www.snirh.gov.br/hidroweb/serieshistoricas", 
                     timeout=12000, wait_until='networkidle')
        
        time.sleep(0.2)
        
        estacoes_baixadas, estacoes_falharam, estacoes_inexistentes, estacoes_sem_dados = processar_lote_com_fallback(
            page, estacoes, pasta_temp, pasta_destino, callback_progresso, parar_callback
        )
        
        browser.close()
    
    # Limpeza final de arquivos temporários
    limpar_downloads_temp_especificos(pasta_temp)
    
    total_solicitadas = len(estacoes)
    total_baixadas = len(estacoes_baixadas)
    total_falharam = len(estacoes_falharam) 
    total_inexistentes = len(estacoes_inexistentes)
    total_sem_dados = len(estacoes_sem_dados)
    
    print(f"\n📊 RESULTADO FINAL")
    print(f"   📥 Baixadas: {total_baixadas}/{total_solicitadas}")
    print(f"   📁 Local: {pasta_destino}")
    
    if total_baixadas > 0:
        taxa_sucesso = (total_baixadas/total_solicitadas*100)
        print(f"   📈 Taxa: {taxa_sucesso:.1f}%")
    
    # Relatório detalhado dos problemas
    if estacoes_falharam:
        print(f"   ❌ Falharam após 3 tentativas: {', '.join(estacoes_falharam)}")
        print(f"      💡 Possíveis problemas técnicos ou de conectividade")
    
    if estacoes_inexistentes:
        print(f"   🚫 Estações inexistentes: {', '.join(estacoes_inexistentes)}")
        print(f"      💡 Códigos não encontrados no sistema ou sem botão de download")
    
    if estacoes_sem_dados:
        print(f"   📋 Sem dados para download: {', '.join(estacoes_sem_dados)}")
        print(f"      💡 Estações existem mas não possuem dados CSV disponíveis")
    
    if not estacoes_falharam and not estacoes_inexistentes and not estacoes_sem_dados:
        print(f"   🎉 TODAS PROCESSADAS COM SUCESSO!")
    
    return {
        'sucesso': total_baixadas == total_solicitadas,
        'baixadas': estacoes_baixadas,
        'falharam': estacoes_falharam,
        'inexistentes': estacoes_inexistentes,
        'sem_dados': estacoes_sem_dados,
        'pasta_destino': pasta_destino
    }