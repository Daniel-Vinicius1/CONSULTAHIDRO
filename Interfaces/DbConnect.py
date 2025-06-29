# scripts/Interfaces/DbConnect.py
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple, Any
import sys
from pathlib import Path
import getpass
import os

# Configurar pasta dados e logging
usuario = getpass.getuser()
pasta_dados = Path(f"C:\\Users\\{usuario}\\Downloads\\Estações_Hidroweb\\Scripts\\dados")
pasta_dados.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(pasta_dados / 'db_operations.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Classe para gerenciar conexões com PostgreSQL"""
    
    def __init__(self, host: str, port: str, database: str, user: str, password: str):
        """
        Inicializa a conexão com o banco de dados.
        
        Args:
            host: Servidor do banco
            port: Porta de conexão
            database: Nome do banco de dados
            user: Usuário
            password: Senha
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
        
    def conectar(self) -> bool:
        """
        Estabelece conexão com o banco de dados.
        
        Returns:
            bool: True se conectou com sucesso, False caso contrário
        """
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logger.info(f"SUCESSO - Conectado ao banco: {self.host}:{self.port}/{self.database}")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"ERRO - Falha ao conectar ao banco: {e}")
            return False
    
    def desconectar(self):
        """Fecha a conexão com o banco de dados"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("INFO - Conexao com banco encerrada")
        except Exception as e:
            logger.error(f"ERRO - Falha ao desconectar: {e}")
    
    def testar_conexao(self) -> bool:
        """
        Testa a conexão com o banco de dados.
        
        Returns:
            bool: True se a conexão está funcionando
        """
        try:
            if not self.connection:
                return False
                
            self.cursor.execute("SELECT 1")
            result = self.cursor.fetchone()
            return result is not None
            
        except Exception as e:
            logger.error(f"ERRO - Teste de conexao falhou: {e}")
            return False
    
    def executar_query(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """
        Executa uma query SELECT e retorna os resultados.
        
        Args:
            query: Query SQL
            params: Parâmetros da query
            
        Returns:
            Lista de dicionários com os resultados ou None em caso de erro
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"ERRO - Falha ao executar query: {e}")
            return None
    
    def executar_comando(self, comando: str, params: tuple = None) -> bool:
        """
        Executa um comando SQL (INSERT, UPDATE, DELETE).
        
        Args:
            comando: Comando SQL
            params: Parâmetros do comando
            
        Returns:
            bool: True se executado com sucesso
        """
        try:
            self.cursor.execute(comando, params)
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"ERRO - Falha ao executar comando: {e}")
            self.connection.rollback()
            return False
    
    def executar_lote(self, comando: str, dados: List[tuple]) -> bool:
        """
        Executa comandos em lote para melhor performance.
        
        Args:
            comando: Comando SQL
            dados: Lista de tuplas com os dados
            
        Returns:
            bool: True se executado com sucesso
        """
        try:
            self.cursor.executemany(comando, dados)
            self.connection.commit()
            logger.info(f"SUCESSO - Lote executado: {len(dados)} registros processados")
            return True
        except Exception as e:
            logger.error(f"ERRO - Falha no lote: {e}")
            logger.error(f"DETALHES: {str(e)}")
            self.connection.rollback()
            return False

    def executar_lote_otimizado(self, comando: str, dados: List[tuple], batch_size: int = 1000) -> bool:
        """
        Executa inserção em lotes otimizada com melhor controle de timeout.
        
        Args:
            comando: Comando SQL
            dados: Lista de tuplas com os dados  
            batch_size: Tamanho do lote
            
        Returns:
            bool: True se executado com sucesso
        """
        try:
            total_registros = len(dados)
            registros_processados = 0
            
            logger.info(f"INFO - Iniciando insercao em lotes otimizada")
            logger.info(f"INFO - Total de registros para processar: {total_registros}")
            logger.info(f"INFO - Tamanho do lote: {batch_size}")
            
            # Processar em lotes
            for i in range(0, total_registros, batch_size):
                batch = dados[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_registros + batch_size - 1) // batch_size
                
                logger.info(f"INFO - Processando lote {batch_num}/{total_batches} ({len(batch)} registros)")
                
                try:
                    # Configurar timeout generoso
                    self.cursor.execute("SET statement_timeout = '600s'")  # 10 minutos
                    
                    # Executar lote
                    start_time = datetime.now()
                    self.cursor.executemany(comando, batch)
                    self.connection.commit()
                    end_time = datetime.now()
                    
                    # Calcular tempo
                    tempo_lote = (end_time - start_time).total_seconds()
                    
                    registros_processados += len(batch)
                    porcentagem = (registros_processados / total_registros) * 100
                    
                    logger.info(f"SUCESSO - Lote {batch_num} concluido em {tempo_lote:.1f}s ({porcentagem:.1f}% total)")
                    
                except Exception as e:
                    logger.error(f"ERRO - Falha no lote {batch_num}: {e}")
                    
                    # Se for timeout, tentar com lote menor
                    if "timeout" in str(e).lower() and batch_size > 500:
                        logger.info(f"INFO - Timeout detectado, reduzindo tamanho do lote")
                        novo_batch_size = max(500, batch_size // 2)
                        return self.executar_lote_otimizado(comando, dados[i:], novo_batch_size)
                    else:
                        self.connection.rollback()
                        return False
            
            logger.info(f"SUCESSO - Insercao em lotes concluida! Total processado: {registros_processados}")
            return True
            
        except Exception as e:
            logger.error(f"ERRO - Falha na insercao em lotes: {e}")
            self.connection.rollback()
            return False

    def verificar_locks_ativos(self) -> List[Dict]:
        """
        Verifica locks ativos na tabela que podem estar causando timeout.
        
        Returns:
            Lista de locks ativos
        """
        try:
            query = """
            SELECT 
                l.locktype,
                l.database,
                l.relation::regclass as table_name,
                l.mode,
                l.granted,
                a.state,
                a.query_start,
                a.state_change,
                LEFT(a.query, 100) as query_preview
            FROM pg_locks l
            LEFT JOIN pg_stat_activity a ON l.pid = a.pid
            WHERE l.relation IS NOT NULL
            AND l.relation::regclass::text LIKE '%ana_%'
            ORDER BY l.granted, a.query_start;
            """
            
            resultado = self.executar_query(query)
            if resultado:
                logger.info(f"INFO - {len(resultado)} locks encontrados em tabelas ana_*")
                for lock in resultado:
                    logger.info(f"  Tabela: {lock.get('table_name')}, Modo: {lock.get('mode')}, Concedido: {lock.get('granted')}")
            
            return resultado or []
            
        except Exception as e:
            logger.error(f"ERRO - Falha ao verificar locks: {e}")
            return []

class HidrowebDatabase:
    """Classe específica para operações com dados do Hidroweb"""
    
    def __init__(self, db_connection: DatabaseConnection, nome_tabela: str = None):
        """
        Inicializa com uma conexão de banco e nome da tabela.
        
        Args:
            db_connection: Instância de DatabaseConnection
            nome_tabela: Nome específico da tabela. Se None, detecta automaticamente
        """
        self.db = db_connection
        
        if nome_tabela:
            # Usar tabela especificada pelo usuário
            if self.verificar_tabela_existe(nome_tabela):
                self.nome_tabela = nome_tabela
                logger.info(f"SUCESSO - Usando tabela especificada: {self.nome_tabela}")
            else:
                raise Exception(f"ERRO - Tabela '{nome_tabela}' nao encontrada no banco!")
        else:
            # Detectar automaticamente
            self.nome_tabela = self.detectar_tabela_cotas()
            if not self.nome_tabela:
                raise Exception("ERRO - Nenhuma tabela de cotas encontrada!")
            logger.info(f"SUCESSO - Tabela detectada automaticamente: {self.nome_tabela}")
    
    def detectar_tabela_cotas(self) -> Optional[str]:
        """
        Detecta automaticamente qual tabela de cotas usar.
        
        Returns:
            str: Nome da tabela encontrada ou None
        """
        # Possíveis nomes de tabela (ordem de prioridade)
        possiveis_tabelas = [
            "origem.ana_cotas_diaria_testing",  # Tabela de teste local
            "ana.ana_cota_diaria",              # Produção
            "public.ana_cot_diaria_daniel_teste_copycomplete",  # Teste do trabalho
            "public.ana_cotas_diaria_inserir",  # Teste vazia do trabalho
            "origem.ana_cota_dia",              # Teste alternativo
            "public.ana_cota_dia",              # Alternativa
            "ana_cota_diaria",                  # Sem schema
            "ana_cota_dia"                      # Sem schema
        ]
        
        for tabela in possiveis_tabelas:
            if self.verificar_tabela_existe(tabela):
                return tabela
        
        return None
    
    def verificar_tabela_existe(self, nome_tabela: str) -> bool:
        """
        Verifica se uma tabela existe no banco.
        
        Args:
            nome_tabela: Nome da tabela (pode incluir schema)
            
        Returns:
            bool: True se a tabela existe
        """
        try:
            # Separar schema e tabela se necessário
            if '.' in nome_tabela:
                schema, tabela = nome_tabela.split('.', 1)
                query = """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
                """
                params = (schema, tabela)
            else:
                query = """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = %s
                """
                params = (nome_tabela,)
            
            resultado = self.db.executar_query(query, params)
            if resultado and resultado[0]['count'] > 0:
                logger.info(f"SUCESSO - Tabela encontrada: {nome_tabela}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"ERRO - Falha ao verificar tabela {nome_tabela}: {e}")
            return False
    
    def buscar_arquivo_consolidado(self, pasta_base: str = None) -> Optional[str]:
        """
        Busca automaticamente o arquivo consolidado mais recente.
        
        Args:
            pasta_base: Pasta onde procurar. Se None, usa pasta padrão
            
        Returns:
            str: Caminho do arquivo encontrado ou None
        """
        if pasta_base is None:
            usuario = getpass.getuser()
            pasta_base = f"C:\\Users\\{usuario}\\Downloads\\Estações_Hidroweb"
            
            # Garantir que pasta Scripts/dados existe
            pasta_scripts_dados = Path(pasta_base) / "Scripts" / "dados"
            pasta_scripts_dados.mkdir(parents=True, exist_ok=True)

        pasta_path = Path(pasta_base)
        if not pasta_path.exists():
            logger.error(f"ERRO - Pasta nao encontrada: {pasta_base}")
            return None
        
        # Procurar arquivos que seguem o padrão
        padrao = "estacao_hidroweb_novosregistros_*.csv"
        arquivos_encontrados = list(pasta_path.glob(padrao))
        
        if not arquivos_encontrados:
            logger.error(f"ERRO - Nenhum arquivo com padrao '{padrao}' encontrado")
            return None
        
        # Pegar o arquivo mais recente
        arquivo_mais_recente = max(arquivos_encontrados, key=lambda x: x.stat().st_mtime)
        logger.info(f"SUCESSO - Arquivo encontrado: {arquivo_mais_recente.name}")
        
        return str(arquivo_mais_recente)

    def verificar_duplicatas_antes_insercao(self, dados: List[tuple]) -> Dict[str, int]:
        """
        Verifica quantos registros já existem na tabela antes da inserção.
        Útil para estimar quantos serão realmente inseridos.
        
        Args:
            dados: Lista de tuplas com os dados a serem inseridos
            
        Returns:
            Dict com estatísticas das duplicatas
        """
        try:
            if not dados:
                return {"total_verificados": 0, "ja_existem": 0, "serao_inseridos": 0}
            
            logger.info("INFO - Verificando duplicatas antes da insercao...")
            
            # Criar consulta para verificar existência
            # Usar apenas as colunas da chave primária
            chaves_primarias = []
            for linha in dados[:100]:  # Verificar apenas as primeiras 100 para amostragem
                chave = (linha[0], linha[1], linha[2], linha[3], linha[4])  # codigo_estacao, data, hora, tipo_medicao_cota, nivel_consistencia
                chaves_primarias.append(chave)
            
            # Consulta para verificar quantos já existem
            sql_verificacao = f"""
            SELECT COUNT(*) as existentes
            FROM {self.nome_tabela}
            WHERE (codigo_estacao, data, hora, tipo_medicao_cota, nivel_consistencia) IN %s
            """
            
            resultado = self.db.executar_query(sql_verificacao, (tuple(chaves_primarias),))
            
            if resultado:
                ja_existem = resultado[0]['existentes']
                total_amostra = len(chaves_primarias)
                porcentagem_duplicatas = (ja_existem / total_amostra) * 100
                
                # Estimar para o total
                total_dados = len(dados)
                estimativa_existentes = int((porcentagem_duplicatas / 100) * total_dados)
                estimativa_inseridos = total_dados - estimativa_existentes
                
                logger.info(f"INFO - Analise de duplicatas (amostra de {total_amostra} registros):")
                logger.info(f"  Ja existem: {ja_existem} ({porcentagem_duplicatas:.1f}%)")
                logger.info(f"  Estimativa para {total_dados} registros:")
                logger.info(f"    Ja existem: ~{estimativa_existentes}")
                logger.info(f"    Serao inseridos: ~{estimativa_inseridos}")
                
                return {
                    "total_verificados": total_dados,
                    "ja_existem": estimativa_existentes,
                    "serao_inseridos": estimativa_inseridos,
                    "porcentagem_duplicatas": porcentagem_duplicatas
                }
            
            return {"total_verificados": len(dados), "ja_existem": 0, "serao_inseridos": len(dados)}
            
        except Exception as e:
            logger.error(f"ERRO - Falha ao verificar duplicatas: {e}")
            return {"total_verificados": len(dados), "ja_existem": 0, "serao_inseridos": len(dados)}
    
    def inserir_dados_csv(self, caminho_csv: str = None) -> bool:
        """
        Insere dados de CSV com DO NOTHING para máxima segurança e performance.
        NÃO modifica dados existentes, apenas insere novos registros.
        """
        try:
            # Se não forneceu caminho, buscar automaticamente
            if caminho_csv is None:
                caminho_csv = self.buscar_arquivo_consolidado()
                if not caminho_csv:
                    logger.error("ERRO - Nenhum arquivo CSV encontrado")
                    return False
            
            # Verificar se arquivo existe
            if not Path(caminho_csv).exists():
                logger.error(f"ERRO - Arquivo nao encontrado: {caminho_csv}")
                return False
            
            logger.info(f"INFO - Processando arquivo: {os.path.basename(caminho_csv)}")
            logger.info(f"INFO - Caminho completo: {caminho_csv}")
            
            # Verificar tamanho do arquivo
            tamanho_arquivo = Path(caminho_csv).stat().st_size
            logger.info(f"INFO - Tamanho do arquivo: {tamanho_arquivo:,} bytes ({tamanho_arquivo/1024/1024:.2f} MB)")
            
            # Ler o CSV com tratamento de encoding
            try:
                # Tentar UTF-8 primeiro
                df = pd.read_csv(caminho_csv, encoding='utf-8')
                logger.info("SUCESSO - Arquivo lido com encoding UTF-8")
            except UnicodeDecodeError:
                try:
                    # Tentar ISO-8859-1 como fallback
                    df = pd.read_csv(caminho_csv, encoding='iso-8859-1')
                    logger.info("SUCESSO - Arquivo lido com encoding ISO-8859-1")
                except Exception as e:
                    logger.error(f"ERRO - Falha de encoding ao ler CSV: {e}")
                    return False
            
            logger.info(f"INFO - CSV carregado: {len(df)} registros encontrados")
            
            if df.empty:
                logger.warning("AVISO - Arquivo CSV esta vazio!")
                return False
            
            # Log das colunas do arquivo
            logger.info(f"INFO - Colunas no arquivo ({len(df.columns)}): {list(df.columns)}")
            
            # Verificar se as colunas necessárias existem
            colunas_obrigatorias = ['codigo_estacao', 'data', 'hora']
            colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
            
            if colunas_faltantes:
                logger.error(f"ERRO - Colunas obrigatorias faltantes: {colunas_faltantes}")
                return False
            
            # Log de amostras dos dados
            logger.info("INFO - Amostra dos dados (primeiras 3 linhas):")
            for i, row in df.head(3).iterrows():
                logger.info(f"  Linha {i+1}: Estacao={row.get('codigo_estacao')}, Data={row.get('data')}, Hora={row.get('hora')}")
            
            # DEFINIR AS 73 COLUNAS DA TABELA NA ORDEM EXATA
            colunas_tabela = [
                'codigo_estacao', 'data', 'hora', 'tipo_medicao_cota', 'nivel_consistencia',
                'cota01', 'cota02', 'cota03', 'cota04', 'cota05', 'cota06', 'cota07', 'cota08', 'cota09', 'cota10',
                'cota11', 'cota12', 'cota13', 'cota14', 'cota15', 'cota16', 'cota17', 'cota18', 'cota19', 'cota20',
                'cota21', 'cota22', 'cota23', 'cota24', 'cota25', 'cota26', 'cota27', 'cota28', 'cota29', 'cota30',
                'cota31', 'cota_maxima', 'cota_minima', 'cota_media',
                'cota01_status', 'cota02_status', 'cota03_status', 'cota04_status', 'cota05_status',
                'cota06_status', 'cota07_status', 'cota08_status', 'cota09_status', 'cota10_status',
                'cota11_status', 'cota12_status', 'cota13_status', 'cota14_status', 'cota15_status',
                'cota16_status', 'cota17_status', 'cota18_status', 'cota19_status', 'cota20_status',
                'cota21_status', 'cota22_status', 'cota23_status', 'cota24_status', 'cota25_status',
                'cota26_status', 'cota27_status', 'cota28_status', 'cota29_status', 'cota30_status',
                'cota31_status', 'cota_maxima_status', 'cota_minima_status', 'cota_media_status'
            ]
            
            logger.info(f"INFO - Tabela espera {len(colunas_tabela)} colunas, CSV tem {len(df.columns)} colunas")
            
            # Preparar dados para inserção com conversão correta de tipos
            dados_para_inserir = []
            registros_com_erro = 0
            registros_processados = 0
            
            logger.info("INFO - Iniciando processamento dos registros...")
            
            for index, row in df.iterrows():
                registros_processados += 1
                
                # Log de progresso a cada 1000 registros
                if registros_processados % 1000 == 0:
                    porcentagem = (registros_processados/len(df)*100)
                    logger.info(f"INFO - Processados: {registros_processados}/{len(df)} registros ({porcentagem:.1f}%)")
                
                try:
                    # Função melhorada para conversão segura
                    def safe_convert(value, tipo='float', nome_campo=''):
                        try:
                            if pd.isna(value) or value == '' or value is None:
                                return None
                            
                            if tipo == 'int':
                                # Converter float para int (importante para os status)
                                if isinstance(value, float):
                                    return int(value) if not pd.isna(value) else 0
                                return int(float(value))
                            elif tipo == 'str':
                                return str(value).strip()
                            else:  # float
                                return float(value)
                        except (ValueError, TypeError) as e:
                            if registros_com_erro < 5:  # Log apenas os primeiros 5 erros
                                logger.warning(f"AVISO - Erro ao converter {nome_campo}='{value}' para {tipo} na linha {index+1}: {e}")
                            return None
                    
                    # PROCESSAR TODAS AS 73 COLUNAS NA ORDEM CORRETA
                    dados_linha = []
                    
                    for coluna in colunas_tabela:
                        if coluna == 'codigo_estacao':
                            valor = safe_convert(row.get(coluna), 'int', coluna)
                        elif coluna in ['data', 'hora']:
                            valor = safe_convert(row.get(coluna), 'str', coluna)
                        elif coluna in ['tipo_medicao_cota', 'nivel_consistencia']:
                            valor = safe_convert(row.get(coluna, 1), 'int', coluna)
                            if valor is None:
                                valor = 1  # Valores padrão conforme estrutura da tabela
                        elif coluna.endswith('_status'):
                            # IMPORTANTE: Converter status de float para int
                            valor_original = row.get(coluna, 0)
                            if pd.isna(valor_original) or valor_original == '':
                                valor = 0
                            else:
                                try:
                                    valor = int(float(valor_original))  # Converter float->int
                                except (ValueError, TypeError):
                                    valor = 0
                        else:  # cotas e estatísticas (float/real)
                            valor = safe_convert(row.get(coluna), 'float', coluna)
                        
                        dados_linha.append(valor)
                    
                    # Verificar se os dados principais são válidos
                    if dados_linha[0] is None or dados_linha[1] is None:  # codigo_estacao ou data
                        if registros_com_erro < 5:
                            logger.warning(f"AVISO - Linha {index+1} ignorada: codigo_estacao={dados_linha[0]}, data={dados_linha[1]}")
                        registros_com_erro += 1
                        continue
                    
                    # Verificar se temos exatamente 73 valores
                    if len(dados_linha) != 73:
                        logger.error(f"ERRO - Linha {index+1} tem {len(dados_linha)} valores, esperado 73")
                        registros_com_erro += 1
                        continue
                    
                    # Converter para tupla e adicionar
                    dados_para_inserir.append(tuple(dados_linha))
                    
                except Exception as e:
                    registros_com_erro += 1
                    if registros_com_erro <= 5:  # Log apenas os primeiros 5 erros
                        logger.warning(f"AVISO - Erro na linha {index + 1}: {e}")
                    continue
            
            # Resumo do processamento
            logger.info(f"INFO - RESUMO DO PROCESSAMENTO:")
            logger.info(f"  Total de linhas no CSV: {len(df)}")
            logger.info(f"  Registros validos processados: {len(dados_para_inserir)}")
            logger.info(f"  Registros com erro ignorados: {registros_com_erro}")
            
            if not dados_para_inserir:
                logger.error("ERRO - Nenhum registro valido para inserir!")
                return False
            
            # NOVO: Verificar duplicatas antes da inserção
            stats_duplicatas = self.verificar_duplicatas_antes_insercao(dados_para_inserir)
            
            # NOVO: Verificar locks antes de iniciar
            logger.info("INFO - Verificando locks ativos na tabela...")
            locks_ativos = self.db.verificar_locks_ativos()
            
            if locks_ativos:
                logger.warning("AVISO - Locks ativos detectados. Isso pode causar timeout!")
                for lock in locks_ativos[:3]:  # Mostrar apenas os primeiros 3
                    logger.warning(f"  Lock: {lock.get('table_name')} - {lock.get('mode')}")
            
            # Testar conexão antes da inserção
            logger.info("INFO - Testando conexao com banco antes da insercao...")
            if not self.db.testar_conexao():
                logger.error("ERRO - Conexao com banco falhou!")
                return False
            
            logger.info("SUCESSO - Conexao com banco OK, iniciando insercao...")
            
            # Obter contagem inicial da tabela
            stats_inicial = self.obter_estatisticas_tabela()
            contagem_inicial = stats_inicial['total_registros'] if stats_inicial else 0
            
            # SQL OTIMIZADO COM DO NOTHING - Muito mais rápido e seguro!
            sql_insert = f"""
INSERT INTO {self.nome_tabela} (
    codigo_estacao, data, hora, tipo_medicao_cota, nivel_consistencia,
    cota01, cota02, cota03, cota04, cota05, cota06, cota07, cota08, cota09, cota10,
    cota11, cota12, cota13, cota14, cota15, cota16, cota17, cota18, cota19, cota20,
    cota21, cota22, cota23, cota24, cota25, cota26, cota27, cota28, cota29, cota30,
    cota31, cota_maxima, cota_minima, cota_media,
    cota01_status, cota02_status, cota03_status, cota04_status, cota05_status,
    cota06_status, cota07_status, cota08_status, cota09_status, cota10_status,
    cota11_status, cota12_status, cota13_status, cota14_status, cota15_status,
    cota16_status, cota17_status, cota18_status, cota19_status, cota20_status,
    cota21_status, cota22_status, cota23_status, cota24_status, cota25_status,
    cota26_status, cota27_status, cota28_status, cota29_status, cota30_status,
    cota31_status, cota_maxima_status, cota_minima_status, cota_media_status
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON CONFLICT (codigo_estacao, data, hora, tipo_medicao_cota, nivel_consistencia) 
DO NOTHING;
"""
            
            logger.info(f"INFO - Iniciando insercao SEGURA de {len(dados_para_inserir)} registros")
            logger.info("INFO - Usando ON CONFLICT DO NOTHING para proteger dados existentes")
            logger.info(f"INFO - Registros na tabela antes: {contagem_inicial}")
            
            # Determinar estratégia baseada no tamanho
            if len(dados_para_inserir) > 1000:
                # Para grandes volumes: usar lotes otimizados
                logger.info("INFO - Volume grande detectado, usando insercao em lotes otimizada")
                batch_size = 1000 if len(dados_para_inserir) < 5000 else 500  # Lotes menores para volumes muito grandes
                resultado = self.db.executar_lote_otimizado(sql_insert, dados_para_inserir, batch_size)
            else:
                # Para volumes pequenos: lote único
                logger.info("INFO - Volume pequeno, usando lote unico")
                resultado = self.db.executar_lote(sql_insert, dados_para_inserir)
            
            if resultado:
                # Verificar quantos registros foram realmente inseridos
                stats_final = self.obter_estatisticas_tabela()
                contagem_final = stats_final['total_registros'] if stats_final else 0
                registros_inseridos = contagem_final - contagem_inicial
                registros_ignorados = len(dados_para_inserir) - registros_inseridos
                
                logger.info(f"SUCESSO - INSERCAO SEGURA CONCLUIDA!")
                logger.info(f"  Registros processados: {len(dados_para_inserir)}")
                logger.info(f"  Registros realmente inseridos: {registros_inseridos}")
                logger.info(f"  Registros ja existentes (ignorados): {registros_ignorados}")
                logger.info(f"  Tabela: {self.nome_tabela}")
                logger.info(f"  Banco: {self.db.host}:{self.db.port}/{self.db.database}")
                logger.info(f"  Total de registros na tabela agora: {contagem_final}")
                logger.info(f"  Estrategia: DO NOTHING (nao sobrescreve dados existentes)")
                
                return True
            else:
                logger.error("ERRO - Falha na insercao segura!")
                return False
                
        except Exception as e:
            logger.error(f"ERRO - Falha na insercao segura: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def consultar_estacao(self, codigo_estacao: str, limite: int = 10) -> Optional[List[Dict]]:
        """
        Consulta dados de uma estação específica.
        
        Args:
            codigo_estacao: Código da estação
            limite: Número máximo de registros
            
        Returns:
            Lista com os dados ou None
        """
        sql = f"""
        SELECT codigo_estacao, data, hora, cota_maxima, cota_minima, cota_media
        FROM {self.nome_tabela}
        WHERE codigo_estacao = %s
        ORDER BY data DESC, hora DESC
        LIMIT %s
        """
        
        return self.db.executar_query(sql, (int(codigo_estacao), limite))
    
    def obter_estatisticas_tabela(self) -> Optional[Dict]:
        """
        Obtém estatísticas da tabela.
        
        Returns:
            Dicionário com estatísticas ou None
        """
        sql = f"""
        SELECT 
            COUNT(*) as total_registros,
            COUNT(DISTINCT codigo_estacao) as total_estacoes,
            MIN(data) as data_mais_antiga,
            MAX(data) as data_mais_recente
        FROM {self.nome_tabela}
        """
        
        resultado = self.db.executar_query(sql)
        return resultado[0] if resultado else None

def testar_conexao_completa(credenciais: Dict[str, str], nome_tabela: str = None) -> bool:
    """
    Testa conexão completa com o banco incluindo detecção de tabela.
    
    Args:
        credenciais: Dicionário com as credenciais de conexão
        nome_tabela: Nome específico da tabela (opcional)
        
    Returns:
        bool: True se todos os testes passaram
    """
    db_conn = None
    try:
        # Conectar ao banco
        db_conn = DatabaseConnection(
            host=credenciais['host'],
            port=credenciais['port'],
            database=credenciais['database'],
            user=credenciais['user'],
            password=credenciais['password']
        )
        
        if not db_conn.conectar():
            return False
        
        # Testar conexão básica
        if not db_conn.testar_conexao():
            return False
        
        # Testar detecção de tabela
        try:
            hidro_db = HidrowebDatabase(db_conn, nome_tabela)
            logger.info(f"SUCESSO - Tabela confirmada: {hidro_db.nome_tabela}")
            
            # Obter estatísticas da tabela
            stats = hidro_db.obter_estatisticas_tabela()
            if stats:
                logger.info(f"INFO - Estatisticas da tabela:")
                logger.info(f"  Total de registros: {stats['total_registros']}")
                logger.info(f"  Total de estacoes: {stats['total_estacoes']}")
                logger.info(f"  Periodo: {stats['data_mais_antiga']} ate {stats['data_mais_recente']}")
            
            return True
            
        except Exception as e:
            logger.error(f"ERRO - Falha ao verificar tabela: {e}")
            return False
        
    except Exception as e:
        logger.error(f"ERRO - Falha no teste de conexao: {e}")
        return False
    
    finally:
        if db_conn:
            db_conn.desconectar()

def processar_dados_completo(credenciais: Dict[str, str], caminho_csv: str = None, nome_tabela: str = None) -> bool:
    """
    Executa o processo completo de inserção de dados no banco.
    
    Args:
        credenciais: Credenciais do banco
        caminho_csv: Caminho do arquivo CSV (opcional - busca automaticamente se None)
        nome_tabela: Nome específico da tabela (opcional - detecta automaticamente se None)
        
    Returns:
        bool: True se processamento foi bem-sucedido
    """
    db_conn = None
    try:
        logger.info("INFO - Iniciando processamento completo de dados...")
        
        # Conectar ao banco
        db_conn = DatabaseConnection(
            host=credenciais['host'],
            port=credenciais['port'],
            database=credenciais['database'],
            user=credenciais['user'],
            password=credenciais['password']
        )
        
        if not db_conn.conectar():
            logger.error("ERRO - Falha na conexao com o banco!")
            return False
        
        # Inicializar classe Hidroweb com nome da tabela específico
        hidro_db = HidrowebDatabase(db_conn, nome_tabela)
        
        # Inserir dados do CSV
        if hidro_db.inserir_dados_csv(caminho_csv):
            logger.info("SUCESSO - Processamento concluido com sucesso!")
            
            # Mostrar estatísticas finais
            stats = hidro_db.obter_estatisticas_tabela()
            if stats:
                logger.info(f"INFO - Estatisticas finais:")
                logger.info(f"  Total de registros: {stats['total_registros']}")
                logger.info(f"  Total de estacoes: {stats['total_estacoes']}")
            
            return True
        else:
            logger.error("ERRO - Falha na insercao dos dados!")
            return False
        
    except Exception as e:
        logger.error(f"ERRO - Falha no processamento: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    finally:
        if db_conn:
            db_conn.desconectar()

if __name__ == "__main__":
    # Teste básico
    credenciais_teste = {
        'host': 'localhost',
        'port': '5432',
        'database': 'sipam_hidro',
        'user': 'postgres',
        'password': 'sua_senha'
    }
    
    print("INFO - Testando conexao e deteccao de tabela...")
    if testar_conexao_completa(credenciais_teste):
        print("SUCESSO - Teste de conexao passou!")
        
        # Teste de inserção (descomente para testar)
        # print("\nINFO - Testando insercao de dados...")
        # processar_dados_completo(credenciais_teste)
    else:
        print("ERRO - Teste de conexao falhou!")