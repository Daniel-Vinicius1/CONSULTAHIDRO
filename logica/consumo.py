# scripts/logica/consumo.py
import os
import re
import getpass
import shutil
from glob import glob
from datetime import datetime
from pathlib import Path

def criar_pasta_base(tipo_consulta="normal"):
    """
    Cria as pastas necessárias para organizar os downloads.
    
    Args:
        tipo_consulta (str): "normal" para pasta principal, "consultadas" para apenas consultas
    
    Returns:
        str: Caminho da pasta criada
    """
    usuario = getpass.getuser()
    caminho_base = Path(f"C:\\Users\\{usuario}\\Downloads\\Estações_Hidroweb")
    
    # SEMPRE criar pasta Scripts/dados
    pasta_scripts_dados = caminho_base / "Scripts" / "dados"
    pasta_scripts_dados.mkdir(parents=True, exist_ok=True)
    
    if tipo_consulta == "consultadas":
        caminho_final = caminho_base / "Consultadas"
    else:
        caminho_final = caminho_base
    
    caminho_final.mkdir(parents=True, exist_ok=True)
    return str(caminho_final)

def criar_estrutura_pastas():
    """Cria toda a estrutura de pastas necessária para o projeto"""
    estrutura = {
        "principal": criar_pasta_base("normal"),
        "consultadas": criar_pasta_base("consultadas")
    }
    
    print(f"📁 Estrutura de pastas criada:")
    print(f"   📂 Principal: {estrutura['principal']}")
    print(f"   📂 Consultadas: {estrutura['consultadas']}")
    
    return estrutura

def verificar_arquivo_existe(base_destino, codigo_estacao):
    """Verifica se arquivo da estação já existe na pasta especificada"""
    if base_destino is None:
        base_destino = criar_pasta_base()
    
    base_path = Path(base_destino)
    padrao = f'Estacao_{codigo_estacao}_CSV_*.zip'
    
    arquivos = list(base_path.glob(padrao))
    return len(arquivos) > 0

def verificar_arquivo_mais_recente(base_destino, codigo_estacao):
    """
    Retorna informações do arquivo mais recente da estação.
    Retorna dict com 'existe', 'arquivo', 'data', 'tamanho' ou None se não existir.
    """
    if base_destino is None:
        base_destino = criar_pasta_base()
    
    base_path = Path(base_destino)
    padrao = f'Estacao_{codigo_estacao}_CSV_*.zip'
    
    arquivos = list(base_path.glob(padrao))
    
    if not arquivos:
        return None
    
    arquivo_mais_recente = None
    data_mais_recente = None
    
    for arquivo_path in arquivos:
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
    
    if arquivo_mais_recente:
        return {
            'existe': True,
            'arquivo': str(arquivo_mais_recente),
            'nome': arquivo_mais_recente.name,
            'data': data_mais_recente,
            'tamanho': arquivo_mais_recente.stat().st_size
        }
    
    return None

def listar_estacoes_baixadas(base_destino=None):
    """Lista todas as estações baixadas com suas informações"""
    if base_destino is None:
        base_destino = criar_pasta_base()
    
    base_path = Path(base_destino)
    padrao = 'Estacao_*_CSV_*.zip'
    
    estacoes = []
    
    for arquivo_path in base_path.glob(padrao):
        nome = arquivo_path.name
        match = re.search(r'Estacao_(\d+)_CSV_(\d{4}-\d{2}-\d{2})T', nome)
        if match:
            codigo = match.group(1)
            data = match.group(2)
            tamanho = arquivo_path.stat().st_size
            estacoes.append({
                'codigo': codigo,
                'data': data,
                'tamanho': tamanho,
                'arquivo': nome
            })
    
    return sorted(estacoes, key=lambda x: x['codigo'])

def limpar_downloads_temporarios():
    """Remove arquivos temporários da pasta Downloads"""
    usuario = getpass.getuser()
    pasta_downloads = Path(f"C:\\Users\\{usuario}\\Downloads")
    padrao = 'Estacao_*_CSV_*.zip'
    
    removidos = 0
    
    for arquivo_path in pasta_downloads.glob(padrao):
        try:
            arquivo_path.unlink()
            removidos += 1
        except:
            continue
    
    return removidos

def verificar_duplicatas_e_organizar(pasta_destino=None):
    """Verifica e remove duplicatas, mantendo o arquivo mais recente"""
    if pasta_destino is None:
        pasta_destino = criar_pasta_base()
    
    print(f"🔍 Verificando duplicatas em: {pasta_destino}")
    
    base_path = Path(pasta_destino)
    padrao = 'Estacao_*_CSV_*.zip'
    estacoes_por_codigo = {}
    
    for arquivo_path in base_path.glob(padrao):
        nome = arquivo_path.name
        match = re.search(r'Estacao_(\d+)_CSV_(\d{4}-\d{2}-\d{2})T', nome)
        if match:
            codigo = match.group(1)
            data = match.group(2)
            try:
                data_dt = datetime.strptime(data, "%Y-%m-%d")
            except ValueError:
                continue
            
            if codigo not in estacoes_por_codigo:
                estacoes_por_codigo[codigo] = []
            
            estacoes_por_codigo[codigo].append({
                'arquivo': str(arquivo_path),
                'nome': nome,
                'data': data_dt,
                'tamanho': arquivo_path.stat().st_size
            })
    
    removidos = 0
    mantidos = 0
    
    for codigo, arquivos in estacoes_por_codigo.items():
        if len(arquivos) > 1:
            print(f"  📋 Estação {codigo}: {len(arquivos)} arquivos encontrados")
            
            # Ordena por data (mais recente primeiro) e depois por tamanho (maior primeiro)
            arquivos.sort(key=lambda x: (x['data'], x['tamanho']), reverse=True)
            
            arquivo_mais_recente = arquivos[0]
            print(f"    ✅ Mantendo: {arquivo_mais_recente['nome']} ({arquivo_mais_recente['tamanho']} bytes)")
            mantidos += 1
            
            for arquivo_antigo in arquivos[1:]:
                try:
                    Path(arquivo_antigo['arquivo']).unlink()
                    print(f"    🗑️  Removido: {arquivo_antigo['nome']} ({arquivo_antigo['tamanho']} bytes)")
                    removidos += 1
                except Exception as e:
                    print(f"    ❌ Erro ao remover {arquivo_antigo['nome']}: {e}")
        else:
            mantidos += 1
    
    print(f"📊 Organização concluída:")
    print(f"   ✅ Arquivos mantidos: {mantidos}")
    print(f"   🗑️  Duplicatas removidas: {removidos}")
    
    return mantidos, removidos

def verificar_integridade_arquivo(caminho_arquivo):
    """Verifica se o arquivo ZIP está íntegro"""
    try:
        arquivo_path = Path(caminho_arquivo)
        if not arquivo_path.exists():
            return False
        
        if arquivo_path.stat().st_size == 0:
            return False
        
        with open(arquivo_path, 'rb') as f:
            header = f.read(2)
            return header == b'PK'
            
    except:
        return False

def obter_estatisticas_pasta(pasta_destino=None, incluir_consultadas=False):
    """Obtém estatísticas detalhadas das pastas"""
    if pasta_destino is None:
        pasta_destino = criar_pasta_base()
    
    estatisticas = {}
    
    # Estatísticas da pasta principal
    stats_principal = calcular_estatisticas(pasta_destino)
    estatisticas['principal'] = stats_principal
    
    # Estatísticas da pasta consultadas (se solicitado)
    if incluir_consultadas:
        pasta_consultadas = criar_pasta_base("consultadas")
        stats_consultadas = calcular_estatisticas(pasta_consultadas)
        estatisticas['consultadas'] = stats_consultadas
    
    return estatisticas

def calcular_estatisticas(pasta_path):
    """Calcula estatísticas para uma pasta específica"""
    base_path = Path(pasta_path)
    
    if not base_path.exists():
        return {
            'total_arquivos': 0,
            'tamanho_total': 0,
            'estacoes_unicas': 0,
            'tamanho_mb': 0
        }
    
    padrao = 'Estacao_*_CSV_*.zip'
    arquivos = list(base_path.glob(padrao))
    
    tamanho_total = sum(arquivo.stat().st_size for arquivo in arquivos)
    
    codigos_unicos = set()
    for arquivo in arquivos:
        match = re.search(r'Estacao_(\d+)_CSV_', arquivo.name)
        if match:
            codigos_unicos.add(match.group(1))
    
    return {
        'total_arquivos': len(arquivos),
        'tamanho_total': tamanho_total,
        'estacoes_unicas': len(codigos_unicos),
        'tamanho_mb': round(tamanho_total / (1024 * 1024), 2)
    }

def comparar_tamanhos_estacao(pasta_destino, codigo_estacao, novo_tamanho):
    """
    Compara o tamanho de um novo arquivo com o arquivo existente mais recente.
    Retorna True se deve fazer download (tamanhos diferentes ou não existe),
    False se não deve fazer download (mesmo tamanho).
    """
    info_arquivo = verificar_arquivo_mais_recente(pasta_destino, codigo_estacao)
    
    if not info_arquivo:
        return True  # Não existe arquivo, deve fazer download
    
    if info_arquivo['tamanho'] != novo_tamanho:
        print(f"    📊 Tamanhos diferentes - Existente: {info_arquivo['tamanho']} bytes, Novo: {novo_tamanho} bytes")
        return True  # Tamanhos diferentes, deve fazer download
    else:
        print(f"    ⚖️ Mesmo tamanho ({info_arquivo['tamanho']} bytes) - Mantendo arquivo existente")
        return False  # Mesmo tamanho, não precisa fazer download

def mover_arquivos_entre_pastas(origem="consultadas", destino="principal"):
    """
    Move arquivos entre as pastas organizadas.
    
    Args:
        origem (str): "consultadas" ou "principal"
        destino (str): "consultadas" ou "principal"
    """
    pasta_origem = criar_pasta_base(origem)
    pasta_destino = criar_pasta_base(destino)
    
    print(f"📦 Movendo arquivos de {origem} para {destino}...")
    
    origem_path = Path(pasta_origem)
    destino_path = Path(pasta_destino)
    
    padrao = 'Estacao_*_CSV_*.zip'
    arquivos = list(origem_path.glob(padrao))
    
    movidos = 0
    for arquivo in arquivos:
        try:
            arquivo_destino = destino_path / arquivo.name
            shutil.move(str(arquivo), str(arquivo_destino))
            print(f"  ✅ Movido: {arquivo.name}")
            movidos += 1
        except Exception as e:
            print(f"  ❌ Erro ao mover {arquivo.name}: {e}")
    
    print(f"📊 {movidos} arquivos movidos com sucesso")
    return movidos

def limpar_pasta_especifica(tipo_pasta="consultadas"):
    """Limpa uma pasta específica"""
    pasta_path = criar_pasta_base(tipo_pasta)
    
    print(f"🧹 Limpando pasta {tipo_pasta}: {pasta_path}")
    
    base_path = Path(pasta_path)
    padrao = 'Estacao_*_CSV_*.zip'
    arquivos = list(base_path.glob(padrao))
    
    removidos = 0
    for arquivo in arquivos:
        try:
            arquivo.unlink()
            removidos += 1
        except Exception as e:
            print(f"❌ Erro ao remover {arquivo.name}: {e}")
    
    print(f"✅ {removidos} arquivos removidos da pasta {tipo_pasta}")
    return removidos