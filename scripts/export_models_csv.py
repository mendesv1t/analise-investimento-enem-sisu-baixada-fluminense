import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from pathlib import Path

# Paths
CURATED = Path("curated/parquet")
OUTPUT = Path("output/modelos")
OUTPUT.mkdir(parents=True, exist_ok=True)

# Load data
print("Carregando dados...")
df_enem = pd.read_parquet(CURATED / "enem/dataset_enem_microdados_baixada.parquet")
df_fundeb = pd.read_parquet(CURATED / "fundeb/dataset_fundeb_municipio_ano.parquet")

# Rename columns
df_fundeb = df_fundeb.rename(columns={'municipio': 'NO_MUNICIPIO_ESC', 'ano': 'NU_ANO'})

# Merge
df_model = pd.merge(df_enem, df_fundeb, on=['NO_MUNICIPIO_ESC', 'NU_ANO'], how='inner')

# Select variables
features = ['total_geral', 'RENDA_FAMILIAR', 'ESCOLARIDADE_MAE', 'TP_DEPENDENCIA_ADM_ESC', 'NO_MUNICIPIO_ESC']
target = 'NOTA_MEDIA_OBJ'
df_model = df_model[features + [target]].dropna()

# Map school network
rede_str_map = {1.0: 'B_Federal', 2.0: 'A_Estadual', 3.0: 'C_Municipal', 4.0: 'D_Privada'}
df_model['TP_DEPENDENCIA_ADM_ESC'] = df_model['TP_DEPENDENCIA_ADM_ESC'].map(rede_str_map)

# Split features & target
num_features = ['total_geral']
cat_features = ['TP_DEPENDENCIA_ADM_ESC', 'NO_MUNICIPIO_ESC', 'RENDA_FAMILIAR', 'ESCOLARIDADE_MAE']

X = df_model[num_features + cat_features]
y = df_model[target]

# Train/Test Split (80/20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Preprocessor
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), num_features),
        ('cat', OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False), cat_features)
    ])

# 1. RIDGE MODEL
print("Treinando Ridge...")
ridge_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                ('model', Ridge(alpha=1.0))])
ridge_pipeline.fit(X_train, y_train)

# Coefs extraction
ridge_model = ridge_pipeline.named_steps['model']
coefs = ridge_model.coef_
cat_encoder = ridge_pipeline.named_steps['preprocessor'].named_transformers_['cat']
cat_features_out = cat_encoder.get_feature_names_out(cat_features)
all_features = num_features + list(cat_features_out)
df_coef_raw = pd.DataFrame({'Feature': all_features, 'Coefficient': coefs})

rede_map = {
    'TP_DEPENDENCIA_ADM_ESC_B_Federal': 'Rede: Federal',
    'TP_DEPENDENCIA_ADM_ESC_C_Municipal': 'Rede: Municipal',
    'TP_DEPENDENCIA_ADM_ESC_D_Privada': 'Rede: Privada',
}

group_map = {
    'total_geral':       'Repasse FUNDEB (R$)',
    'NO_MUNICIPIO_ESC':  'Município da Escola (média)',
    'ESCOLARIDADE_MAE':  'Escolaridade da Mãe (média)',
    'ESCOLARIDADE_PAI':  'Escolaridade do Pai (média)',
}

rows = []
grouped = {}

for _, row in df_coef_raw.iterrows():
    feat = row['Feature']
    coef = row['Coefficient']

    if feat in rede_map:
        rows.append({'Variável': rede_map[feat], 'Coefficient': coef})
    elif feat.startswith('RENDA_FAMILIAR_'):
        label = 'Renda: ' + feat.replace('RENDA_FAMILIAR_', '')
        rows.append({'Variável': label, 'Coefficient': coef})
    else:
        matched = False
        for prefix, label in group_map.items():
            if feat == prefix or feat.startswith(prefix + '_'):
                grouped.setdefault(label, []).append(coef)
                matched = True
                break
        if not matched:
            rows.append({'Variável': feat, 'Coefficient': coef})

for label, coef_list in grouped.items():
    rows.append({'Variável': label, 'Coefficient': sum(coef_list)/len(coef_list)})

rows.append({'Variável': 'Rede: Estadual (baseline=0)', 'Coefficient': 0.0})
df_coef = pd.DataFrame(rows).sort_values('Coefficient', ascending=True)
df_coef.to_csv(OUTPUT / "ridge_coeficientes.csv", index=False)
print("Salvo: ridge_coeficientes.csv")

# 2. RANDOM FOREST MODEL (using the best params from CV: depth=10, split=5, estimators=50)
print("Treinando Random Forest...")
rf_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                              ('model', RandomForestRegressor(n_estimators=50, max_depth=10, min_samples_split=5, random_state=42, n_jobs=-1))])
rf_pipeline.fit(X_train, y_train)

# Feature importance extraction
best_rf = rf_pipeline
importances = best_rf.named_steps['model'].feature_importances_
cat_encoder = best_rf.named_steps['preprocessor'].named_transformers_['cat']
cat_features_out = cat_encoder.get_feature_names_out(cat_features)
all_features = num_features + list(cat_features_out)
df_imp_raw = pd.DataFrame({'Feature': all_features, 'Importance': importances})

rede_map_imp = {
    'TP_DEPENDENCIA_ADM_ESC_B_Federal': 'Rede: Federal',
    'TP_DEPENDENCIA_ADM_ESC_C_Municipal': 'Rede: Municipal',
    'TP_DEPENDENCIA_ADM_ESC_D_Privada': 'Rede: Privada',
}

group_map_imp = {
    'total_geral':       'Repasse FUNDEB (R$)',
    'NO_MUNICIPIO_ESC':  'Município da Escola',
    'ESCOLARIDADE_MAE':  'Escolaridade da Mãe',
    'ESCOLARIDADE_PAI':  'Escolaridade do Pai',
    'RENDA_FAMILIAR':    'Renda Familiar',
}

rows_imp = []
grouped_imp = {}

for _, row in df_imp_raw.iterrows():
    feat = row['Feature']
    imp = row['Importance']

    if feat in rede_map_imp:
        rows_imp.append({'Variável': rede_map_imp[feat], 'Importance': imp})
    else:
        matched = False
        for prefix, label in group_map_imp.items():
            if feat == prefix or feat.startswith(prefix + '_'):
                grouped_imp.setdefault(label, []).append(imp)
                matched = True
                break
        if not matched:
            rows_imp.append({'Variável': feat, 'Importance': imp})

for label, imp_list in grouped_imp.items():
    rows_imp.append({'Variável': label, 'Importance': sum(imp_list)})

df_imp = pd.DataFrame(rows_imp).sort_values('Importance', ascending=True)
df_imp.to_csv(OUTPUT / "rf_feature_importance.csv", index=False)
print("Salvo: rf_feature_importance.csv")
