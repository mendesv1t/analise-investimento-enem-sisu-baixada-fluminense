import polars as pl
import os
import glob
import gc
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

# Lista de Municípios da Baixada Fluminense
BAIXADA_MUNICIPIOS = [
    'BELFORD ROXO', 'DUQUE DE CAXIAS', 'GUAPIMIRIM', 'ITAGUAI', 'ITAGUAÍ', 
    'JAPERI', 'MAGE', 'MAGÉ', 'MESQUITA', 'NILOPOLIS', 'NILÓPOLIS', 
    'NOVA IGUACU', 'NOVA IGUAÇU', 'PARACAMBI', 'QUEIMADOS', 
    'SAO JOAO DE MERITI', 'SÃO JOÃO DE MERITI', 'SEROPEDICA', 'SEROPÉDICA'
]

# Dicionários Universais
DICT_RENDA = {
    'A': 'Nenhuma renda', 'B': 'Até 1 SM', 'C': 'De 1 a 1,5 SM', 'D': 'De 1,5 a 2 SM',
    'E': 'De 2 a 2,5 SM', 'F': 'De 2,5 a 3 SM', 'G': 'De 3 a 4 SM', 'H': 'De 4 a 5 SM',
    'I': 'De 5 a 6 SM', 'J': 'De 6 a 7 SM', 'K': 'De 7 a 8 SM', 'L': 'De 8 a 9 SM',
    'M': 'De 9 a 10 SM', 'N': 'De 10 a 12 SM', 'O': 'De 12 a 15 SM', 'P': 'De 15 a 20 SM',
    'Q': 'Mais de 20 SM'
}

DICT_ESCOLARIDADE = {
    'A': 'Nunca estudou', 'B': 'Fundamental Incompleto (Até 5º ano)',
    'C': 'Fundamental Incompleto (Até 9º ano)', 'D': 'Médio Incompleto',
    'E': 'Médio Completo', 'F': 'Superior Completo', 'G': 'Pós-graduação', 'H': 'Não sei'
}

DICT_RACA = {
    0: 'Não declarado', 1: 'Branca', 2: 'Preta', 3: 'Parda', 4: 'Amarela', 5: 'Indígena', 6: 'Não disp'
}

DICT_ESCOLA = {
    1: 'Não Respondeu', 2: 'Pública', 3: 'Privada', 4: 'Exterior'
}

raw_dir = 'raw_data/microdados-enem'
out_dir = 'curated/parquet/enem/microdados_por_ano'

def processar_ano(ano):
    print(f"\n[Ano {ano}] Iniciando processamento...")
    
    pattern = f"{raw_dir}/microdados_enem_{ano}/DADOS/*.csv"
    files = glob.glob(pattern)
    files = [f for f in files if 'MICRODADOS' in os.path.basename(f).upper() and 'ITENS' not in os.path.basename(f).upper()]
    
    if not files:
        pattern = f"{raw_dir}/microdados_enem_{ano}/DADOS/*.txt"
        files = glob.glob(pattern)
        files = [f for f in files if 'MICRODADOS' in os.path.basename(f).upper() and 'ITENS' not in os.path.basename(f).upper()]
    
    if not files:
        print(f"[Ano {ano}] Arquivo bruto não encontrado!")
        return None
        
    file_path = files[0]
    print(f"[Ano {ano}] Lendo {file_path}...")
    
    try:
        df_head = pl.read_csv(file_path, separator=';', n_rows=1, encoding='iso-8859-1', ignore_errors=True)
        exist_cols = df_head.columns
        
        target_cols = ['NU_ANO', 'CO_MUNICIPIO_ESC', 'NO_MUNICIPIO_ESC', 'CO_MUNICIPIO_PROVA', 'NO_MUNICIPIO_PROVA', 
                       'CO_MUNICIPIO_RESIDENCIA', 'NO_MUNICIPIO_RESIDENCIA', 'TP_DEPENDENCIA_ADM_ESC', 'TP_ESCOLA', 
                       'IN_TREINEIRO', 'TP_ST_CONCLUSAO', 'TP_PRESENCA_CN', 'TP_PRESENCA_CH', 'TP_PRESENCA_LC', 'TP_PRESENCA_MT',
                       'NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO', 'TP_COR_RACA']
        
        quest_cols = [f'Q{str(i).zfill(3)}' for i in range(1, 26)]
        target_cols.extend(quest_cols)
                       
        keep_cols = [c for c in target_cols if c in exist_cols]
        
        df_collected = pl.read_csv(file_path, separator=';', encoding='iso-8859-1', columns=keep_cols, infer_schema_length=10000, ignore_errors=True)
        df = df_collected.lazy()
    except Exception as e:
        print(f"[Ano {ano}] Erro ao ler: {e}")
        return None
        
    cols = df.columns
    
    exprs = []
    for c in ['NO_MUNICIPIO_RESIDENCIA', 'NO_MUNICIPIO_PROVA', 'NO_MUNICIPIO_ESC']:
        if c in cols:
            exprs.append(pl.col(c).cast(pl.Utf8).str.to_uppercase().str.strip_chars().is_in(BAIXADA_MUNICIPIOS))
            
    if not exprs:
        print(f"[Ano {ano}] Nenhuma coluna de município encontrada!")
        return None
        
    filter_expr = exprs[0]
    for e in exprs[1:]:
        filter_expr = filter_expr | e
        
    df = df.filter(filter_expr)
    
    if 'IN_TREINEIRO' in cols:
        df = df.filter(pl.col('IN_TREINEIRO') != 1)
    elif 'TP_ST_CONCLUSAO' in cols:
        df = df.filter(pl.col('TP_ST_CONCLUSAO') != 3)
        
    pres_cols = [c for c in cols if 'TP_PRESENCA' in c]
    for pc in pres_cols:
        df = df.filter(pl.col(pc) == 1)
        
    nota_cols = [c for c in cols if 'NU_NOTA' in c and 'REDACAO' not in c]
    if len(nota_cols) == 4:
        nota_exprs = [pl.col(c).cast(pl.Float64) for c in nota_cols]
        media_expr = (nota_exprs[0] + nota_exprs[1] + nota_exprs[2] + nota_exprs[3]) / 4.0
        df = df.with_columns(media_expr.alias('NOTA_MEDIA_OBJ'))
        
    if 'Q006' in cols:
        df = df.with_columns(pl.col('Q006').cast(pl.Utf8).str.to_uppercase().replace_strict(DICT_RENDA, default=pl.col('Q006')).alias('RENDA_FAMILIAR'))
    if 'Q002' in cols:
        df = df.with_columns(pl.col('Q002').cast(pl.Utf8).str.to_uppercase().replace_strict(DICT_ESCOLARIDADE, default=pl.col('Q002')).alias('ESCOLARIDADE_MAE'))
    if 'Q001' in cols:
        df = df.with_columns(pl.col('Q001').cast(pl.Utf8).str.to_uppercase().replace_strict(DICT_ESCOLARIDADE, default=pl.col('Q001')).alias('ESCOLARIDADE_PAI'))
    if 'TP_COR_RACA' in cols:
        df = df.with_columns(pl.col('TP_COR_RACA').cast(pl.Int32, strict=False).replace_strict(DICT_RACA, default=pl.col('TP_COR_RACA').cast(pl.Utf8)).alias('RACA_DESC'))
    if 'TP_ESCOLA' in cols:
        df = df.with_columns(pl.col('TP_ESCOLA').cast(pl.Int32, strict=False).replace_strict(DICT_ESCOLA, default=pl.col('TP_ESCOLA').cast(pl.Utf8)).alias('TIPO_ESCOLA'))
        
    if 'NU_ANO' not in cols:
        df = df.with_columns(pl.lit(ano).alias('NU_ANO'))
        
    print(f"[Ano {ano}] Extraindo dados para memória...")
    try:
        df_collected = df.collect()
    except Exception as e:
        print(f"[Ano {ano}] Erro ao coletar (tentando fallback): {e}")
        df_fallback = pl.read_csv(file_path, separator=';', columns=keep_cols, infer_schema_length=10000, ignore_errors=True, encoding='iso-8859-1', quote_char=None).lazy()
        df_fallback = df_fallback.filter(filter_expr)
        df_collected = df_fallback.collect()
        
    linhas = df_collected.height
    out_file = f"{out_dir}/enem_microdados_{ano}.parquet"
    df_collected.write_parquet(out_file)
    print(f"[Ano {ano}] Concluído: {linhas} registros salvos em {out_file}")
    
    del df_collected
    gc.collect()
    return out_file

def main():
    os.makedirs(out_dir, exist_ok=True)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'consolidate':
        # Apenas consolidar
        print("\nIniciando consolidação de todos os anos...")
        files = sorted(glob.glob('curated/parquet/enem/microdados_por_ano/*.parquet'))
        dfs = []
        for file in files:
            print(f"  Lendo {file}...")
            df = pl.read_parquet(file)
            dfs.append(df)
        print("Concatenando dados (Diagonal Relaxed)...")
        df_final = pl.concat(dfs, how='diagonal_relaxed')
        final_path = 'curated/parquet/enem/dataset_enem_microdados_baixada.parquet'
        df_final.write_parquet(final_path)
        print(f"Consolidação concluída! Total de registros: {df_final.height}")
        sys.exit(0)

    # Definir quais anos processar
    if len(sys.argv) > 1:
        # Se passar anos na linha de comando
        try:
            anos = [int(x) for x in sys.argv[1:] if x.isdigit()]
        except ValueError:
            anos = list(range(2013, 2023))
    else:
        # Por padrão, reprocessa os anos que faltam (2017 a 2022)
        # para economizar tempo, uma vez que 2013 a 2016 já foram processados!
        # Mas vamos permitir reprocessar todos se for o caso.
        # Vamos rodar os anos pendentes: 2017 a 2022
        anos = list(range(2017, 2023))

    print(f"Anos a processar concorrentemente: {anos}")
    
    # Processamento paralelo
    # Limitando a 2 workers para evitar estourar a memória
    max_workers = min(2, len(anos))
    print(f"Iniciando ProcessPoolExecutor com {max_workers} workers...")
    
    resultados = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(processar_ano, ano): ano for ano in anos}
        
        for future in as_completed(futures):
            ano = futures[future]
            try:
                out_file = future.result()
                if out_file:
                    resultados.append(out_file)
            except Exception as e:
                print(f"[Ano {ano}] Ocorreu um erro na thread/processo: {e}")
                
    print("\nTodos os anos do lote foram processados!")
    
    # Faz a consolidação automática com todos os arquivos que estão na pasta
    print("\nIniciando consolidação automática...")
    files = sorted(glob.glob('curated/parquet/enem/microdados_por_ano/*.parquet'))
    dfs = []
    for file in files:
        print(f"  Lendo {file}...")
        df = pl.read_parquet(file)
        dfs.append(df)
    print("Concatenando dados (Diagonal Relaxed)...")
    df_final = pl.concat(dfs, how='diagonal_relaxed')
    final_path = 'curated/parquet/enem/dataset_enem_microdados_baixada.parquet'
    df_final.write_parquet(final_path)
    print(f"Consolidação concluída! Total de registros: {df_final.height}")

if __name__ == '__main__':
    main()
