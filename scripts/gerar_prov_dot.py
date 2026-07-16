import os
from prov.model import ProvDocument
from prov.dot import prov_to_dot

def generate_and_draw_provenance():
    # ─── 1. CRIAR DOCUMENTO W3C PROV ───
    doc = ProvDocument()
    doc.add_namespace('ex', 'http://example.org/education-provenance#')
    
    # Entidades (Dados e Modelos)
    raw_enem = doc.entity('ex:raw_enem', {'prov:label': 'Microdados do ENEM (2013-2022) - INEP'})
    raw_fundeb = doc.entity('ex:raw_fundeb', {'prov:label': 'Relatórios do FUNDEB (2011-2024) - FNDE'})
    raw_sisu = doc.entity('ex:raw_sisu', {'prov:label': 'Microdados do SISU (2014-2023) - MEC'})
    
    curated_enem = doc.entity('ex:curated_enem', {'prov:label': 'ENEM Curated (dataset_enem_microdados_baixada.parquet)'})
    curated_fundeb = doc.entity('ex:curated_fundeb', {'prov:label': 'FUNDEB Curated (dataset_fundeb_municipio_ano.parquet)'})
    curated_sisu = doc.entity('ex:curated_sisu', {'prov:label': 'SISU Curated (dataset_sisu_municipio_ano.parquet)'})
    
    model_outputs = doc.entity('ex:model_outputs', {'prov:label': 'Model Outputs (rf_feature_importance.csv, municipios_clusters.csv)'})
    dashboard_app = doc.entity('ex:dashboard_app', {'prov:label': 'Dashboard Interativo (Streamlit App)'})
    
    # Atividades (Processamento)
    act_ingest_enem = doc.activity('ex:act_ingest_enem', other_attributes={'prov:label': 'Filtragem de treineiros/presença e filtro geográfico'})
    act_ingest_fundeb = doc.activity('ex:act_ingest_fundeb', other_attributes={'prov:label': 'Deflacionamento pelo IPCA e agrupamento por município e ano'})
    act_ingest_sisu = doc.activity('ex:act_ingest_sisu', other_attributes={'prov:label': 'Filtragem de município de origem'})
    
    act_model_training = doc.activity('ex:act_model_training', other_attributes={'prov:label': 'Treinamento do Random Forest Regressor e Clusterização K-Means'})
    act_dashboard_run = doc.activity('ex:act_dashboard_run', other_attributes={'prov:label': 'Renderização visual e cálculo de KPIs dinâmicos'})
    
    # Relações (Linhagem)
    doc.generation(curated_enem, act_ingest_enem)
    doc.usage(act_ingest_enem, raw_enem)
    doc.derivation(curated_enem, raw_enem)
    
    doc.generation(curated_fundeb, act_ingest_fundeb)
    doc.usage(act_ingest_fundeb, raw_fundeb)
    doc.derivation(curated_fundeb, raw_fundeb)
    
    doc.generation(curated_sisu, act_ingest_sisu)
    doc.usage(act_ingest_sisu, raw_sisu)
    doc.derivation(curated_sisu, raw_sisu)
    
    doc.generation(model_outputs, act_model_training)
    doc.usage(act_model_training, curated_enem)
    doc.usage(act_model_training, curated_fundeb)
    doc.usage(act_model_training, curated_sisu)
    doc.derivation(model_outputs, curated_enem)
    doc.derivation(model_outputs, curated_fundeb)
    doc.derivation(model_outputs, curated_sisu)
    
    doc.generation(dashboard_app, act_dashboard_run)
    doc.usage(act_dashboard_run, curated_enem)
    doc.usage(act_dashboard_run, curated_fundeb)
    doc.usage(act_dashboard_run, curated_sisu)
    doc.usage(act_dashboard_run, model_outputs)
    doc.derivation(dashboard_app, curated_enem)
    doc.derivation(dashboard_app, curated_fundeb)
    doc.derivation(dashboard_app, curated_sisu)
    doc.derivation(dashboard_app, model_outputs)
    
    # ─── 2. SERIALIZAR ARQUIVOS DE METADADOS ───
    # XML
    xml_data = doc.serialize(format='xml')
    if isinstance(xml_data, bytes): xml_data = xml_data.decode('utf-8')
    with open('provenance/data_provenance.xml', 'w', encoding='utf-8') as f: f.write(xml_data)
        
    # JSON
    json_data = doc.serialize(format='json')
    if isinstance(json_data, bytes): json_data = json_data.decode('utf-8')
    with open('provenance/data_provenance.json', 'w', encoding='utf-8') as f: f.write(json_data)
        
    # RDF Turtle
    rdf_data = doc.serialize(format='rdf', rdf_format='turtle')
    if isinstance(rdf_data, bytes): rdf_data = rdf_data.decode('utf-8')
    with open('provenance/data_provenance.ttl', 'w', encoding='utf-8') as f: f.write(rdf_data)
        
    # ─── 3. GERAR GRAFO COM DOT (Graphviz) ───
    dot = prov_to_dot(doc)
    dot.write_png('provenance/data_provenance_dot.png')
    
if __name__ == "__main__":
    generate_and_draw_provenance()
    print("Sucesso! Grafo de proveniencia gerado em provenance/data_provenance_dot.png usando prov.dot")
