const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  BorderStyle, ShadingType, FootnoteReferenceRun, ImageRun,
} = require("docx");
const fs = require("fs");
const sizeOf = (p) => {
  // lê largura/altura do PNG direto do header (evita dependência externa)
  const buf = fs.readFileSync(p);
  const width = buf.readUInt32BE(16);
  const height = buf.readUInt32BE(20);
  return { width, height };
};

const RED = "C00000";
const GRAY = "595959";
const NOTE_BLUE = "1F4E79";
const NOTE_BLUE_BG = "EAF1F8";

function body(text, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 160, line: 288 },
    children: [new TextRun({ text, size: 21, ...opts })],
  });
}

function bodyMixed(runs) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 160, line: 288 },
    children: runs,
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 220, after: 120 },
    children: [new TextRun({ text, bold: true, color: RED, size: 24 })],
  });
}

function fonteNota(lines) {
  return lines.map(
    (l, i) =>
      new Paragraph({
        spacing: { after: i === lines.length - 1 ? 160 : 20 },
        children: [new TextRun({ text: l, size: 17, italics: true, color: GRAY })],
      })
  );
}

function nota(kind, ...lines) {
  const paras = [];
  paras.push(
    new Paragraph({
      spacing: { before: 120, after: 40 },
      border: { left: { style: BorderStyle.SINGLE, size: 24, color: NOTE_BLUE, space: 8 } },
      shading: { type: ShadingType.CLEAR, fill: NOTE_BLUE_BG },
      indent: { left: 200 },
      children: [new TextRun({ text: kind, bold: true, size: 19, color: NOTE_BLUE })],
    })
  );
  lines.forEach((l, idx) => {
    paras.push(
      new Paragraph({
        spacing: { after: idx === lines.length - 1 ? 200 : 60 },
        border: { left: { style: BorderStyle.SINGLE, size: 24, color: NOTE_BLUE, space: 8 } },
        shading: { type: ShadingType.CLEAR, fill: NOTE_BLUE_BG },
        indent: { left: 200 },
        alignment: AlignmentType.JUSTIFIED,
        children: [new TextRun({ text: l, size: 19, italics: true })],
      })
    );
  });
  return paras;
}

function imagem(path, maxWidthTw = 9000) {
  const { width, height } = sizeOf(path);
  const ratio = height / width;
  const w = maxWidthTw;
  const h = Math.round(w * ratio);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 80 },
    children: [
      new ImageRun({
        data: fs.readFileSync(path),
        transformation: { width: w / 15, height: h / 15 }, // twips->px aprox (96/1440*15)
        type: "png",
      }),
    ],
  });
}

function withFoot(text, footId) {
  return [new TextRun({ text, size: 21 }), new FootnoteReferenceRun(footId)];
}

const G = "analise/graficos";
const children = [];

children.push(
  new Paragraph({
    spacing: { after: 40 },
    children: [
      new TextRun({ text: "v. [?] n. [?] — agosto 2026", color: GRAY, size: 20 }),
      new TextRun({ text: "\tÁrea Temática: Educação", color: GRAY, size: 20 }),
    ],
    tabStops: [{ type: "right", position: 9350 }],
  })
);

children.push(
  new Paragraph({
    spacing: { before: 300, after: 300 },
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({
        text: "O desempenho da educação básica em Minas Gerais (Ideb) — resultados de 2025",
        bold: true,
        color: RED,
        size: 32,
      }),
    ],
  })
);

// Abertura
children.push(
  bodyMixed([
    ...withFoot(
      "O resultado do Índice de Desenvolvimento da Educação Básica (Ideb) de 2025 foi divulgado em agosto de 2026. Este informativo apresenta os principais resultados do índice para Minas Gerais considerando as diferentes etapas da educação básica (anos iniciais e finais do ensino fundamental e ensino médio) e as diferentes redes de ensino (municipal, estadual, privada e pública). Também apresenta os resultados para as superintendências regionais de ensino (SRE) do estado, coordenadorias regionais com a finalidade de supervisionar, orientar as diretrizes e políticas educacionais e de cooperar e articular com os municípios.",
      1
    ),
  ])
);
children.push(
  body(
    "Desde a última edição deste informativo, referente ao Ideb de 2019, o indicador já passou por três novos ciclos de divulgação — 2021, 2023 e 2025 —, o primeiro deles marcado pelo hiato letivo provocado pela pandemia de Covid-19. Este texto retoma a análise considerando esse período mais recente, com ênfase na comparação entre 2023 e 2025."
  )
);
children.push(
  bodyMixed([
    ...withFoot(
      "Principal indicador de acompanhamento da qualidade da educação básica, o Ideb é importante porque avalia duas dimensões fundamentais do funcionamento do sistema educacional: o desempenho dos alunos na aprendizagem (notas em provas de português e matemática) e o rendimento escolar (taxas de aprovação dos estudantes nas séries)",
      2
    ),
    new TextRun({ text: ". Assim, ele é composto por dois subíndices: a nota média padronizada das provas (indicador que varia de zero a dez) e o indicador de rendimento (que varia de zero a um).", size: 21 }),
  ])
);
children.push(
  body(
    "A melhoria no Ideb deve ser resultado do aumento desses dois subíndices, ou seja, tanto da melhora das taxas de aprovação quanto das notas dos alunos. Se a aprovação aumenta sem a contrapartida do aprendizado, a proficiência diminui, sem impacto positivo no Ideb. Já a melhora na proficiência decorrente da reprovação dos alunos com baixo aprendizado também não tem impacto no Ideb."
  )
);

children.push(h2("O desenvolvimento da educação em Minas Gerais"));
children.push(
  bodyMixed([
    ...withFoot(
      "O Gráfico 1 apresenta o Ideb de Minas Gerais de 2023 e 2025 para cada etapa de ensino e rede, com os valores de 2025 para o Brasil como base de comparação. Ela foi estabelecida tendo como referência o índice médio dos países membros da Organização para a Cooperação e Desenvolvimento Econômico (OCDE) em 2003, 6,0. Assim, o Compromisso Todos pela Educação de 2007 fixou como objetivo de longo prazo atingir um Ideb igual a 6,0 em 2021 na primeira etapa do ensino fundamental, em 2025, na segunda etapa e, em 2028, no ensino médio",
      3
    ),
    new TextRun({ text: ".", size: 21 }),
  ])
);
children.push(
  body(
    "2025 é justamente o ano-alvo dessa meta de longo prazo para os anos finais do ensino fundamental. Minas Gerais não a alcançou: registrou Ideb de 5,3 nessa etapa (tanto na rede estadual quanto na pública), abaixo dos 6,0 pretendidos — mas também abaixo da meta mais recente fixada pelo próprio Plano Estadual de Educação para o período (5,5), embora a distância tenha diminuído bastante frente a 2023. O Brasil como um todo também está distante desse patamar, com Ideb de 5,1 (rede estadual) na mesma etapa em 2025."
  )
);
children.push(imagem(`${G}/grafico_1.png`));
children.push(
  body(
    "De maneira geral, os dados de 2025 apontam para avanços em todas as etapas e redes, revertendo a estagnação observada na comparação anterior (2017-2019). Nos anos iniciais, o Ideb estadual passou de 6,2 para 6,7 entre 2023 e 2025; nos anos finais, de 4,6 para 5,3; e no ensino médio, de 4,0 para 4,5. Minas Gerais superou a média nacional em todas as etapas e redes comparáveis: 6,7 contra 6,4 nos anos iniciais (rede estadual), 5,3 contra 5,1 nos anos finais, e 4,5 contra 4,3 no ensino médio. À medida que se avança no processo de escolarização, o desempenho absoluto ainda cai — os anos finais e o ensino médio seguem com Ideb mais baixo que os anos iniciais —, mas o ritmo de melhora entre 2023 e 2025 foi mais forte justamente nessas duas etapas mais desafiadoras."
  )
);
children.push(
  body(
    "Desde 2005, quando a série histórica do Ideb foi iniciada, os anos iniciais tiveram o maior avanço, tendo alcançado a meta de longo prazo (6,0) ainda na década passada. O ciclo de 2021 marcou uma queda em todas as etapas, refletindo o impacto da pandemia de Covid-19 sobre a aprendizagem; em 2025, todas as três etapas atingiram os maiores valores da própria série histórica iniciada em 2005 (Gráfico 2)."
  )
);
children.push(...fonteNota([
  "Fonte: Inep/MEC, divulgação Ideb 2025 (por município e por UF).",
  "Nota: Rede pública: considera as escolas municipais, estaduais e federais. A rede municipal, quando aparece nos Gráficos 1 e 5, é uma aproximação pela média simples dos municípios de MG — ver observação no próprio gráfico.",
]));

children.push(h2("Anos iniciais do ensino fundamental"));
children.push(
  body(
    "Entre 2023 e 2025, o Ideb dos anos iniciais avançou em todas as redes de ensino em Minas Gerais: de 6,2 para 6,7 na rede estadual e de 6,1 para 6,4 na rede pública. É o maior valor de toda a série iniciada em 2005, superando inclusive o patamar pré-pandemia (6,5, em 2017 e 2019). A queda de 2021 — quando o Ideb estadual recuou para 6,0 — foi, portanto, temporária: a etapa não só recuperou como ultrapassou a trajetória que vinha antes da pandemia."
  )
);
children.push(imagem(`${G}/grafico_2.png`));
children.push(...fonteNota(["Fonte: Inep/MEC."]));

children.push(h2("Anos finais do ensino fundamental e ensino médio"));
children.push(imagem(`${G}/grafico_3.png`));
children.push(imagem(`${G}/grafico_4.png`));
children.push(
  body(
    "Os anos finais do ensino fundamental tiveram o avanço mais expressivo do ciclo: o Ideb estadual saltou de 4,6 (2023) para 5,3 (2025), o maior valor da série histórica — superando até o pico local de 2021 (5,0), atingido em condições atípicas de pandemia. A rede pública seguiu o mesmo padrão (de 4,7 para 5,3)."
  )
);
children.push(
  bodyMixed([
    new TextRun({
      text: "No ensino médio, o Ideb estadual passou de 4,0, patamar em que estava estabilizado desde 2019, para 4,5 em 2025 — também recorde da série histórica. Vale registrar que o período avaliado (2023–2025) coincide com a consolidação do Novo Ensino Médio nas redes estaduais, reforma curricular implementada a partir de 2022 cujos efeitos sobre a organização da etapa ainda estão em avaliação; não é possível, com os dados disponíveis, isolar sua contribuição específica para o resultado.",
      size: 21,
    }),
  ])
);
children.push(...fonteNota(["Fonte: Inep/MEC (ambos os gráficos)."]));

children.push(h2("Subíndices: rendimento × desempenho"));
children.push(
  body(
    "Como o Ideb sintetiza os resultados de rendimento e desempenho, é importante entender o comportamento dos seus subíndices. O Gráfico 5 mostra a variação do desempenho (nota média padronizada obtida pelo Saeb, de 0 a 10) e do rendimento (indicador de aprovação, de 0 a 1, aqui multiplicado por dez para ficar na mesma escala) entre 2023 e 2025."
  )
);
children.push(imagem(`${G}/grafico_5.png`));
children.push(
  body(
    "Nas redes pública e estadual, os dois subíndices subiram juntos nas três etapas — sinal de melhora \"genuína\", em que o avanço na aprovação veio acompanhado de aprendizagem maior, e não de uma aprovação mais frouxa. O padrão mais chamativo é o da rede privada: o rendimento subiu com força nas três etapas (o equivalente a 0,02 a 0,12 ponto de aprovação a mais), mas o desempenho no Saeb caiu nos anos iniciais e no ensino médio. Ou seja, a rede privada aprovou mais alunos sem que isso viesse acompanhado, em média, de mais aprendizagem — o inverso do movimento observado nas redes públicas."
  )
);
children.push(...fonteNota(["Fonte: Inep/MEC."]));

children.push(h2("E o desempenho da rede estadual?"));
children.push(
  body(
    "Na comparação da rede estadual de Minas Gerais com a dos demais estados do Brasil, o estado ocupa hoje a 6ª posição no ranking do Ideb de 2025 tanto nos anos iniciais (6,7) quanto nos anos finais (5,3) do ensino fundamental — a mesma posição de 2023 nos anos iniciais. No ensino médio, Minas subiu da 12ª para a 8ª posição (Ideb de 4,5)."
  )
);
children.push(
  body(
    "O avanço mais notável foi na rede pública dos anos finais do fundamental: Minas Gerais saltou da 16ª para a 4ª posição entre os estados, com alta de 0,6 ponto (de 4,7 para 5,3) — um dos maiores avanços do país nessa rede e etapa."
  )
);
children.push(...fonteNota(["Fonte: Inep/MEC, divulgação Ideb 2025 por UF (ranking calculado sobre as 27 unidades da federação)."]));

children.push(h2("Recorte regional — rede estadual"));
children.push(imagem(`${G}/grafico_6.png`, 8600));
children.push(imagem(`${G}/grafico_7.png`, 8600));
children.push(imagem(`${G}/grafico_8.png`, 8600));
children.push(
  body(
    "Nos anos iniciais, o quadro regional é bastante positivo: em 34 das SRE analisadas, mais de 90% das escolas estaduais têm Ideb igual ou acima de 6 — e em 12 delas, 100% das escolas atingem essa faixa. As SRE de Januária, Almenara e Carangola têm os menores percentuais nessa faixa (48% a 50%), ainda assim a maioria das escolas."
  )
);
children.push(
  body(
    "Avançando no ciclo escolar, o quadro nos anos finais é mais desafiador: apenas 13% das escolas estaduais do estado têm Ideb igual ou acima de 6, e a maior parte (56%) está na faixa intermediária, de 5 a 5,9. As SRE de Conselheiro Lafaiete (43%), Muriaé (32%) e Poços de Caldas (29%) têm os maiores percentuais de escolas na faixa mais alta; já Teófilo Otoni e Unaí não têm nenhuma escola estadual com Ideb acima de 6 nessa etapa, e Caratinga, Januária e Teófilo Otoni concentram os maiores percentuais de escolas abaixo de 4."
  )
);
children.push(
  body(
    "O ensino médio é a etapa com o cenário mais crítico: menos de 1% das escolas estaduais do estado atingem Ideb igual ou acima de 6, e 72% estão na faixa de 4 a 4,9. Januária (38%), Teófilo Otoni (33%) e Montes Claros (30%) concentram os maiores percentuais de escolas com Ideb abaixo de 4 nessa etapa."
  )
);
children.push(
  ...nota(
    "OBSERVAÇÃO METODOLÓGICA",
    "Nos Gráficos 6 a 8, SRE com menos de 3 escolas naquela rede/etapa foram omitidas para evitar percentuais de \"tudo ou nada\" sem significado (afetou Campo Belo, Curvelo, Itajubá, Metropolitana A e Pirapora, só nos anos iniciais). É um corte mais simples do que o critério de participação usado pelo Inep para divulgar resultado por escola (10 alunos presentes e 80% de participação), que não pôde ser aplicado aqui porque os arquivos de divulgação não trazem o número de alunos avaliados — apenas o Ideb já calculado.",
    "Ainda pendente: a SRE de Belo Horizonte aparece na base como \"Metropolitana\", separada de \"Metropolitana A/B/C\" — provavelmente uma pendência do cruzamento de município × SRE que vocês enviaram. Precisamos confirmar em qual das três sub-regionais Belo Horizonte deveria entrar antes de publicar esses gráficos."
  )
);
children.push(...fonteNota(["Fonte: Inep/MEC (Gráficos 6, 7 e 8)."]));

children.push(h2("Recorte regional — rede municipal"));
children.push(
  bodyMixed([
    new TextRun({
      text: "Nos anos iniciais do ensino fundamental, 67% das escolas municipais de Minas Gerais têm Ideb igual ou acima de 6 — proporção menor que a da rede estadual na mesma etapa (78%), mas ainda majoritária. Já nos anos finais, apenas 7% das escolas municipais atingem essa faixa, e 46% delas têm Ideb entre 4 e 4,9",
      size: 21,
    }),
    new FootnoteReferenceRun(4),
    new TextRun({ text: ".", size: 21 }),
  ])
);
children.push(imagem(`${G}/grafico_9.png`, 8600));
children.push(imagem(`${G}/grafico_10.png`, 8600));
children.push(...fonteNota(["Fonte: Inep/MEC (Gráficos 9 e 10)."]));

children.push(h2("Nível socioeconômico (Inse)"));
children.push(
  bodyMixed([
    new TextRun({
      text: "O desempenho das escolas por região deve ser analisado considerando-se que as condições socioeconômicas tendem a limitar o desempenho dos sistemas educacionais. Vários estudos mostram que o contexto socioeconômico das escolas é um fator importante para os resultados educacionais",
      size: 21,
    }),
    new FootnoteReferenceRun(5),
    new TextRun({ text: ". Assim, regiões com melhor poder aquisitivo dos seus alunos tendem a ter um Ideb mais alto.", size: 21 }),
  ])
);
children.push(
  ...nota(
    "PENDENTE",
    "Ainda não recebemos uma base de Inse (2023) para cruzar com os resultados por SRE/RGInt. Esta seção fica de fora até chegar esse dado — o parágrafo interpretativo (regiões de menor Inse com pior Ideb, como em 2020) e o recálculo do coeficiente de correlação dependem dele."
  )
);

children.push(h2("O que os dados do Ideb informam"));
children.push(
  body(
    "Os resultados de 2025 marcam uma inflexão positiva na trajetória do Ideb em Minas Gerais: depois do recuo generalizado provocado pela pandemia em 2021, as três etapas da educação básica não só recuperaram como superaram seus melhores patamares históricos, com melhora simultânea de aprovação e aprendizagem nas redes pública e estadual — o caminho mais sólido para o avanço do indicador. O estado também melhorou sua posição relativa no país, com destaque para o salto da rede estadual nos anos finais do fundamental, da 16ª para a 4ª colocação nacional."
  )
);
children.push(
  body(
    "Ainda assim, o desafio de sustentar a qualidade ao longo da trajetória escolar permanece: o Ideb cai a cada etapa, e o recorte por SRE mostra desigualdades regionais persistentes, mais amplas justamente nas etapas mais avançadas — no ensino médio, praticamente nenhuma escola estadual do estado atinge a marca de 6, e regionais como Januária e Teófilo Otoni concentram os piores resultados em quase todas as etapas e redes analisadas."
  )
);
children.push(
  bodyMixed([
    new TextRun({
      text: "Cabe registrar, por fim, que o Ideb, como todo indicador sintético, tem limites. Ao combinar rendimento e desempenho em um único número, ele pode mascarar estratégias de melhoria que não se traduzem em aprendizagem efetiva — como o próprio recorte por rede sugere ter ocorrido na rede privada em 2025, onde a aprovação subiu mais que o aprendizado",
      size: 21,
    }),
    new FootnoteReferenceRun(6),
    new TextRun({
      text: ". Isso não invalida seu uso como referência de acompanhamento, mas recomenda cautela na leitura de variações pontuais e reforça a importância de olhar os subíndices — e não apenas o resultado final — na análise de política educacional.",
      size: 21,
    }),
  ])
);

children.push(h2("Notas de rodapé e referências"));
children.push(
  ...nota(
    "AJUSTE",
    "Lista abaixo mantém a maioria das referências de 2020, acrescida da Nota Informativa do Ideb 2025 (Inep). Falta reconferir se os links do Inep ainda resolvem antes de publicar."
  )
);

children.push(h2("Expediente"));
children.push(body("Mantido como em 2020 (Presidência, diretorias, Assessoria de Comunicação Social)."));
children.push(
  ...nota("AJUSTE", "Confirmar se a equipe da Coordenação de Pesquisas em Políticas Públicas — elaboração e revisão — mudou desde 2020, antes de publicar os nomes.")
);

const footnotes = {
  1: { children: [new Paragraph({ children: [new TextRun({ text: "Fernandes, R. Índice de Desenvolvimento da Educação Básica (Ideb). Textos para discussão, n.26, Brasília: Inep, 2007.", size: 18 })] })] },
  2: { children: [new Paragraph({ children: [new TextRun({ text: "Nota Técnica do Inep sobre a metodologia de cálculo do Ideb.", size: 18 })] })] },
  3: { children: [new Paragraph({ children: [new TextRun({ text: "Compromisso Todos pela Educação, Decreto nº 6.094/2007; Nota Técnica do Inep sobre metas intermediárias.", size: 18 })] })] },
  4: { children: [new Paragraph({ children: [new TextRun({ text: "Ensino médio não é analisado na rede municipal por ter poucas escolas municipais ofertantes dessa etapa.", size: 18 })] })] },
  5: { children: [new Paragraph({ children: [new TextRun({ text: "Soares & Pereira Xavier, 2013; Figueiredo et al., 2018; Souza, Costa & Riani, 2019.", size: 18 })] })] },
  6: { children: [new Paragraph({ children: [new TextRun({ text: "Figueiredo, D., Carmo, E., Maia, R. e Silva, L. Os cavalos também caem: tratado das inconsistências do Ideb. Ensaio: avaliação e políticas públicas em educação, v.26, n.100, 2018.", size: 18 })] })] },
};

const doc = new Document({
  footnotes,
  styles: { default: { document: { run: { font: "Calibri", size: 21 } } } },
  sections: [
    {
      properties: {
        page: { size: { width: 11906, height: 16838 }, margin: { top: 1000, bottom: 1000, left: 1100, right: 1100 } },
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("2025/rascunho_informativo_ideb_2025.docx", buf);
  console.log("OK", buf.length, "bytes");
});
