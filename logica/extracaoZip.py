# scripts/logica/extracaoZip.py - VERSÃO CORRIGIDA E COMPLETA
import zipfile
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import getpass

def extrair_arquivos_cotas(caminho_pasta_zip, caminho_saida=None, callback_progresso=None):
    """
    Extrai apenas os arquivos *_Cotas.csv de todos os ZIPs na pasta especificada.
    
    Args:
        caminho_pasta_zip (str): Caminho da pasta contendo os arquivos ZIP
        caminho_saida (str, optional): Pasta de destino. Se None, usa a mesma pasta dos ZIPs
        callback_progresso (callable, optional): Função para callback de progresso
    
    Returns:
        list: Lista de arquivos CSV extraídos
    """
    if caminho_saida is None:
        caminho_saida = caminho_pasta_zip
    
    # Garante que a pasta de saída existe
    os.makedirs(caminho_saida, exist_ok=True)
    
    arquivos_extraidos = []
    
    print(f"🔍 Procurando arquivos ZIP em: {caminho_pasta_zip}")
    
    # Listar arquivos ZIP
    arquivos_zip = [f for f in os.listdir(caminho_pasta_zip) if f.endswith('.zip')]
    total_zips = len(arquivos_zip)
    
    if callback_progresso:
        callback_progresso("Extração", 15, 100, tipo="porcentagem")
    
    # Itera sobre todos os arquivos ZIP na pasta
    for i, arquivo_zip in enumerate(arquivos_zip, 1):
        caminho_zip = os.path.join(caminho_pasta_zip, arquivo_zip)
        
        # Callback de progresso durante extração
        if callback_progresso:
            progresso = 15 + (i / total_zips) * 20  # 15% a 35%
            callback_progresso("Extração", int(progresso), 100, tipo="porcentagem")
        
        try:
            # Abre o arquivo ZIP
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                # Itera sobre todos os arquivos dentro do ZIP
                for arquivo in zip_ref.namelist():
                    # Verifica se o arquivo termina com '_Cotas.csv'
                    if arquivo.endswith('_Cotas.csv'):
                        # Extrai o arquivo CSV para a pasta de saída
                        zip_ref.extract(arquivo, caminho_saida)
                        arquivos_extraidos.append(arquivo)
                        print(f'✅ Extraído: {arquivo} de {arquivo_zip}')
                        
        except Exception as e:
            print(f'❌ Erro ao processar {arquivo_zip}: {str(e)}')
            continue
    
    print(f"📊 Total de arquivos extraídos: {len(arquivos_extraidos)}")
    return arquivos_extraidos

def consolidar_arquivos_cotas(pasta_csv, nome_arquivo_saida=None, callback_progresso=None):
    """
    Consolida todos os arquivos *_Cotas.csv em um único arquivo no padrão do banco SIPAM.
    VERSÃO MELHORADA com callback de progresso e melhor tratamento de datas e erros.
    
    Args:
        pasta_csv (str): Pasta contendo os arquivos CSV extraídos
        nome_arquivo_saida (str, optional): Nome do arquivo de saída. Se None, usa padrão com data
        callback_progresso (callable, optional): Função para callback de progresso
    
    Returns:
        str: Caminho do arquivo consolidado criado
    """
    if nome_arquivo_saida is None:
        data_atual = datetime.now().strftime('%Y-%m-%d')
        nome_arquivo_saida = f'estacao_hidroweb_novosregistros_{data_atual}.csv'
    
    caminho_arquivo_saida = os.path.join(pasta_csv, nome_arquivo_saida)
    
    print(f"🔄 Consolidando arquivos CSV em: {caminho_arquivo_saida}")
    
    # Inicializar um DataFrame vazio para armazenar todos os dados
    df_final = pd.DataFrame()
    
    # Listar todos os arquivos CSV na pasta
    arquivos_csv = [f for f in os.listdir(pasta_csv) if f.endswith('_Cotas.csv')]
    
    if not arquivos_csv:
        print("❌ Nenhum arquivo *_Cotas.csv encontrado na pasta!")
        return None
    
    print(f"📋 Processando {len(arquivos_csv)} arquivos CSV...")
    
    # Número de linhas de metadados antes do cabeçalho
    linhas_para_pular = 15
    
    # Contadores para estatísticas
    total_arquivos_processados = 0
    total_arquivos_com_erro = 0
    total_registros_processados = 0
    
    # Callback inicial da consolidação
    if callback_progresso:
        callback_progresso("Extração", 35, 100, tipo="porcentagem")
    
    # Iterar sobre cada arquivo CSV
    for i, arquivo in enumerate(arquivos_csv, 1):
        print(f"  [{i}/{len(arquivos_csv)}] Processando: {arquivo}")
        
        # Callback de progresso durante consolidação
        if callback_progresso:
            progresso_atual = 35 + (i / len(arquivos_csv)) * 50  # 35% a 85%
            callback_progresso("Extração", int(progresso_atual), 100, tipo="porcentagem")
        
        # Caminho completo para o arquivo CSV
        csv_path = os.path.join(pasta_csv, arquivo)
        
        try:
            # Tentar ler com diferentes codificações
            df = None
            encodings_para_testar = ['ISO-8859-1', 'utf-8', 'cp1252']
            
            for encoding in encodings_para_testar:
                try:
                    df = pd.read_csv(csv_path, sep=';', skiprows=linhas_para_pular, encoding=encoding)
                    print(f"    ✅ Lido com encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"    ⚠️ Erro com encoding {encoding}: {e}")
                    continue
            
            if df is None:
                print(f"    ❌ Não foi possível ler o arquivo com nenhum encoding testado")
                total_arquivos_com_erro += 1
                continue
            
            # Verificar se o DataFrame está vazio
            if df.empty:
                print(f"    ⚠️ Arquivo vazio ou sem dados válidos")
                total_arquivos_com_erro += 1
                continue
            
            # Definir colunas esperadas
            colunas_esperadas = [
                'EstacaoCodigo', 'Data', 'hora', 'TipoMedicaoCotas', 'NivelConsistencia',
                'Cota01', 'Cota02', 'Cota03', 'Cota04', 'Cota05', 'Cota06', 'Cota07', 'Cota08', 'Cota09',
                'Cota10', 'Cota11', 'Cota12', 'Cota13', 'Cota14', 'Cota15', 'Cota16', 'Cota17', 'Cota18',
                'Cota19', 'Cota20', 'Cota21', 'Cota22', 'Cota23', 'Cota24', 'Cota25', 'Cota26', 'Cota27',
                'Cota28', 'Cota29', 'Cota30', 'Cota31', 'Maxima', 'Minima', 'Media',
                'Cota01Status', 'Cota02Status', 'Cota03Status', 'Cota04Status', 'Cota05Status', 'Cota06Status',
                'Cota07Status', 'Cota08Status', 'Cota09Status', 'Cota10Status', 'Cota11Status', 'Cota12Status',
                'Cota13Status', 'Cota14Status', 'Cota15Status', 'Cota16Status', 'Cota17Status', 'Cota18Status',
                'Cota19Status', 'Cota20Status', 'Cota21Status', 'Cota22Status', 'Cota23Status', 'Cota24Status',
                'Cota25Status', 'Cota26Status', 'Cota27Status', 'Cota28Status', 'Cota29Status', 'Cota30Status',
                'Cota31Status', 'MaximaStatus', 'MinimaStatus', 'MediaStatus'
            ]
            
            # Verificar se todas as colunas esperadas existem
            colunas_faltantes = [col for col in colunas_esperadas if col not in df.columns]
            
            if colunas_faltantes:
                print(f"    ⚠️ Arquivo {arquivo} não possui todas as colunas esperadas")
                print(f"    📋 Colunas disponíveis: {list(df.columns)}")
                print(f"    ❌ Colunas faltantes: {colunas_faltantes}")
                total_arquivos_com_erro += 1
                continue
            
            # Selecionar e renomear colunas
            df_selecionado = df[colunas_esperadas].copy()
            
            # Renomear colunas para padrão do banco
            novos_nomes = [
                'codigo_estacao', 'data', 'hora', 'tipo_medicao_cota', 'nivel_consistencia',
                'cota01', 'cota02', 'cota03', 'cota04', 'cota05', 'cota06', 'cota07', 'cota08', 'cota09',
                'cota10', 'cota11', 'cota12', 'cota13', 'cota14', 'cota15', 'cota16', 'cota17', 'cota18',
                'cota19', 'cota20', 'cota21', 'cota22', 'cota23', 'cota24', 'cota25', 'cota26', 'cota27',
                'cota28', 'cota29', 'cota30', 'cota31', 'cota_maxima', 'cota_minima', 'cota_media',
                'cota01_status', 'cota02_status', 'cota03_status', 'cota04_status', 'cota05_status', 'cota06_status',
                'cota07_status', 'cota08_status', 'cota09_status', 'cota10_status', 'cota11_status', 'cota12_status',
                'cota13_status', 'cota14_status', 'cota15_status', 'cota16_status', 'cota17_status', 'cota18_status',
                'cota19_status', 'cota20_status', 'cota21_status', 'cota22_status', 'cota23_status', 'cota24_status',
                'cota25_status', 'cota26_status', 'cota27_status', 'cota28_status', 'cota29_status', 'cota30_status',
                'cota31_status', 'cota_maxima_status', 'cota_minima_status', 'cota_media_status'
            ]
            
            df_selecionado.columns = novos_nomes
            
            # CORREÇÃO MELHORADA: Transformar formato de data com tratamento de erros
            print(f"    🗓️ Convertendo datas...")
            try:
                # Opção 1: Converter para formato YYYY-MM (mais comum para dados mensais)
                df_selecionado['data'] = pd.to_datetime(df_selecionado['data'], format='%d/%m/%Y').dt.strftime('%Y-%m')
                print(f"    ✅ Datas convertidas para formato YYYY-MM")
            except Exception as e:
                print(f"    ⚠️ Erro na conversão de data com formato específico: {e}")
                # Fallback: tentar formato automático
                try:
                    df_selecionado['data'] = pd.to_datetime(df_selecionado['data']).dt.strftime('%Y-%m')
                    print(f"    ✅ Datas convertidas usando detecção automática")
                except Exception as e2:
                    print(f"    ❌ Erro crítico na conversão de data: {e2}")
                    total_arquivos_com_erro += 1
                    continue
            
            # Verificar se há valores inválidos na coluna data após conversão
            valores_invalidos = df_selecionado['data'].isnull().sum()
            if valores_invalidos > 0:
                print(f"    ⚠️ {valores_invalidos} registros com data inválida serão removidos")
                df_selecionado = df_selecionado.dropna(subset=['data'])
            
            # Verificar se ainda há dados após limpeza
            if df_selecionado.empty:
                print(f"    ❌ Nenhum registro válido após limpeza de datas")
                total_arquivos_com_erro += 1
                continue
            
            # CORREÇÃO MELHORADA: Formatar coluna hora com tratamento de erros
            print(f"    🕐 Formatando horas...")
            def formatar_hora(x):
                try:
                    if pd.isna(x) or x == '' or str(x).strip() == '':
                        return 'MEDIA'
                    
                    # Converter para string e limpar
                    hora_str = str(x).strip()
                    
                    # Se já está no formato HH:MM, manter
                    if ':' in hora_str:
                        return hora_str
                    
                    # Se é um número, adicionar :00
                    try:
                        hora_int = int(float(hora_str))
                        return f"{hora_int:02d}:00"
                    except (ValueError, TypeError):
                        return 'MEDIA'
                        
                except Exception:
                    return 'MEDIA'
            
            df_selecionado['hora'] = df_selecionado['hora'].apply(formatar_hora)
            print(f"    ✅ Horas formatadas")
            
            # Verificar amostra dos dados processados
            print(f"    📊 Amostra processada:")
            print(f"       Estação: {df_selecionado['codigo_estacao'].iloc[0] if not df_selecionado.empty else 'N/A'}")
            print(f"       Data: {df_selecionado['data'].iloc[0] if not df_selecionado.empty else 'N/A'}")
            print(f"       Hora: {df_selecionado['hora'].iloc[0] if not df_selecionado.empty else 'N/A'}")
            
            # Adicionar ao DataFrame final
            df_final = pd.concat([df_final, df_selecionado], ignore_index=True)
            registros_adicionados = len(df_selecionado)
            total_registros_processados += registros_adicionados
            total_arquivos_processados += 1
            print(f"    ✅ {registros_adicionados} registros adicionados (Total: {total_registros_processados})")
                
        except Exception as e:
            print(f"    ❌ Erro ao processar {arquivo}: {str(e)}")
            total_arquivos_com_erro += 1
            continue
    
    # Callback para processamento final
    if callback_progresso:
        callback_progresso("Extração", 85, 100, tipo="porcentagem")
    
    # Relatório final do processamento
    print(f"\n📊 RELATÓRIO DE CONSOLIDAÇÃO:")
    print(f"   📁 Total de arquivos encontrados: {len(arquivos_csv)}")
    print(f"   ✅ Arquivos processados com sucesso: {total_arquivos_processados}")
    print(f"   ❌ Arquivos com erro: {total_arquivos_com_erro}")
    print(f"   📋 Total de registros consolidados: {total_registros_processados}")
    
    if not df_final.empty:
        # Verificar duplicatas antes de salvar
        print(f"\n🔍 Verificando duplicatas...")
        tamanho_antes = len(df_final)
        
        # Identificar duplicatas com base nas colunas chave
        colunas_chave = ['codigo_estacao', 'data', 'hora']
        duplicatas = df_final.duplicated(subset=colunas_chave, keep='first')
        num_duplicatas = duplicatas.sum()
        
        if num_duplicatas > 0:
            print(f"   ⚠️ {num_duplicatas} duplicatas encontradas - removendo...")
            df_final = df_final[~duplicatas]
            print(f"   ✅ Duplicatas removidas. Registros finais: {len(df_final)}")
        else:
            print(f"   ✅ Nenhuma duplicata encontrada")
        
        # Callback para verificação de duplicatas
        if callback_progresso:
            callback_progresso("Extração", 90, 100, tipo="porcentagem")
        
        # Verificar estatísticas dos dados
        print(f"\n📈 ESTATÍSTICAS DOS DADOS:")
        print(f"   🏢 Estações únicas: {df_final['codigo_estacao'].nunique()}")
        print(f"   📅 Período de dados: {df_final['data'].min()} até {df_final['data'].max()}")
        print(f"   🕐 Tipos de hora únicos: {sorted(df_final['hora'].unique())}")
        
        # Callback antes de salvar
        if callback_progresso:
            callback_progresso("Extração", 95, 100, tipo="porcentagem")
        
        # Salvar o DataFrame final
        try:
            df_final.to_csv(caminho_arquivo_saida, index=False, encoding='utf-8')
            print(f"\n✅ Arquivo consolidado criado com sucesso!")
            print(f"📁 Local: {nome_arquivo_saida}")
            print(f"📊 Total de registros: {len(df_final):,}")
            print(f"💾 Tamanho do arquivo: {os.path.getsize(caminho_arquivo_saida):,} bytes")
            
            return caminho_arquivo_saida
            
        except Exception as e:
            print(f"\n❌ Erro ao salvar arquivo consolidado: {e}")
            return None
    else:
        print(f"\n❌ Nenhum dado foi consolidado!")
        print(f"💡 Verifique se os arquivos CSV possuem o formato esperado")
        return None

def processar_estacoes_completo(pasta_base=None, callback_progresso=None):
    """
    Executa o processo completo: extração dos ZIPs e consolidação dos CSVs.
    VERSÃO MELHORADA com callback de progresso.
    
    Args:
        pasta_base (str, optional): Pasta base. Se None, usa a pasta padrão do usuário
        callback_progresso (callable, optional): Função para callback de progresso
    
    Returns:
        str: Caminho do arquivo consolidado final
    """
    if pasta_base is None:
        usuario = getpass.getuser()
        pasta_base = f"C:\\Users\\{usuario}\\Downloads\\Estações_Hidroweb"
    
        # Garantir que pasta Scripts/dados existe
        pasta_scripts_dados = Path(pasta_base) / "Scripts" / "dados"
        pasta_scripts_dados.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Iniciando processamento completo em: {pasta_base}")
    
    # Callback inicial
    if callback_progresso:
        callback_progresso("Extração", 0, 100, tipo="porcentagem")
    
    # Verificar se a pasta existe
    if not os.path.exists(pasta_base):
        print(f"❌ Pasta não encontrada: {pasta_base}")
        print(f"💡 Verifique se o caminho está correto e se há arquivos ZIP na pasta")
        return None
    
    # Verificar se há arquivos ZIP na pasta
    arquivos_zip = [f for f in os.listdir(pasta_base) if f.endswith('.zip')]
    if not arquivos_zip:
        print(f"❌ Nenhum arquivo ZIP encontrado em: {pasta_base}")
        print(f"💡 Certifique-se de que os downloads foram concluídos")
        return None
    
    print(f"📦 {len(arquivos_zip)} arquivos ZIP encontrados")
    
    # Callback para arquivos encontrados
    if callback_progresso:
        callback_progresso("Extração", 5, 100, tipo="porcentagem")
    
    # Etapa 1: Extrair arquivos de cotas dos ZIPs (5% a 35% do progresso)
    print("\n" + "="*60)
    print("📦 ETAPA 1: Extraindo arquivos *_Cotas.csv dos ZIPs...")
    print("="*60)
    
    arquivos_extraidos = extrair_arquivos_cotas(pasta_base, callback_progresso=callback_progresso)
    
    if not arquivos_extraidos:
        print("❌ Nenhum arquivo de cotas foi extraído!")
        print("💡 Verifique se os arquivos ZIP contêm dados de cotas (*_Cotas.csv)")
        return None
    
    # Etapa 2: Consolidar arquivos CSV (35% a 95% do progresso)
    print("\n" + "="*60)
    print("🔄 ETAPA 2: Consolidando arquivos CSV...")
    print("="*60)
    
    arquivo_final = consolidar_arquivos_cotas(pasta_base, callback_progresso=callback_progresso)
    
    if arquivo_final:
        # Progresso final
        if callback_progresso:
            callback_progresso("Extração", 100, 100, tipo="porcentagem")
        
        print(f"\n" + "="*60)
        print(f"🎉 PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
        print("="*60)
        print(f"📁 Arquivo final: {os.path.basename(arquivo_final)}")
        print(f"📂 Localização: {arquivo_final}")
        
        # Mostrar estatísticas finais do arquivo
        try:
            tamanho_mb = os.path.getsize(arquivo_final) / 1024 / 1024
            print(f"💾 Tamanho: {tamanho_mb:.2f} MB")
            
            # Contar linhas no arquivo (aproximado)
            with open(arquivo_final, 'r', encoding='utf-8') as f:
                num_linhas = sum(1 for _ in f) - 1  # -1 para excluir cabeçalho
            print(f"📊 Registros: {num_linhas:,}")
            
        except Exception as e:
            print(f"⚠️ Erro ao obter estatísticas do arquivo: {e}")
        
        print(f"\n💡 O arquivo está pronto para inserção no banco de dados!")
        
    else:
        print(f"\n" + "="*60)
        print(f"❌ FALHA NO PROCESSAMENTO!")
        print("="*60)
        print(f"💡 Verifique os logs acima para identificar problemas:")
        print(f"   • Arquivos CSV podem estar corrompidos")
        print(f"   • Formato dos dados pode estar incorreto")
        print(f"   • Problemas de encoding nos arquivos")
    
    return arquivo_final

def limpar_arquivos_temporarios(pasta_base):
    """
    Remove os arquivos ZIP e CSV individuais após a consolidação.
    VERSÃO MELHORADA para limpeza completa e organizada.
    
    Args:
        pasta_base (str): Pasta contendo os arquivos temporários
    """
    print(f"\n🧹 Limpando arquivos temporários em: {pasta_base}")
    
    if not os.path.exists(pasta_base):
        print(f"⚠️ Pasta não encontrada: {pasta_base}")
        return
    
    arquivos_zip_removidos = 0
    arquivos_csv_removidos = 0
    arquivos_com_erro = 0
    
    try:
        # 1. Remover arquivos CSV temporários individuais
        arquivos_csv_temporarios = [f for f in os.listdir(pasta_base) if f.endswith('_Cotas.csv')]
        
        print(f"🔍 {len(arquivos_csv_temporarios)} arquivos CSV temporários encontrados")
        
        for arquivo in arquivos_csv_temporarios:
            try:
                caminho_arquivo = os.path.join(pasta_base, arquivo)
                os.remove(caminho_arquivo)
                arquivos_csv_removidos += 1
                print(f"  🗑️ CSV removido: {arquivo}")
            except Exception as e:
                arquivos_com_erro += 1
                print(f"  ⚠️ Erro ao remover CSV {arquivo}: {e}")
        
        # 2. Remover arquivos ZIP das estações consultadas
        arquivos_zip = [f for f in os.listdir(pasta_base) if f.endswith('.zip') and f.startswith('Estacao_')]
        
        print(f"🔍 {len(arquivos_zip)} arquivos ZIP de estações encontrados")
        
        for arquivo in arquivos_zip:
            try:
                caminho_arquivo = os.path.join(pasta_base, arquivo)
                os.remove(caminho_arquivo)
                arquivos_zip_removidos += 1
                print(f"  🗑️ ZIP removido: {arquivo}")
            except Exception as e:
                arquivos_com_erro += 1
                print(f"  ⚠️ Erro ao remover ZIP {arquivo}: {e}")
        
        # Relatório final da limpeza
        print(f"\n📊 RESUMO DA LIMPEZA:")
        print(f"   ✅ Arquivos CSV removidos: {arquivos_csv_removidos}")
        print(f"   ✅ Arquivos ZIP removidos: {arquivos_zip_removidos}")
        if arquivos_com_erro > 0:
            print(f"   ❌ Arquivos com erro: {arquivos_com_erro}")
        
        total_removidos = arquivos_csv_removidos + arquivos_zip_removidos
        if total_removidos > 0:
            print(f"✅ Limpeza concluída - {total_removidos} arquivos temporários removidos")
            print(f"💡 Pasta organizada: apenas o arquivo consolidado permanece")
        else:
            print("📋 Nenhum arquivo temporário encontrado para limpeza")
        
    except Exception as e:
        print(f"❌ Erro durante limpeza de arquivos temporários: {e}")

def verificar_integridade_arquivo_csv(caminho_arquivo):
    """
    Verifica a integridade de um arquivo CSV consolidado.
    
    Args:
        caminho_arquivo (str): Caminho para o arquivo CSV
        
    Returns:
        dict: Dicionário com resultado da verificação
    """
    resultado = {
        'valido': False,
        'erro': None,
        'estatisticas': {}
    }
    
    try:
        if not os.path.exists(caminho_arquivo):
            resultado['erro'] = f"Arquivo não encontrado: {caminho_arquivo}"
            return resultado
        
        # Verificar tamanho do arquivo
        tamanho = os.path.getsize(caminho_arquivo)
        if tamanho == 0:
            resultado['erro'] = "Arquivo está vazio"
            return resultado
        
        # Tentar ler o arquivo
        df = pd.read_csv(caminho_arquivo, encoding='utf-8')
        
        if df.empty:
            resultado['erro'] = "Arquivo CSV não contém dados"
            return resultado
        
        # Verificar colunas obrigatórias
        colunas_obrigatorias = ['codigo_estacao', 'data', 'hora']
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltantes:
            resultado['erro'] = f"Colunas obrigatórias faltantes: {colunas_faltantes}"
            return resultado
        
        # Estatísticas do arquivo
        resultado['estatisticas'] = {
            'total_registros': len(df),
            'total_colunas': len(df.columns),
            'estacoes_unicas': df['codigo_estacao'].nunique(),
            'periodo_inicio': df['data'].min(),
            'periodo_fim': df['data'].max(),
            'tamanho_bytes': tamanho,
            'tamanho_mb': round(tamanho / 1024 / 1024, 2)
        }
        
        resultado['valido'] = True
        return resultado
        
    except Exception as e:
        resultado['erro'] = f"Erro ao verificar arquivo: {str(e)}"
        return resultado

def obter_informacoes_processamento(pasta_base):
    """
    Obtém informações sobre o estado do processamento na pasta.
    
    Args:
        pasta_base (str): Pasta base para verificação
        
    Returns:
        dict: Informações sobre o processamento
    """
    info = {
        'pasta_existe': False,
        'arquivos_zip': 0,
        'arquivos_csv_temporarios': 0,
        'arquivo_consolidado': None,
        'pronto_para_processamento': False,
        'pronto_para_banco': False
    }
    
    try:
        if not os.path.exists(pasta_base):
            return info
        
        info['pasta_existe'] = True
        
        # Contar arquivos ZIP
        arquivos_zip = [f for f in os.listdir(pasta_base) if f.endswith('.zip')]
        info['arquivos_zip'] = len(arquivos_zip)
        
        # Contar arquivos CSV temporários
        arquivos_csv_temp = [f for f in os.listdir(pasta_base) if f.endswith('_Cotas.csv')]
        info['arquivos_csv_temporarios'] = len(arquivos_csv_temp)
        
        # Procurar arquivo consolidado
        pasta_path = Path(pasta_base)
        arquivos_consolidados = list(pasta_path.glob("estacao_hidroweb_novosregistros_*.csv"))
        
        if arquivos_consolidados:
            # Pegar o mais recente
            arquivo_mais_recente = max(arquivos_consolidados, key=lambda x: x.stat().st_mtime)
            info['arquivo_consolidado'] = str(arquivo_mais_recente)
            
            # Verificar se está pronto para banco
            verificacao = verificar_integridade_arquivo_csv(info['arquivo_consolidado'])
            info['pronto_para_banco'] = verificacao['valido']
        
        # Verificar se está pronto para processamento
        info['pronto_para_processamento'] = info['arquivos_zip'] > 0
        
        return info
        
    except Exception as e:
        print(f"⚠️ Erro ao obter informações: {e}")
        return info

if __name__ == "__main__":
    # Teste da funcionalidade
    print("🧪 TESTE DO MÓDULO DE EXTRAÇÃO E CONSOLIDAÇÃO")
    print("="*60)
    
    # Obter informações da pasta
    usuario = getpass.getuser()
    pasta_teste = f"C:\\Users\\{usuario}\\Downloads\\Estações_Hidroweb"

# Garantir que pasta Scripts/dados existe
    pasta_scripts_dados = Path(pasta_teste) / "Scripts" / "dados"
    pasta_scripts_dados.mkdir(parents=True, exist_ok=True)

    
    print(f"📂 Verificando pasta: {pasta_teste}")
    info = obter_informacoes_processamento(pasta_teste)
    
    print(f"\n📊 INFORMAÇÕES DA PASTA:")
    print(f"   📁 Pasta existe: {'✅' if info['pasta_existe'] else '❌'}")
    print(f"   📦 Arquivos ZIP: {info['arquivos_zip']}")
    print(f"   📄 Arquivos CSV temporários: {info['arquivos_csv_temporarios']}")
    print(f"   📋 Arquivo consolidado: {'✅' if info['arquivo_consolidado'] else '❌'}")
    print(f"   🚀 Pronto para processamento: {'✅' if info['pronto_para_processamento'] else '❌'}")
    print(f"   💾 Pronto para banco: {'✅' if info['pronto_para_banco'] else '❌'}")
    
    if info['arquivo_consolidado']:
        print(f"   📁 Arquivo: {os.path.basename(info['arquivo_consolidado'])}")
        
        # Verificar integridade
        verificacao = verificar_integridade_arquivo_csv(info['arquivo_consolidado'])
        if verificacao['valido']:
            stats = verificacao['estatisticas']
            print(f"   📊 Registros: {stats['total_registros']:,}")
            print(f"   🏢 Estações: {stats['estacoes_unicas']}")
            print(f"   📅 Período: {stats['periodo_inicio']} até {stats['periodo_fim']}")
            print(f"   💾 Tamanho: {stats['tamanho_mb']} MB")
        else:
            print(f"   ❌ Erro: {verificacao['erro']}")
    
    # Executar processamento se necessário
    if info['pronto_para_processamento'] and not info['pronto_para_banco']:
        print(f"\n🤔 Deseja executar o processamento? (y/n): ", end="")
        resposta = input().lower().strip()
        
        if resposta in ['y', 'yes', 's', 'sim']:
            # Função de callback de exemplo para teste
            def callback_teste(etapa, atual, total, tipo="porcentagem"):
                if tipo == "porcentagem":
                    print(f"[TESTE] {etapa}: {atual}%")
                else:
                    print(f"[TESTE] {etapa}: {atual}/{total}")
            
            resultado = processar_estacoes_completo(pasta_teste, callback_progresso=callback_teste)
            if resultado:
                print(f"\n🎉 Processamento concluído!")
                print(f"📁 Arquivo disponível em: {resultado}")
                
                # Demonstrar a limpeza
                print(f"\n🤔 Deseja limpar arquivos temporários? (y/n): ", end="")
                resposta_limpeza = input().lower().strip()
                
                if resposta_limpeza in ['y', 'yes', 's', 'sim']:
                    limpar_arquivos_temporarios(pasta_teste)
            else:
                print(f"\n❌ Processamento falhou!")
        else:
            print(f"\n📋 Processamento cancelado pelo usuário")
    
    elif info['pronto_para_banco']:
        print(f"\n✅ Arquivo consolidado já está disponível e pronto para inserção no banco!")
        
        # Opção para limpar arquivos temporários mesmo com arquivo já pronto
        if info['arquivos_zip'] > 0 or info['arquivos_csv_temporarios'] > 0:
            print(f"\n🤔 Há {info['arquivos_zip']} ZIPs e {info['arquivos_csv_temporarios']} CSVs temporários.")
            print(f"Deseja limpar estes arquivos temporários? (y/n): ", end="")
            resposta_limpeza = input().lower().strip()
            
            if resposta_limpeza in ['y', 'yes', 's', 'sim']:
                limpar_arquivos_temporarios(pasta_teste)
    
    elif not info['pronto_para_processamento']:
        print(f"\n💡 Para usar este módulo:")
        print(f"   1. Baixe algumas estações usando a interface principal")
        print(f"   2. Execute este script novamente")
        print(f"   3. Ou chame processar_estacoes_completo() diretamente")
    
    print(f"\n" + "="*60)