## ---------------------------------------------------------------------------
## Gera os Gráficos 1 a 10 do informativo Ideb-MG 2025 a partir de
## analise/indicadores_ideb_mg.xlsx (gerado por scripts/build_indicadores.py).
##
## Este script NÃO refaz o cruzamento dos microdados do Inep (isso já está
## feito na planilha de indicadores) — ele só lê as abas já processadas e
## gera as figuras, espelhando exatamente scripts/gerar_graficos.py (Python).
##
## Pacotes necessários (rode uma vez, se não tiver):
##   install.packages(c("readxl", "dplyr", "tidyr", "ggplot2", "stringr", "forcats", "scales"))
## ---------------------------------------------------------------------------

library(readxl)
library(dplyr)
library(tidyr)
library(ggplot2)
library(stringr)
library(forcats)
library(scales)

IN_XLSX <- "analise/indicadores_ideb_mg.xlsx"
OUT_DIR <- "analise/graficos_R"   # pasta separada, para não sobrescrever os PNGs oficiais gerados em Python
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

## Paleta categórica validada (skill dataviz) — ordem fixa por série.
BLUE   <- "#2a78d6"  # MG 2023 / Estadual
ORANGE <- "#eb6834"  # MG 2025 / Municipal
AQUA   <- "#1baf7a"  # Brasil 2025 / Pública
YELLOW <- "#eda100"  # Privada
GRID       <- "#d9d8d3"
TEXT_COL   <- "#0b0b0b"
TEXT_MUTED <- "#52514e"

FAIXA_ORDEM <- c("< 4", "4 a 4,9", "5 a 5,9", ">= 6")
FAIXA_CORES <- c("< 4" = "#e34948", "4 a 4,9" = YELLOW, "5 a 5,9" = "#8fd0ba", ">= 6" = AQUA)

ETAPAS <- c(
  "Anos Iniciais do Ensino Fundamental",
  "Anos Finais do Ensino Fundamental",
  "Ensino Médio"
)
ETAPA_ABREV <- c(
  "Anos Iniciais do Ensino Fundamental" = "Anos iniciais",
  "Anos Finais do Ensino Fundamental"   = "Anos finais",
  "Ensino Médio"                        = "Ensino médio"
)
REDES_ORDEM <- c("Estadual", "Municipal", "Privada", "Pública")

tema_base <- theme_minimal(base_size = 13) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = GRID, linewidth = 0.4),
    axis.line.x = element_line(color = GRID),
    axis.title = element_text(color = TEXT_COL),
    axis.text = element_text(color = TEXT_MUTED),
    plot.title = element_text(hjust = 0, size = 13),
    plot.caption = element_text(hjust = 0, size = 9.5, color = TEXT_MUTED, margin = margin(t = 10)),
    strip.text = element_text(hjust = 0, size = 11, color = TEXT_COL),
    legend.title = element_text(size = 10),
    legend.position = "top",
    plot.background = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

## ---------------------------------------------------------------------------
## Leitura das abas já processadas
## ---------------------------------------------------------------------------
serie_uf  <- read_excel(IN_XLSX, sheet = "Serie_UF_Regiao")
serie_mun <- read_excel(IN_XLSX, sheet = "Serie_Municipios_MG")
escolas   <- read_excel(IN_XLSX, sheet = "Escolas_2025_MG")

## O Inep não publica, na tabela de UF/Região, um agregado estadual da rede
## municipal (só Estadual, Privada, Pública e Total). Para poder mostrar a
## rede municipal nos Gráficos 1, 2, 3 e 5, usamos a média simples dos
## municípios de MG como aproximação (mesmo critério do script em Python).
## Ensino Médio fica de fora porque tem poucas escolas municipais ofertantes.
municipal_approx <- serie_mun %>%
  filter(REDE == "Municipal", ETAPA != "Ensino Médio") %>%
  group_by(ETAPA, ANO) %>%
  summarise(IDEB = mean(IDEB, na.rm = TRUE),
            N = mean(N, na.rm = TRUE),
            P = mean(P, na.rm = TRUE),
            .groups = "drop") %>%
  mutate(REDE = "Municipal", UF = "MG", NOME = "Minas Gerais", REGIAO = NA_character_)

serie_uf <- bind_rows(serie_uf, municipal_approx)

salvar <- function(p, nome, largura = 9, altura = 5) {
  caminho <- file.path(OUT_DIR, paste0(nome, ".png"))
  ggsave(caminho, p, width = largura, height = altura, dpi = 200, bg = "white")
  message("salvo: ", caminho)
}

## ---------------------------------------------------------------------------
## Gráfico 1: Ideb por rede de ensino, Brasil 2025 e Minas Gerais, 2023-2025
## ---------------------------------------------------------------------------
grafico_1 <- function() {
  sub <- serie_uf %>%
    filter(ETAPA %in% ETAPAS, ANO %in% c(2023, 2025))

  mg <- sub %>% filter(UF == "MG") %>%
    transmute(ETAPA, REDE, ANO, IDEB, SERIE = paste0("MG ", ANO))
  br <- sub %>% filter(NOME == "Brasil", ANO == 2025) %>%
    transmute(ETAPA, REDE, ANO, IDEB, SERIE = "Brasil 2025")

  dados <- bind_rows(mg, br) %>%
    mutate(
      ETAPA = factor(ETAPA, levels = ETAPAS, labels = ETAPA_ABREV[ETAPAS]),
      REDE = factor(REDE, levels = REDES_ORDEM),
      SERIE = factor(SERIE, levels = c("MG 2023", "MG 2025", "Brasil 2025")),
      aprox = REDE == "Municipal"
    ) %>%
    filter(!is.na(REDE))

  p <- ggplot(dados, aes(x = REDE, y = IDEB, fill = SERIE, alpha = aprox)) +
    geom_col(position = position_dodge(width = 0.75), width = 0.7, color = "white", linewidth = 0.3) +
    geom_text(aes(label = number(IDEB, accuracy = 0.1)),
              position = position_dodge(width = 0.75), vjust = -0.4, size = 3, color = TEXT_MUTED) +
    facet_wrap(~ETAPA, scales = "free_x") +
    scale_fill_manual(values = c("MG 2023" = BLUE, "MG 2025" = ORANGE, "Brasil 2025" = AQUA)) +
    scale_alpha_manual(values = c(`TRUE` = 0.55, `FALSE` = 1), guide = "none") +
    scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +
    labs(
      title = "Gráfico 1: Ideb por rede de ensino, Brasil 2025 e Minas Gerais, 2023-2025",
      x = NULL, y = "Ideb", fill = NULL,
      caption = paste0(
        "Barras mais claras (rede Municipal): o Inep não publica agregado estadual dessa rede nesta tabela.\n",
        "O valor foi aproximado pela média simples dos municípios de MG.\n",
        "Fonte: Inep/MEC, divulgação Ideb 2025 (por município e por UF)."
      )
    ) +
    tema_base

  salvar(p, "grafico_1", largura = 11, altura = 4.5)
}

## ---------------------------------------------------------------------------
## Gráficos 2, 3, 4: evolução histórica por rede, MG (nível UF), 2005/2007-2025
## ---------------------------------------------------------------------------

## Rotula só o pico e o vale de cada série (nunca todo ponto), pulando
## rótulos que ficariam colados em outro já colocado — mesma lógica do
## script em Python (scripts/gerar_graficos.py::rotula_extremos).
rotula_extremos <- function(sub, cores, prioridade, x_range, y_range) {
  colocados <- list()
  perto_demais <- function(xn, yn) {
    if (length(colocados) == 0) return(FALSE)
    any(sapply(colocados, function(pt) sqrt((xn - pt[1])^2 + (yn - pt[2])^2) < 0.09))
  }
  labels <- list()
  for (rede in prioridade) {
    if (!(rede %in% names(cores))) next
    s <- sub %>% filter(REDE == rede) %>% arrange(ANO)
    if (nrow(s) < 2 || max(s$IDEB) == min(s$IDEB)) next
    i_max <- which.max(s$IDEB)
    i_min <- which.min(s$IDEB)
    for (info in list(list(i = i_max, tipo = "pico"), list(i = i_min, tipo = "vale"))) {
      ano <- s$ANO[info$i]; val <- s$IDEB[info$i]
      xn <- (ano - x_range[1]) / diff(x_range)
      yn <- (val - y_range[1]) / diff(y_range)
      if (perto_demais(xn, yn)) next
      colocados[[length(colocados) + 1]] <- c(xn, yn)
      labels[[length(labels) + 1]] <- data.frame(
        ANO = ano, IDEB = val, REDE = rede, tipo = info$tipo, cor = cores[[rede]]
      )
    }
  }
  if (length(labels) == 0) return(data.frame(ANO = numeric(0), IDEB = numeric(0), REDE = character(0), tipo = character(0), cor = character(0)))
  bind_rows(labels)
}

grafico_evolucao <- function(etapa, numero, titulo) {
  cores <- c(Estadual = BLUE, Municipal = ORANGE, Privada = YELLOW, "Pública" = AQUA)
  sub <- serie_uf %>% filter(ETAPA == etapa, UF == "MG", REDE %in% names(cores))
  anos_com_dado <- sort(unique(sub$ANO))
  x_range <- range(anos_com_dado)
  y_range <- range(sub$IDEB, na.rm = TRUE)
  pad <- diff(y_range) * 0.12
  y_range_pad <- c(y_range[1] - pad, y_range[2] + pad)

  rot <- rotula_extremos(sub, cores, c("Estadual", "Pública", "Privada", "Municipal"), x_range, y_range_pad)

  tem_municipal <- "Municipal" %in% sub$REDE
  legenda_dash <- if (tem_municipal) {
    paste0(
      "Linha tracejada (Municipal): aproximação pela média simples dos municípios de MG.\n",
      "O Inep não publica agregado estadual dessa rede nesta tabela.\nFonte: Inep/MEC."
    )
  } else "Fonte: Inep/MEC."

  p <- ggplot(sub, aes(x = ANO, y = IDEB, color = REDE, linetype = REDE)) +
    { if (!is.null(sub$ANO[sub$ANO == 2021]) && any(sub$ANO == 2021))
        annotate("rect", xmin = 2020.6, xmax = 2021.4, ymin = -Inf, ymax = Inf, fill = GRID, alpha = 0.5) } +
    geom_line(linewidth = 1) +
    geom_point(size = 2) +
    { if (nrow(rot) > 0)
        geom_text(data = rot, aes(x = ANO, y = IDEB, label = number(IDEB, accuracy = 0.1), color = REDE),
                   vjust = ifelse(rot$tipo == "pico", -0.8, 1.8), fontface = "bold", size = 3.3,
                   show.legend = FALSE) } +
    { if (any(sub$ANO == 2021))
        annotate("text", x = 2021, y = y_range_pad[1], label = "2021\nciclo pós-pandemia",
                 hjust = 0.5, vjust = -0.1, size = 3.1, color = TEXT_MUTED) } +
    scale_color_manual(values = cores, breaks = REDES_ORDEM) +
    scale_linetype_manual(values = c(Estadual = "solid", Municipal = "22", Privada = "solid", "Pública" = "solid"),
                           breaks = REDES_ORDEM, guide = "none") +
    scale_x_continuous(breaks = anos_com_dado) +
    coord_cartesian(ylim = y_range_pad) +
    labs(title = paste0("Gráfico ", numero, ": ", titulo), x = NULL, y = "Ideb", color = NULL,
         caption = legenda_dash) +
    tema_base +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))

  salvar(p, paste0("grafico_", numero), largura = 8.5, altura = 5)
}

## ---------------------------------------------------------------------------
## Gráfico 5: variação de desempenho (N) e rendimento (P), 2023 -> 2025, por rede
## ---------------------------------------------------------------------------
grafico_5 <- function() {
  sub <- serie_uf %>%
    filter(ETAPA %in% ETAPAS, UF == "MG", ANO %in% c(2023, 2025))

  variacao <- sub %>%
    select(ETAPA, REDE, ANO, N, P) %>%
    pivot_wider(names_from = ANO, values_from = c(N, P), names_sep = "_") %>%
    mutate(
      var_N = N_2025 - N_2023,
      var_P = (P_2025 - P_2023) * 10  # P vai de 0-1; escala x10 p/ comparar com N (0-10)
    ) %>%
    select(ETAPA, REDE, var_N, var_P) %>%
    pivot_longer(cols = c(var_N, var_P), names_to = "indicador", values_to = "valor") %>%
    mutate(
      indicador = recode(indicador, var_N = "Δ Desempenho (N)", var_P = "Δ Rendimento (P×10)"),
      ETAPA = factor(ETAPA, levels = ETAPAS, labels = ETAPA_ABREV[ETAPAS]),
      REDE = factor(REDE, levels = REDES_ORDEM),
      aprox = REDE == "Municipal"
    ) %>%
    filter(!is.na(REDE))

  p <- ggplot(variacao, aes(x = REDE, y = valor, fill = indicador, alpha = aprox)) +
    geom_col(position = position_dodge(width = 0.7), width = 0.6, color = "white", linewidth = 0.3) +
    geom_hline(yintercept = 0, color = TEXT_MUTED, linewidth = 0.4) +
    geom_text(aes(label = number(valor, accuracy = 0.01)),
              position = position_dodge(width = 0.7),
              vjust = ifelse(variacao$valor >= 0, -0.4, 1.2), size = 3, color = TEXT_MUTED) +
    facet_wrap(~ETAPA, scales = "free_x") +
    scale_fill_manual(values = c("Δ Desempenho (N)" = BLUE, "Δ Rendimento (P×10)" = ORANGE)) +
    scale_alpha_manual(values = c(`TRUE` = 0.55, `FALSE` = 1), guide = "none") +
    labs(
      title = "Gráfico 5: Variação de desempenho (Saeb) e rendimento por rede, MG, 2023-2025",
      x = NULL, y = NULL, fill = NULL,
      caption = "Barras mais claras (rede Municipal): aproximação pela média simples dos municípios de MG.\nFonte: Inep/MEC."
    ) +
    tema_base

  salvar(p, "grafico_5", largura = 11, altura = 4.5)
}

## ---------------------------------------------------------------------------
## Gráficos 6-8 (estadual) e 9-10 (municipal): % de escolas por faixa de Ideb,
## por SRE
## ---------------------------------------------------------------------------
grafico_faixas <- function(rede, etapa, numero, titulo, min_escolas = 3) {
  sub <- escolas %>% filter(REDE == rede, ETAPA == etapa, !is.na(FAIXA))

  contagem <- sub %>% count(SRE, name = "n_escolas")
  sres_validas <- contagem %>% filter(n_escolas >= min_escolas) %>% pull(SRE)

  pct <- sub %>%
    filter(SRE %in% sres_validas) %>%
    count(SRE, FAIXA) %>%
    group_by(SRE) %>%
    mutate(pct = n / sum(n) * 100) %>%
    ungroup() %>%
    complete(SRE, FAIXA = FAIXA_ORDEM, fill = list(n = 0, pct = 0))

  ordem_sre <- pct %>% filter(FAIXA == ">= 6") %>% arrange(pct) %>% pull(SRE)
  pct <- pct %>% mutate(SRE = factor(SRE, levels = ordem_sre), FAIXA = factor(FAIXA, levels = FAIXA_ORDEM))

  n_sre <- length(ordem_sre)
  altura <- max(4, 0.22 * n_sre) + 1.4

  p <- ggplot(pct, aes(x = pct, y = SRE, fill = FAIXA)) +
    geom_col(width = 0.7) +
    scale_fill_manual(values = FAIXA_CORES, name = "Faixa de Ideb") +
    scale_x_continuous(expand = c(0, 0)) +
    coord_cartesian(xlim = c(0, 100)) +
    labs(
      title = paste0("Gráfico ", numero, ": ", titulo),
      x = "% de escolas", y = NULL,
      caption = paste0("SRE com menos de ", min_escolas, " escolas nessa rede/etapa foram omitidas.\nFonte: Inep/MEC.")
    ) +
    tema_base +
    theme(legend.position = "top")

  salvar(p, paste0("grafico_", numero), largura = 8.5, altura = altura)
}

## ---------------------------------------------------------------------------
## Roda tudo
## ---------------------------------------------------------------------------
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

message("OK — 10 gráficos salvos em ", OUT_DIR)
