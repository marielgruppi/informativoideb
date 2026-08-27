"""Gera as imagens dos Gráficos 1 a 10 do informativo Ideb-MG 2025 a partir de
analise/indicadores_ideb_mg.xlsx. Saída: analise/graficos/grafico_N.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# Paleta categórica validada (skill dataviz) — ordem fixa por série.
BLUE = "#2a78d6"    # MG 2023
ORANGE = "#eb6834"  # MG 2025
AQUA = "#1baf7a"    # Brasil 2025
YELLOW = "#eda100"
GRID = "#d9d8d3"
TEXT = "#0b0b0b"
TEXT_MUTED = "#52514e"

plt.rcParams.update({
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT,
    "text.color": TEXT,
    "xtick.color": TEXT_MUTED,
    "ytick.color": TEXT_MUTED,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})

OUT = "analise/graficos"
os.makedirs(OUT, exist_ok=True)

xls = pd.ExcelFile("analise/indicadores_ideb_mg.xlsx")
serie_uf = pd.read_excel(xls, "Serie_UF_Regiao")
serie_mun = pd.read_excel(xls, "Serie_Municipios_MG")
escolas = pd.read_excel(xls, "Escolas_2025_MG")

ETAPAS = [
    "Anos Iniciais do Ensino Fundamental",
    "Anos Finais do Ensino Fundamental",
    "Ensino Médio",
]
ETAPA_ABREV = {
    "Anos Iniciais do Ensino Fundamental": "Anos iniciais",
    "Anos Finais do Ensino Fundamental": "Anos finais",
    "Ensino Médio": "Ensino médio",
}
REDES_ORDEM = ["Estadual", "Municipal", "Privada", "Pública"]

# O Inep não publica, nesta tabela de UF/Região, um agregado estadual da rede
# municipal (só Estadual, Privada, Pública e Total). Para poder mostrar a rede
# municipal nos Gráficos 1, 2, 3 e 5, usamos a média simples dos municípios de
# MG como aproximação — deixamos isso marcado (estilo tracejado/hachurado +
# nota de rodapé) em vez de apresentar como valor oficial.
_municipal_approx = (
    serie_mun[(serie_mun.REDE == "Municipal") & (serie_mun.ETAPA != "Ensino Médio")]
    .groupby(["ETAPA", "ANO"])[["IDEB", "N", "P"]]
    .mean()
    .reset_index()
)
_municipal_approx["REDE"] = "Municipal"
_municipal_approx["UF"] = "MG"
_municipal_approx["NOME"] = "Minas Gerais"
serie_uf = pd.concat([serie_uf, _municipal_approx], ignore_index=True)


def savefig(fig, name):
    path = f"{OUT}/{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("salvo:", path)


# ---------------------------------------------------------------------------
# Gráfico 1 — Ideb por rede de ensino, Brasil 2025 e Minas Gerais 2023–2025
# ---------------------------------------------------------------------------
def grafico_1():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3), sharey=True)
    for ax, etapa in zip(axes, ETAPAS):
        sub = serie_uf[(serie_uf.ETAPA == etapa) & (serie_uf.ANO.isin([2023, 2025]))]
        mg = sub[sub.UF == "MG"].set_index(["REDE", "ANO"])["IDEB"]
        br = sub[sub.NOME == "Brasil"].set_index(["REDE", "ANO"])["IDEB"]
        redes = [r for r in REDES_ORDEM if (r, 2025) in mg.index]
        x = range(len(redes))
        w = 0.27
        mg23 = [mg.get((r, 2023), float("nan")) for r in redes]
        mg25 = [mg.get((r, 2025), float("nan")) for r in redes]
        br25 = [br.get((r, 2025), float("nan")) for r in redes]
        b1 = ax.bar([i - w for i in x], mg23, width=w, color=BLUE, label="MG 2023")
        b2 = ax.bar([i for i in x], mg25, width=w, color=ORANGE, label="MG 2025")
        b3 = ax.bar([i + w for i in x], br25, width=w, color=AQUA, label="Brasil 2025")
        for bars in (b1, b2, b3):
            ax.bar_label(bars, fmt="%.1f", fontsize=9, padding=1, color=TEXT_MUTED)
        # Municipal é aproximação (média dos municípios), marcada com hachura.
        if "Municipal" in redes:
            i_mun = redes.index("Municipal")
            for bars in (b1, b2, b3):
                bars.patches[i_mun].set_hatch("///")
                bars.patches[i_mun].set_edgecolor("white")
        ax.set_xticks(list(x))
        ax.set_xticklabels(redes, fontsize=9)
        ax.set_title(ETAPA_ABREV[etapa], fontsize=10, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Ideb")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.06))
    fig.suptitle("Gráfico 1: Ideb por rede de ensino, Brasil 2025 e Minas Gerais, 2023-2025", y=1.14, fontsize=11)
    fig.text(0.02, -0.05, "Nota: barras hachuradas (rede Municipal) indicam aproximação pela média simples dos municípios de MG; o Inep não publica agregado estadual dessa rede nesta tabela.", fontsize=9, color=TEXT_MUTED)
    fig.text(0.02, -0.095, "Fonte: Inep/MEC, divulgação Ideb 2025 (por município e por UF).", fontsize=9, color=TEXT_MUTED)
    savefig(fig, "grafico_1")


# ---------------------------------------------------------------------------
# Gráficos 2, 3, 4 — evolução histórica por rede, MG (nível UF), 2005/2007–2025
# ---------------------------------------------------------------------------
def rotula_extremos(ax, sub, cores, prioridade):
    """Rotula pico, vale, primeiro e último ano de cada série, pulando
    rótulos que ficariam colados em outro já colocado."""
    x0, x1 = min(sub.ANO), max(sub.ANO)
    y0, y1 = ax.get_ylim()
    colocados = []  # (x_norm, y_norm)

    def perto_demais(xn, yn):
        return any(((xn - px) ** 2 + (yn - py) ** 2) ** 0.5 < 0.065 for px, py in colocados)

    for rede in prioridade:
        if rede not in cores:
            continue
        s = sub[sub.REDE == rede].sort_values("ANO")
        if len(s) < 2:
            continue
        cor = cores[rede]
        candidatos = [s.IDEB.idxmax(), s.IDEB.idxmin(), s.index[0], s.index[-1]]
        for i in candidatos:
            ano, val = s.loc[i, "ANO"], s.loc[i, "IDEB"]
            xn, yn = (ano - x0) / (x1 - x0 or 1), (val - y0) / (y1 - y0 or 1)
            if perto_demais(xn, yn):
                continue
            colocados.append((xn, yn))
            acima = yn >= 0.5
            offset = 9 if acima else -11
            va = "bottom" if acima else "top"
            ax.annotate(
                f"{val:.1f}", xy=(ano, val), xytext=(0, offset), textcoords="offset points",
                ha="center", va=va, fontsize=7.5, color=cor, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.8),
            )


def grafico_evolucao(etapa, numero, titulo):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    sub = serie_mg = serie_uf[(serie_uf.ETAPA == etapa) & (serie_uf.UF == "MG")]
    cores = {"Estadual": BLUE, "Municipal": ORANGE, "Privada": YELLOW, "Pública": AQUA}
    estilos = {"Municipal": (0, (4, 2))}  # tracejado = aproximação por média de municípios
    for rede, cor in cores.items():
        s = sub[sub.REDE == rede].sort_values("ANO")
        if s.empty:
            continue
        ax.plot(s.ANO, s.IDEB, marker="o", markersize=4, linewidth=2, color=cor, label=rede,
                linestyle=estilos.get(rede, "-"))
    # marca 2021 (ciclo pós-pandemia)
    if 2021 in sub.ANO.values:
        ax.axvline(2021, color=GRID, linewidth=8, alpha=0.5, zorder=0)
        ax.annotate("2021\nciclo pós-pandemia", xy=(2021, ax.get_ylim()[0]),
                    xytext=(2021, ax.get_ylim()[0]), fontsize=9, color=TEXT_MUTED,
                    ha="center", va="bottom")
    ax.set_ylabel("Ideb")
    ax.spines[["top", "right"]].set_visible(False)
    anos_com_dado = sorted(sub.ANO.unique())
    ax.xaxis.set_major_locator(mticker.FixedLocator(anos_com_dado))
    ax.set_xticklabels([str(int(a)) for a in anos_com_dado], rotation=45, ha="right")
    ax.set_xlim(min(anos_com_dado) - 0.5, max(anos_com_dado) + 0.5)
    ymin, ymax = ax.get_ylim()
    pad = (ymax - ymin) * 0.12
    ax.set_ylim(ymin - pad, ymax + pad)
    rotula_extremos(ax, sub, cores, ["Estadual", "Pública", "Privada", "Municipal"])
    fig.suptitle(f"Gráfico {numero}: {titulo}", fontsize=11)
    # Legenda embaixo (fora da área de plotagem), pra nunca sobrepor o
    # primeiro ponto de nenhuma série.
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=4)
    if "Municipal" in sub.REDE.unique():
        fig.text(0.02, -0.40, "Linha tracejada (Municipal): aproximação pela média simples dos municípios de MG.\nO Inep não publica agregado estadual dessa rede nesta tabela.", fontsize=9, color=TEXT_MUTED)
    savefig(fig, f"grafico_{numero}")


# ---------------------------------------------------------------------------
# Gráfico 5 — Variação de desempenho (N) e rendimento (P), 2023 -> 2025, por rede
# ---------------------------------------------------------------------------
def grafico_5():
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, etapa in zip(axes, ETAPAS):
        sub = serie_uf[(serie_uf.ETAPA == etapa) & (serie_uf.UF == "MG") & (serie_uf.ANO.isin([2023, 2025]))]
        redes = [r for r in REDES_ORDEM if r in sub.REDE.unique()]
        var_n, var_p = [], []
        for r in redes:
            s = sub[sub.REDE == r].set_index("ANO")
            var_n.append((s.loc[2025, "N"] - s.loc[2023, "N"]) / s.loc[2023, "N"] * 100)
            var_p.append((s.loc[2025, "P"] - s.loc[2023, "P"]) / s.loc[2023, "P"] * 100)
        x = range(len(redes))
        w = 0.33
        b1 = ax.bar([i - w / 2 for i in x], var_n, width=w, color=BLUE, label="Δ% Desempenho (N)")
        b2 = ax.bar([i + w / 2 for i in x], var_p, width=w, color=ORANGE, label="Δ% Rendimento (P)")
        ax.bar_label(b1, fmt="%.1f%%", fontsize=9, padding=1, color=TEXT_MUTED)
        ax.bar_label(b2, fmt="%.1f%%", fontsize=9, padding=1, color=TEXT_MUTED)
        if "Municipal" in redes:
            i_mun = redes.index("Municipal")
            b1.patches[i_mun].set_hatch("///")
            b2.patches[i_mun].set_hatch("///")
            b1.patches[i_mun].set_edgecolor("white")
            b2.patches[i_mun].set_edgecolor("white")
        ax.axhline(0, color=TEXT_MUTED, linewidth=0.8)
        ax.set_xticks(list(x))
        ax.set_xticklabels(redes, fontsize=9)
        ax.set_title(ETAPA_ABREV[etapa], fontsize=10, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Variação percentual (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.08))
    fig.suptitle("Gráfico 5: Variação percentual de desempenho (Saeb) e rendimento por rede, MG, 2023-2025", y=1.16, fontsize=11)
    savefig(fig, "grafico_5")


# ---------------------------------------------------------------------------
# Gráficos 6-8 (estadual) e 9-10 (municipal) — % de escolas por faixa de Ideb, por SRE
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Gráfico 6 — Ideb da rede estadual por UF, três etapas, 2025
# ---------------------------------------------------------------------------
def grafico_ranking_uf(numero, ano=2025):
    rk = pd.read_excel(xls, "Ranking_Estadual_por_UF")
    rk = rk[rk.ANO == ano]
    cores = {
        "Anos Iniciais do Ensino Fundamental": BLUE,
        "Anos Finais do Ensino Fundamental": AQUA,
        "Ensino Médio": YELLOW,
    }
    piv = rk.pivot(index="UF", columns="ETAPA", values="IDEB")[list(cores)]
    # Ordena pela média do Ideb nas etapas disponíveis (RR não tem valor de
    # anos iniciais em 2025, por isso não dá pra ordenar por uma etapa só).
    ordem = piv.mean(axis=1).sort_values().index.tolist()
    piv = piv.loc[ordem]

    altura_barras = max(3.2, 0.28 * len(ordem))
    header_in = 1.3
    bottom_in = 0.75
    fig_h = altura_barras + header_in
    fig, ax = plt.subplots(figsize=(8, fig_h))
    fig.subplots_adjust(top=altura_barras / fig_h, bottom=bottom_in / fig_h)

    y = list(range(len(ordem)))
    h = 0.24
    deslocs = {
        "Anos Iniciais do Ensino Fundamental": h,
        "Anos Finais do Ensino Fundamental": 0,
        "Ensino Médio": -h,
    }
    for etapa, cor in cores.items():
        barras = ax.barh([yy + deslocs[etapa] for yy in y], piv[etapa], height=h * 0.92, color=cor, label=ETAPA_ABREV[etapa])
        # Rotula só a UF em destaque (MG), pra não poluir com 27 UF x 3 etapas.
        rotulos = ["" if uf != "MG" else f"{v:.1f}" for uf, v in zip(ordem, piv[etapa])]
        ax.bar_label(barras, labels=rotulos, fontsize=8.5, padding=2, color=TEXT_MUTED, fontweight="bold")

    ax.set_yticks(y)
    labels = ax.set_yticklabels(ordem)
    if "MG" in ordem:
        i_mg = ordem.index("MG")
        labels[i_mg].set_fontweight("bold")
        ax.axhspan(i_mg - 1.5 * h, i_mg + 1.5 * h, color=GRID, alpha=0.6, zorder=0)
    ax.set_xlabel("Ideb")
    ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Gráfico {numero}: Ideb da rede estadual por UF e etapa de ensino, {ano}", fontsize=10.5, y=1 - 0.28 / fig_h)
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1 - 0.55 / fig_h), bbox_transform=fig.transFigure)
    fig.text(
        0.02, -0.55 / fig_h,
        "Nota: UF ordenadas pela média do Ideb nas três etapas; Minas Gerais em destaque.\n"
        "Fonte: Inep/MEC, divulgação Ideb 2025 por UF (ranking calculado sobre as 27 unidades da federação).",
        fontsize=9, color=TEXT_MUTED,
    )
    savefig(fig, f"grafico_{numero}")


FAIXA_ORDEM = ["< 4", "4 a 4,9", "5 a 5,9", ">= 6"]
FAIXA_CORES = {"< 4": "#e34948", "4 a 4,9": YELLOW, "5 a 5,9": "#8fd0ba", ">= 6": AQUA}


def grafico_faixas(rede, etapa, numero, titulo, min_escolas=3):
    sub = escolas[(escolas.REDE == rede) & (escolas.ETAPA == etapa) & escolas.FAIXA.notna()]
    cont = sub.groupby("SRE").size()
    sres_validas = cont[cont >= min_escolas].index
    tab = (
        sub[sub.SRE.isin(sres_validas)]
        .groupby(["SRE", "FAIXA"]).size().unstack(fill_value=0)
    )
    tab = tab.reindex(columns=FAIXA_ORDEM, fill_value=0)
    pct = tab.div(tab.sum(axis=1), axis=0) * 100
    pct = pct.sort_values(">= 6")

    # Reserva uma faixa de cabeçalho de altura FIXA (em polegadas) para título e
    # legenda, independente da altura do gráfico de barras (que cresce com o
    # número de SRE) — evita o espaço em branco que aparecia nos gráficos com
    # muitas linhas.
    altura_barras = max(3.2, 0.22 * len(pct))
    header_in = 1.3
    bottom_in = 0.7
    fig_h = altura_barras + header_in
    fig, ax = plt.subplots(figsize=(8, fig_h))
    fig.subplots_adjust(top=altura_barras / fig_h, bottom=bottom_in / fig_h)

    left = pd.Series(0.0, index=pct.index)
    for faixa in FAIXA_ORDEM:
        ax.barh(pct.index, pct[faixa], left=left, color=FAIXA_CORES[faixa], label=faixa, height=0.7)
        left += pct[faixa]
    ax.set_xlim(0, 100)
    ax.set_xlabel("Percentual de escolas")
    ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Gráfico {numero}: {titulo}", fontsize=10.5, y=1 - 0.28 / fig_h)
    ax.legend(
        title="Faixa de Ideb", frameon=False, ncol=4, loc="upper center",
        bbox_to_anchor=(0.5, 1 - 0.55 / fig_h), bbox_transform=fig.transFigure,
    )
    fig.text(0.02, -0.5 / fig_h, f"SRE com menos de {min_escolas} escolas nessa rede/etapa foram omitidas.", fontsize=9, color=TEXT_MUTED)
    savefig(fig, f"grafico_{numero}")


# ---------------------------------------------------------------------------
# Gráfico 12 — Inse (SRE) x percentual de escolas por faixa de Ideb, rede estadual
# ---------------------------------------------------------------------------
def grafico_inse(numero):
    inse = pd.read_excel(xls, "Inse_2023_por_SRE")
    inse = inse[inse.REDE == "Estadual"][["SRE", "MEDIA_INSE"]]
    corr = pd.read_excel(xls, "Correlacao_Inse_Ideb")

    sub = escolas[(escolas.REDE == "Estadual") & escolas.FAIXA.notna()]
    pct = (
        sub.groupby(["ETAPA", "SRE"])["FAIXA"]
        .value_counts(normalize=True)
        .mul(100)
        .rename("PCT")
        .reset_index()
    )

    def serie(etapa, faixa):
        d = pct[(pct.ETAPA == etapa) & (pct.FAIXA == faixa)][["SRE", "PCT"]]
        return inse.merge(d, on="SRE", how="inner")

    paineis = [
        (">= 6", "Percentual de escolas com Ideb >= 6", "CORR_INSE_x_PCT_IDEB_MAIOR_6", "P_VALOR_MAIOR_6",
         [("Anos Iniciais do Ensino Fundamental", BLUE), ("Anos Finais do Ensino Fundamental", AQUA)]),
        ("< 4", "Percentual de escolas com Ideb < 4", "CORR_INSE_x_PCT_IDEB_MENOR_4", "P_VALOR_MENOR_4",
         [("Anos Finais do Ensino Fundamental", AQUA), ("Ensino Médio", YELLOW)]),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, (faixa, ylabel, col_r, col_p, series) in zip(axes, paineis):
        for i, (etapa, cor) in enumerate(series):
            d = serie(etapa, faixa)
            ax.scatter(d.MEDIA_INSE, d.PCT, s=24, color=cor, alpha=0.8, label=ETAPA_ABREV[etapa])
            if len(d) >= 2:
                b, a = np.polyfit(d.MEDIA_INSE, d.PCT, 1)
                xs = np.linspace(d.MEDIA_INSE.min(), d.MEDIA_INSE.max(), 50)
                ax.plot(xs, a + b * xs, color=cor, linewidth=1.5, linestyle="--")
            r = float(corr.loc[corr.ETAPA == etapa, col_r].iloc[0])
            p = float(corr.loc[corr.ETAPA == etapa, col_p].iloc[0])
            p_txt = "p < 0,01" if p < 0.01 else f"p = {p:.2f}".replace(".", ",")
            ax.text(
                0.03, 0.96 - i * 0.08, f"{ETAPA_ABREV[etapa]}: r = {r:.2f} ({p_txt})".replace(".", ","),
                transform=ax.transAxes, fontsize=8.5, color=cor, va="top", fontweight="bold",
            )
        ax.set_xlabel("Inse médio da SRE (rede estadual)")
        ax.set_ylabel(ylabel)
        ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle(
        f"Gráfico {numero}: Inse médio da SRE e percentual de escolas estaduais por faixa de Ideb, MG, 2023-2025",
        fontsize=10.5, y=1.06,
    )
    fig.text(
        0.02, -0.14,
        "Nota: cada ponto é uma SRE (rede estadual, N=47); linha tracejada é a reta de regressão linear.\n"
        "Fonte: Inep/MEC (Ideb 2025) e Inep, Indicador de Nível Socioeconômico das Escolas de Educação Básica (Inse), edição 2023.",
        fontsize=9, color=TEXT_MUTED,
    )
    savefig(fig, f"grafico_{numero}")


# ---------------------------------------------------------------------------
# Gráfico 13 — Mediana do Ideb das escolas estaduais, ensino médio, por RGInt
# ---------------------------------------------------------------------------
def grafico_mediana_rgint(numero):
    sub = escolas[(escolas.REDE == "Estadual") & (escolas.ETAPA == "Ensino Médio") & escolas.IDEB.notna()]
    med = sub.groupby("RGINT")["IDEB"].median().sort_values()

    mg_ideb = serie_uf.loc[
        (serie_uf.ETAPA == "Ensino Médio") & (serie_uf.UF == "MG") & (serie_uf.REDE == "Estadual") & (serie_uf.ANO == 2025),
        "IDEB",
    ].iloc[0]

    fig, ax = plt.subplots(figsize=(8, 0.4 * len(med) + 1.8))
    ax.barh(med.index, med.values, color=BLUE, height=0.65)
    ax.bar_label(ax.containers[0], fmt="%.1f", fontsize=9, padding=3, color=TEXT_MUTED)
    ax.axvline(mg_ideb, color=TEXT_MUTED, linewidth=1.2, linestyle="--", zorder=0)
    ax.text(mg_ideb, len(med) - 0.4, f" MG: {mg_ideb:.1f}", color=TEXT_MUTED, fontsize=9, va="center")
    ax.set_xlabel("Ideb (mediana das escolas)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(
        f"Gráfico {numero}: Mediana do Ideb das escolas estaduais, ensino médio, por RGInt, MG, 2025",
        fontsize=10.5, y=1.03,
    )
    fig.text(
        0.02, -0.11,
        f"Nota: linha tracejada é o Ideb da rede estadual de MG no ensino médio ({mg_ideb:.1f}).\n"
        "Fonte: Inep/MEC, divulgação Ideb 2025 por escola.",
        fontsize=9, color=TEXT_MUTED,
    )
    savefig(fig, f"grafico_{numero}")


if __name__ == "__main__":
    grafico_1()
    grafico_evolucao("Anos Iniciais do Ensino Fundamental", 2, "Evolução do Ideb, anos iniciais, por rede, MG, 2005-2025")
    grafico_evolucao("Anos Finais do Ensino Fundamental", 3, "Evolução do Ideb, anos finais, por rede, MG, 2005-2025")
    grafico_evolucao("Ensino Médio", 4, "Evolução do Ideb, ensino médio, por rede, MG, 2005-2025")
    grafico_5()
    grafico_ranking_uf(6)
    grafico_faixas("Estadual", "Anos Iniciais do Ensino Fundamental", 7, "Percentual de escolas estaduais por faixa de Ideb, anos iniciais, MG, 2025")
    grafico_faixas("Estadual", "Anos Finais do Ensino Fundamental", 8, "Percentual de escolas estaduais por faixa de Ideb, anos finais, MG, 2025")
    grafico_faixas("Estadual", "Ensino Médio", 9, "Percentual de escolas estaduais por faixa de Ideb, ensino médio, MG, 2025")
    grafico_faixas("Municipal", "Anos Iniciais do Ensino Fundamental", 10, "Percentual de escolas municipais por faixa de Ideb, anos iniciais, MG, 2025")
    grafico_faixas("Municipal", "Anos Finais do Ensino Fundamental", 11, "Percentual de escolas municipais por faixa de Ideb, anos finais, MG, 2025")
    grafico_inse(12)
    grafico_mediana_rgint(13)
    print("OK")
