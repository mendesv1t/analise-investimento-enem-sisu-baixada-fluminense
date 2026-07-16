import polars as pl
import os
import glob
import re
import unicodedata
from collections import defaultdict

def normalize_name(s: str | None) -> str | None:
    if s is None:
        return None
    normalized = unicodedata.normalize('NFD', str(s))
    sem_acento = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return sem_acento.upper().strip()

BAIXADA_MUNICIPIOS_NORM = [
    'BELFORD ROXO', 'DUQUE DE CAXIAS', 'GUAPIMIRIM', 'ITAGUAI',
    'JAPERI', 'MAGE', 'MESQUITA', 'NILOPOLIS', 'NOVA IGUACU',
    'PARACAMBI', 'QUEIMADOS', 'SAO JOAO DE MERITI', 'SEROPEDICA'
]

NOME_CANONICO = {
    'BELFORD ROXO':      'Belford Roxo',
    'DUQUE DE CAXIAS':   'Duque de Caxias',
    'GUAPIMIRIM':        'Guapimirim',
    'ITAGUAI':           'Itaguaí',
    'JAPERI':            'Japeri',
    'MAGE':              'Magé',
    'MESQUITA':          'Mesquita',
    'NILOPOLIS':         'Nilópolis',
    'NOVA IGUACU':       'Nova Iguaçu',
    'PARACAMBI':         'Paracambi',
    'QUEIMADOS':         'Queimados',
    'SAO JOAO DE MERITI':'São João de Meriti',
    'SEROPEDICA':        'Seropédica',
}

def detect_encoding(filepath: str) -> str:
    for enc in ('utf-8-sig', 'utf-8', 'iso-8859-1'):
        try:
            with open(filepath, 'r', encoding=enc, errors='strict') as f:
                f.read(8192)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return 'iso-8859-1'

def detect_separator(filepath: str, encoding: str) -> str:
    with open(filepath, 'r', encoding=encoding, errors='replace') as f:
        first_line = f.readline()
    return '|' if '|' in first_line else ';'

raw_sisu_path = 'raw_data/dados_sisu/'
files = glob.glob(os.path.join(raw_sisu_path, '*.csv'))
files_por_ano = defaultdict(list)
for file in files:
    match = re.search(r'20\d{2}', os.path.basename(file))
    if match:
        files_por_ano[match.group()].append(file)

agregados_totais = []

for ano, arquivos in sorted(files_por_ano.items()):
    ano_num = int(ano)
    if ano_num < 2014 or ano_num > 2023:
        continue
    print(f"\nProcessando ano {ano}...")
    
    for file in arquivos:
        print(f"  Lendo {file}...")
        try:
            encoding = detect_encoding(file)
            sep = detect_separator(file, encoding)
            df = pl.read_csv(
                file,
                separator=sep,
                encoding=encoding,
                infer_schema_length=0,
                ignore_errors=True,
            )
            
            # Limpa colunas removendo aspas extras
            df = df.rename({c: c.replace('"', '').strip() for c in df.columns})
            
            # Localiza a coluna de município
            col_mun = None
            for c in df.columns:
                if c.upper().strip() in ['MUNICIPIO_CANDIDATO', 'NO_MUNICIPIO_RESIDENCIA', 'NO_MUNICIPIO_CANDIDATO']:
                    col_mun = c
                    break
            
            if not col_mun:
                print(f"  Aviso: Município não encontrado em {file}")
                continue
                
            # Filtra Baixada
            df = df.with_columns(
                pl.col(col_mun).cast(pl.Utf8).map_elements(normalize_name, return_dtype=pl.Utf8).alias('__mun_norm')
            )
            df = df.filter(pl.col('__mun_norm').is_in(BAIXADA_MUNICIPIOS_NORM))
            df = df.with_columns(
                pl.col('__mun_norm').map_elements(lambda x: NOME_CANONICO.get(x, x), return_dtype=pl.Utf8).alias('municipio')
            ).drop('__mun_norm')
            
            # Localiza aprovado
            col_aprovado = None
            for c in df.columns:
                if c.upper().strip() in ['APROVADO', 'ST_APROVADO']:
                    col_aprovado = c
                    break
                    
            if not col_aprovado:
                print(f"  Aviso: Coluna aprovado não encontrada em {file}")
                continue
                
            df = df.with_columns(
                pl.when(pl.col(col_aprovado).cast(pl.Utf8).str.to_uppercase().str.strip_chars().is_in(['S', 'SIM', 'TRUE', '1']))
                  .then(1).otherwise(0).alias('is_aprovado')
            )
            
            # Filtra apenas aprovados
            df = df.filter(pl.col('is_aprovado') == 1)
            
            # Localiza modalidade
            col_mod = None
            for c in df.columns:
                if c.upper().strip() in ['TP_MOD_CONCORRENCIA', 'TIPO_MOD_CONCORRENCIA', 'TP_MODALIDADE', 'TP_COTA']:
                    col_mod = c
                    break
                    
            if col_mod:
                df = df.with_columns(
                    pl.col(col_mod).cast(pl.Utf8).str.to_uppercase().str.strip_chars().alias('modality_code')
                )
            else:
                # Tenta fallback para descrição da modalidade
                col_mod_desc = None
                for c in df.columns:
                    if c.upper().strip() in ['DS_MOD_CONCORRENCIA', 'MOD_CONCORRENCIA', 'DS_MODALIDADE']:
                        col_mod_desc = c
                        break
                if col_mod_desc:
                    df = df.with_columns(
                        pl.when(pl.col(col_mod_desc).cast(pl.Utf8).str.to_uppercase().str.contains('LEI 12.711') | 
                                pl.col(col_mod_desc).cast(pl.Utf8).str.to_uppercase().str.contains('ESCOLA PÚBLICA') | 
                                pl.col(col_mod_desc).cast(pl.Utf8).str.to_uppercase().str.contains('ESCOLAS PÚBLICAS'))
                          .then(pl.lit('L')).otherwise(pl.lit('A')).alias('modality_code')
                    )
                else:
                    df = df.with_columns(pl.lit('A').alias('modality_code'))
            
            # Classifica em Cotas vs Ampla Concorrência
            df = df.with_columns(
                pl.when(pl.col('modality_code').str.starts_with('L'))
                  .then(pl.lit('Lei de Cotas (Escola Pública)'))
                  .otherwise(pl.lit('Ampla Concorrência / Outros'))
                  .alias('tipo_concorrencia')
            )
            
            # Agrupa
            agg = df.group_by(['municipio', 'tipo_concorrencia']).agg(
                pl.len().alias('total_aprovados')
            ).with_columns(
                pl.lit(ano_num).alias('ano')
            )
            agregados_totais.append(agg)
            
        except Exception as e:
            print(f"  Erro ao processar {file}: {e}")

if agregados_totais:
    df_consolidado = pl.concat(agregados_totais)
    df_consolidado = df_consolidado.group_by(['ano', 'municipio', 'tipo_concorrencia']).agg(
        pl.col('total_aprovados').sum()
    ).sort(['ano', 'municipio', 'tipo_concorrencia'])
    
    os.makedirs('curated/parquet/sisu/', exist_ok=True)
    df_consolidado.write_parquet('curated/parquet/sisu/dataset_sisu_cotas_ano.parquet')
    print(f"\nSucesso! Salvo curated/parquet/sisu/dataset_sisu_cotas_ano.parquet com {df_consolidado.height} linhas.")
else:
    print("\nNenhum registro processado!")
