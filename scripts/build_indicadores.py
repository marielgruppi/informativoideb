"""
Processa os arquivos oficiais do Inep (divulgação Ideb por município e por escola,
2025) cruzando com o crosswalk RGInt/SRE, e gera uma planilha de indicadores
agregados prontos para os gráficos do informativo Ideb-MG.

Fontes (baixadas do Inep e do IBGE, na raiz do repo):
  - divulgacao_{anos_iniciais,anos_finais,ensino_medio}_municipios_2025.xlsx
  - divulgacao_{anos_iniciais,anos_finais,ensino_medio}_escolas_2025.xlsx
  - RGInt_SRE_MUN_UF.xlsx (aba DTB_Municípios_SRE_MG: cruzamento município -> RGInt/SRE)

Saída: analise/indicadores_ideb_mg.xlsx
"""
import re
import openpyxl
import pandas as pd

UF_VALIDAS = {
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB",
    "PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO",
}

ETAPAS = {
    "anos_iniciais": "Anos Iniciais do Ensino Fundamental",
    "anos_finais": "Anos Finais do Ensino Fundamental",
    "ensino_medio": "Ensino Médio",
}


def to_num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s in ("-", "", "ND*", "ND**", "ND***", "ND"):
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def load_divulgacao(path, nivel):
    """nivel: 'municipio' ou 'escola'. Retorna DataFrame long: uma linha por
    (chave, rede, ano) com colunas P, N, IDEB, META."""
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    codes = rows[9]

    col = {c: i for i, c in enumerate(codes) if c}
    idx_uf = col["SG_UF"]
    idx_mun_cod = col["CO_MUNICIPIO"]
    idx_mun_nome = col["NO_MUNICIPIO"]
    idx_rede = col["REDE"]
    if nivel == "escola":
        idx_esc_cod = col["ID_ESCOLA"]
        idx_esc_nome = col["NO_ESCOLA"]

    # mapeia ano -> índices de P, N, IDEB
    anos = {}
    for code, i in col.items():
        m = re.match(r"VL_(OBSERVADO|NOTA_MEDIA|INDICADOR_REND|PROJECAO)_(\d+)", code)
        if not m:
            continue
        kind, ano = m.groups()
        ano = int(re.sub(r"\D", "", ano)[:4])  # "20212" -> "2021"
        anos.setdefault(ano, {})[kind] = i

    records = []
    for row in rows[10:]:
        uf = row[idx_uf]
        if uf not in UF_VALIDAS:
            continue
        base = {
            "UF": uf,
            "CO_MUNICIPIO": row[idx_mun_cod],
            "NO_MUNICIPIO": row[idx_mun_nome],
            "REDE": row[idx_rede],
        }
        if nivel == "escola":
            base["CO_ESCOLA"] = row[idx_esc_cod]
            base["NO_ESCOLA"] = row[idx_esc_nome]
        for ano, idxs in anos.items():
            ideb = to_num(row[idxs["OBSERVADO"]]) if "OBSERVADO" in idxs else None
            n = to_num(row[idxs["NOTA_MEDIA"]]) if "NOTA_MEDIA" in idxs else None
            p = to_num(row[idxs["INDICADOR_REND"]]) if "INDICADOR_REND" in idxs else None
            meta = to_num(row[idxs["PROJECAO"]]) if "PROJECAO" in idxs else None
            if ideb is None and n is None and p is None:
                continue
            rec = dict(base)
            rec.update(ANO=ano, IDEB=ideb, N=n, P=p, META=meta)
            records.append(rec)
    df = pd.DataFrame.from_records(records)
    return df


def faixa_ideb(v):
    if v is None or pd.isna(v):
        return None
    if v < 4:
        return "< 4"
    if v < 5:
        return "4 a 4,9"
    if v < 6:
        return "5 a 5,9"
    return ">= 6"


def main():
    print("Carregando crosswalk RGInt/SRE...")
    cross = pd.read_excel("RGInt_SRE_MUN_UF.xlsx", sheet_name="DTB_Municípios_SRE_MG")
    cross = cross.rename(columns={
        "id_municipio": "CO_MUNICIPIO",
        "nome_municipio": "NO_MUNICIPIO_CROSS",
        "nome_rgint": "RGINT",
        "sre": "SRE",
    })[["CO_MUNICIPIO", "RGINT", "SRE"]]
    cross["CO_MUNICIPIO"] = cross["CO_MUNICIPIO"].astype(int)
    cross["SRE"] = cross["SRE"].str.replace("SRE ", "", regex=False).str.title()

    out = {}

    # ---- Série histórica por município (MG) — Gráficos 1 a 5 ----
    serie_frames = []
    for etapa_key, etapa_nome in ETAPAS.items():
        print(f"Lendo divulgacao_{etapa_key}_municipios_2025.xlsx ...")
        df = load_divulgacao(f"divulgacao_{etapa_key}_municipios_2025.xlsx", "municipio")
        df = df[df["UF"] == "MG"].copy()
        df["ETAPA"] = etapa_nome
        serie_frames.append(df)
    serie_mun = pd.concat(serie_frames, ignore_index=True)
    serie_mun = serie_mun.merge(cross, on="CO_MUNICIPIO", how="left")
    out["Serie_Municipios_MG"] = serie_mun

    # Média simples entre municípios por rede/etapa/ano — aproximação do "MG total"
    # (Inep calcula o agregado estadual a partir dos microdados pool, não como média
    # simples dos municípios; usar com essa ressalva no texto).
    approx_mg = (
        serie_mun.groupby(["ETAPA", "REDE", "ANO"])[["IDEB", "N", "P"]]
        .mean()
        .round(2)
        .reset_index()
        .sort_values(["ETAPA", "REDE", "ANO"])
    )
    out["MG_aprox_media_municipios"] = approx_mg

    # Variação P e N entre 2023 e 2025, por rede/etapa (Gráfico 5) — a partir da
    # mesma aproximação por média simples de municípios.
    piv = approx_mg[approx_mg["ANO"].isin([2023, 2025])].pivot_table(
        index=["ETAPA", "REDE"], columns="ANO", values=["N", "P"]
    )
    piv.columns = [f"{v}_{a}" for v, a in piv.columns]
    piv = piv.reset_index()
    piv["VAR_N_23_25"] = (piv["N_2025"] - piv["N_2023"]).round(3)
    piv["VAR_P_23_25"] = (piv["P_2025"] - piv["P_2023"]).round(3)
    out["Variacao_N_P_2023_2025"] = piv

    # ---- Nível escola: % de escolas por faixa de Ideb, por SRE/RGInt (2025) ----
    faixa_frames = []
    for etapa_key, etapa_nome in ETAPAS.items():
        print(f"Lendo divulgacao_{etapa_key}_escolas_2025.xlsx ...")
        df = load_divulgacao(f"divulgacao_{etapa_key}_escolas_2025.xlsx", "escola")
        df = df[(df["UF"] == "MG") & (df["ANO"] == 2025)].copy()
        df["ETAPA"] = etapa_nome
        faixa_frames.append(df)
    escolas_2025 = pd.concat(faixa_frames, ignore_index=True)
    escolas_2025 = escolas_2025.merge(cross, on="CO_MUNICIPIO", how="left")
    escolas_2025["FAIXA"] = escolas_2025["IDEB"].apply(faixa_ideb)
    out["Escolas_2025_MG"] = escolas_2025

    def tabela_faixas(df, rede, dimensao):
        sub = df[(df["REDE"] == rede) & df["FAIXA"].notna()].copy()
        tab = (
            sub.groupby(["ETAPA", dimensao, "FAIXA"])
            .size()
            .rename("N_ESCOLAS")
            .reset_index()
        )
        totais = tab.groupby(["ETAPA", dimensao])["N_ESCOLAS"].transform("sum")
        tab["PCT_ESCOLAS"] = (tab["N_ESCOLAS"] / totais * 100).round(1)
        return tab.sort_values(["ETAPA", dimensao, "FAIXA"])

    out["Faixas_Estadual_por_SRE"] = tabela_faixas(escolas_2025, "Estadual", "SRE")
    out["Faixas_Estadual_por_RGInt"] = tabela_faixas(escolas_2025, "Estadual", "RGINT")
    out["Faixas_Municipal_por_SRE"] = tabela_faixas(
        escolas_2025[escolas_2025["ETAPA"] != "Ensino Médio"], "Municipal", "SRE"
    )
    out["Faixas_Municipal_por_RGInt"] = tabela_faixas(
        escolas_2025[escolas_2025["ETAPA"] != "Ensino Médio"], "Municipal", "RGINT"
    )

    # N de escolas por SRE/rede/etapa, para aplicar corte de N mínimo depois se quiserem
    contagem = (
        escolas_2025.groupby(["ETAPA", "REDE", "SRE"])
        .size()
        .rename("N_ESCOLAS_TOTAL")
        .reset_index()
    )
    out["Contagem_Escolas_por_SRE"] = contagem

    print("Salvando analise/indicadores_ideb_mg.xlsx ...")
    import os
    os.makedirs("analise", exist_ok=True)
    with pd.ExcelWriter("analise/indicadores_ideb_mg.xlsx", engine="openpyxl") as writer:
        for name, df in out.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    print("OK")


if __name__ == "__main__":
    main()
