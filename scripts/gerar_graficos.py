"""Gera as imagens dos Gráficos 1 a 10 do informativo Ideb-MG 2025 a partir de
analise/indicadores_ideb_mg.xlsx. Saída: analise/graficos/grafico_N.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
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
            ax.bar_label(bars, fmt="%.1f", fontsize=7, padding=1, color=TEXT_MUTED)
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
    fig.text(0.02, -0.11, "Barras hachuradas (rede Municipal): o Inep não publica agregado estadual dessa rede nesta tabela.\nO valor foi aproximado pela média simples dos municípios de MG.", fontsize=9, color=TEXT_MUTED)
    savefig(fig, "grafico_1")


# ---------------------------------------------------------------------------
# Gráficos 2, 3, 4 — evolução histórica por rede, MG (nível UF), 2005/2007–2025
# ---------------------------------------------------------------------------
def rotula_extremos(ax, sub, cores, prioridade):
    """Rotula só o pico e o vale de cada série (nunca todo ponto), pulando
    rótulos que ficariam colados em outro já colocado."""
    x0, x1 = min(sub.ANO), max(sub.ANO)
    y0, y1 = ax.get_ylim()
    colocados = []  # (x_norm, y_norm)

    def perto_demais(xn, yn):
        return any(((xn - px) ** 2 + (yn - py) ** 2) ** 0.5 < 0.09 for px, py in colocados)

    for rede in prioridade:
        if rede not in cores:
            continue
        s = sub[sub.REDE == rede].sort_values("ANO")
        if len(s) < 2 or s.IDEB.max() == s.IDEB.min():
            continue
        cor = cores[rede]
        i_max = s.IDEB.idxmax()
        i_min = s.IDEB.idxmin()
        for i, tipo in ((i_max, "pico"), (i_min, "vale")):
            ano, val = s.loc[i, "ANO"], s.loc[i, "IDEB"]
            xn, yn = (ano - x0) / (x1 - x0 or 1), (val - y0) / (y1 - y0 or 1)
            if perto_demais(xn, yn):
                continue
            colocados.append((xn, yn))
            offset = 9 if tipo == "pico" else -11
            va = "bottom" if tipo == "pico" else "top"
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
    ax.legend(frameon=False, loc="upper left")
    anos_com_dado = sorted(sub.ANO.unique())
    ax.xaxis.set_major_locator(mticker.FixedLocator(anos_com_dado))
    ax.set_xticklabels([str(int(a)) for a in anos_com_dado], rotation=45, ha="right")
    ax.set_xlim(min(anos_com_dado) - 0.5, max(anos_com_dado) + 0.5)
    ymin, ymax = ax.get_ylim()
    pad = (ymax - ymin) * 0.12
    ax.set_ylim(ymin - pad, ymax + pad)
    rotula_extremos(ax, sub, cores, ["Estadual", "Pública", "Privada", "Municipal"])
    fig.suptitle(f"Gráfico {numero}: {titulo}", fontsize=11)
    if "Municipal" in sub.REDE.unique():
        fig.text(0.02, -0.16, "Linha tracejada (Municipal): aproximação pela média simples dos municípios de MG.\nO Inep não publica agregado estadual dessa rede nesta tabela.", fontsize=9, color=TEXT_MUTED)
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
            var_n.append(s.loc[2025, "N"] - s.loc[2023, "N"])
            var_p.append((s.loc[2025, "P"] - s.loc[2023, "P"]) * 10)  # P vai de 0-1; escala x10 p/ comparar com N (0-10)
        x = range(len(redes))
        w = 0.33
        b1 = ax.bar([i - w / 2 for i in x], var_n, width=w, color=BLUE, label="Δ Desempenho (N)")
        b2 = ax.bar([i + w / 2 for i in x], var_p, width=w, color=ORANGE, label="Δ Rendimento (P×10)")
        ax.bar_label(b1, fmt="%.2f", fontsize=7, padding=1, color=TEXT_MUTED)
        ax.bar_label(b2, fmt="%.2f", fontsize=7, padding=1, color=TEXT_MUTED)
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
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.08))
    fig.suptitle("Gráfico 5: Variação de desempenho (Saeb) e rendimento por rede, MG, 2023-2025", y=1.16, fontsize=11)
    savefig(fig, "grafico_5")


# ---------------------------------------------------------------------------
# Gráficos 6-8 (estadual) e 9-10 (municipal) — % de escolas por faixa de Ideb, por SRE
# ---------------------------------------------------------------------------
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
    ax.set_xlabel("% de escolas")
    ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Gráfico {numero}: {titulo}", fontsize=10.5, y=1 - 0.28 / fig_h)
    ax.legend(
        title="Faixa de Ideb", frameon=False, ncol=4, loc="upper center",
        bbox_to_anchor=(0.5, 1 - 0.55 / fig_h), bbox_transform=fig.transFigure,
    )
    fig.text(0.02, -0.5 / fig_h, f"SRE com menos de {min_escolas} escolas nessa rede/etapa foram omitidas.", fontsize=9, color=TEXT_MUTED)
    savefig(fig, f"grafico_{numero}")


if __name__ == "__main__":
    grafico_1()
    grafico_evolucao("Anos Iniciais do Ensino Fundamental", 2, "Evolução do Ideb, anos iniciais, por rede, MG, 2005-2025")
    grafico_evolucao("Anos Finais do Ensino Fundamental", 3, "Evolução do Ideb, anos finais, por rede, MG, 2005-2025")
    grafico_evolucao("Ensino Médio", 4, "Evolução do Ideb, ensino médio, por rede, MG, 2005-2025")
    grafico_5()
    grafico_faixas("Estadual", "Anos Iniciais do Ensino Fundamental", 6, "% de escolas estaduais por faixa de Ideb, anos iniciais, MG, 2025")
    grafico_faixas("Estadual", "Anos Finais do Ensino Fundamental", 7, "% de escolas estaduais por faixa de Ideb, anos finais, MG, 2025")
    grafico_faixas("Estadual", "Ensino Médio", 8, "% de escolas estaduais por faixa de Ideb, ensino médio, MG, 2025")
    grafico_faixas("Municipal", "Anos Iniciais do Ensino Fundamental", 9, "% de escolas municipais por faixa de Ideb, anos iniciais, MG, 2025")
    grafico_faixas("Municipal", "Anos Finais do Ensino Fundamental", 10, "% de escolas municipais por faixa de Ideb, anos finais, MG, 2025")
    print("OK")
