# Gráfico 14 — Mapa de MG: mediana do Ideb (ensino médio, rede estadual) por
# RGInt, com grid de municípios e hachura nos municípios abaixo da mediana da
# sua RGInt.
#
# Este script é autocontido: os dados de entrada são lidos diretamente do
# GitHub (raw.githubusercontent.com), então não é preciso clonar o repositório
# nem rodar a partir de uma pasta específica — só baixar este arquivo .R e
# rodar. Se quiser usar dados locais mais recentes em vez do que está no
# GitHub, troque as 3 linhas `read_csv(RAW_BASE, ...)` /
# `readLines(RAW_BASE, ...)` abaixo por caminhos locais
# (analise/mapa_rgint/...).
#
# Como rodar:
#   1. install.packages(c("geobr", "sf", "ggplot2", "dplyr", "readr", "ggpattern"))
#      (ggpattern é opcional — sem ele o script cai num fallback com contorno
#      tracejado no lugar da hachura de fato)
#   2. Rscript gerar_mapa_rgint.R  (ou "Source" no RStudio)
#
# Saída: grafico_14.png, salvo na pasta de trabalho atual do R (getwd()).
#
# geobr baixa a malha municipal do IBGE/IPEA na primeira execução (precisa de
# internet); em execuções seguintes ele usa o cache local.

library(geobr)
library(sf)
library(ggplot2)
library(dplyr)
library(readr)

RAW_BASE <- "https://raw.githubusercontent.com/marielgruppi/informativoideb/claude/ideb-2025-informativo-g86l9l/analise/mapa_rgint/"

rgint_med <- read_csv(paste0(RAW_BASE, "mediana_rgint.csv"), show_col_types = FALSE)
mun_med   <- read_csv(paste0(RAW_BASE, "mediana_municipio.csv"), show_col_types = FALSE)
mg_ideb   <- as.numeric(readLines(paste0(RAW_BASE, "mg_ideb.txt")))

# Malha dos municípios de MG (código UF 31)
mun_sf <- read_municipality(code_muni = "MG", year = 2020, simplified = TRUE)

mun_sf <- mun_sf %>%
  mutate(code_muni = as.numeric(code_muni)) %>%
  left_join(mun_med, by = c("code_muni" = "CO_MUNICIPIO"))

abaixo <- filter(mun_sf, ABAIXO_MEDIANA_RGINT == TRUE)

titulo <- "Gráfico 14: Mediana do Ideb por RGInt e municípios abaixo da mediana da própria RGInt, ensino médio, rede estadual, MG, 2025"
subtitulo <- paste0(
  "Hachurado: município com Ideb (mediana das escolas) abaixo da mediana da sua RGInt  |  Ideb mediano de MG: ",
  format(mg_ideb, decimal.mark = ",")
)

tema <- theme_void(base_size = 11) +
  theme(
    plot.title = element_text(size = 11, hjust = 0.5),
    plot.subtitle = element_text(size = 9, hjust = 0.5, color = "grey35"),
    legend.position = "right"
  )

# Grid dos municípios: contorno branco fino sobre todo o mapa (geom_sf base,
# em ambos os ramos abaixo) — dá o efeito de grade municipal por cima do
# preenchimento por RGInt.

if (requireNamespace("ggpattern", quietly = TRUE)) {
  library(ggpattern)
  mapa <- ggplot(mun_sf) +
    geom_sf(aes(fill = IDEB_MEDIANA_RGINT), color = "white", linewidth = 0.08) +
    geom_sf_pattern(
      data = abaixo,
      aes(fill = IDEB_MEDIANA_RGINT),
      pattern = "stripe", pattern_fill = "white", pattern_colour = "white",
      pattern_density = 0.15, pattern_spacing = 0.01, pattern_angle = 45,
      color = "white", linewidth = 0.08
    ) +
    scale_fill_gradient(low = "#cfe3f7", high = "#1a4d8f", na.value = "grey85",
                         name = "Mediana do Ideb\n(RGInt, EM estadual)") +
    tema +
    labs(title = titulo, subtitle = subtitulo)
} else {
  message("Pacote 'ggpattern' não encontrado — usando contorno tracejado como ",
          "fallback para marcar os municípios abaixo da mediana da RGInt. ",
          "Rode install.packages('ggpattern') e execute de novo para a hachura de fato.")
  mapa <- ggplot(mun_sf) +
    geom_sf(aes(fill = IDEB_MEDIANA_RGINT), color = "white", linewidth = 0.08) +
    geom_sf(data = abaixo, fill = NA, color = "#c0392b", linewidth = 0.35, linetype = "22") +
    scale_fill_gradient(low = "#cfe3f7", high = "#1a4d8f", na.value = "grey85",
                         name = "Mediana do Ideb\n(RGInt, EM estadual)") +
    tema +
    labs(title = titulo,
         subtitle = sub("Hachurado", "Contorno tracejado", subtitulo))
}

ggsave("analise/graficos/grafico_14.png", mapa, width = 9, height = 8, dpi = 200, bg = "white")
message("Salvo: analise/graficos/grafico_14.png")
