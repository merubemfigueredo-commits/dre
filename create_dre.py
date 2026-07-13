import streamlit as st
from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Helpers ──────────────────────────────────────────────────────────────────

def fmt_brl(value: float) -> str:
    """Formata número como moeda brasileira."""
    if value < 0:
        return f"({abs(value):,.2f})".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num_input(label: str, key: str, help_text: str = "") -> float:
    """Campo numérico com validação."""
    val = st.number_input(
        label,
        min_value=0.0,
        value=0.0,
        step=0.01,
        format="%.2f",
        key=key,
        help=help_text or None,
    )
    return float(val)


# ── PDF ───────────────────────────────────────────────────────────────────────

def gerar_pdf(dados: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "titulo",
        parent=styles["Normal"],
        fontSize=14,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitulo_style = ParagraphStyle(
        "subtitulo",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    rodape_style = ParagraphStyle(
        "rodape",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica",
        alignment=TA_CENTER,
        textColor=colors.grey,
    )

    story = []

    # Cabeçalho
    story.append(Paragraph("DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO (DRE)", titulo_style))
    story.append(Paragraph(f"<b>{dados['empresa']}</b>", subtitulo_style))
    if dados["cnpj"]:
        story.append(Paragraph(f"CNPJ: {dados['cnpj']}", subtitulo_style))
    story.append(Paragraph(f"Período: {dados['periodo']}", subtitulo_style))
    if dados["responsavel"]:
        story.append(Paragraph(f"Responsável: {dados['responsavel']}", subtitulo_style))
    story.append(Spacer(1, 0.5 * cm))

    # Cores
    COR_HEADER   = colors.HexColor("#1a3a5c")
    COR_SUBTOTAL = colors.HexColor("#d0e4f7")
    COR_TOTAL    = colors.HexColor("#1a3a5c")
    COR_LINHA_PAR = colors.HexColor("#f7f9fc")
    COR_BRANCO   = colors.white

    largura_total = A4[0] - 3 * cm
    col_desc = largura_total * 0.65
    col_val  = largura_total * 0.35

    linhas = []

    def add_header(texto):
        linhas.append(("HEADER", texto))

    def add_item(texto, valor, negativo=False):
        linhas.append(("ITEM", texto, valor, negativo))

    def add_subtotal(texto, valor):
        linhas.append(("SUBTOTAL", texto, valor))

    def add_total(texto, valor):
        linhas.append(("TOTAL", texto, valor))

    def add_spacer_row():
        linhas.append(("SPACE",))

    # Bloco 1
    add_header("1. RECEITA BRUTA")
    add_item("    (-) IPI", dados["ipi"], negativo=True)
    add_item("    (-) ICMS-ST", dados["icms_st"], negativo=True)
    add_item("    (-) PIS", dados["pis"], negativo=True)
    add_item("    (-) COFINS", dados["cofins"], negativo=True)
    add_subtotal("FATURAMENTO BRUTO", dados["faturamento_bruto"])
    add_spacer_row()

    # Bloco 2
    add_header("2. DEDUÇÕES")
    add_item("    Descontos incondicionais", dados["descontos"], negativo=True)
    add_item("    Vendas canceladas", dados["vendas_canceladas"], negativo=True)
    add_item("    Devoluções", dados["devolucoes"], negativo=True)
    add_total("LUCRO BRUTO", dados["lucro_bruto"])
    add_spacer_row()

    # Bloco 3
    add_header("3. DESPESAS OPERACIONAIS")
    add_item("    Despesas gerais / administrativas", dados["desp_admin"], negativo=True)
    add_item("    Despesas com vendas", dados["desp_vendas"], negativo=True)
    add_item("    Outras despesas operacionais", dados["desp_outras_op"], negativo=True)
    add_subtotal("RESULTADO OPERACIONAL", dados["resultado_operacional"])
    add_spacer_row()

    # Bloco 4
    add_header("4. RECEITAS / DESPESAS NÃO OPERACIONAIS")
    add_item("    Receitas / despesas financeiras", dados["rec_desp_fin"])
    add_item("    Outras receitas / despesas", dados["outras_rec_desp"])
    add_subtotal("RESULTADO ANTES DO IR / CSLL", dados["resultado_antes_ir"])
    add_spacer_row()

    # Bloco 5
    add_header("5. PROVISÕES")
    add_item("    Provisão para o IR", dados["prov_ir"], negativo=True)
    add_item("    Provisão para a CSLL", dados["prov_csll"], negativo=True)
    add_spacer_row()

    # Bloco 6
    add_header("6. (-) PARTICIPAÇÕES")
    add_item("    Debenturistas", dados["part_debenturistas"], negativo=True)
    add_item("    Empregados", dados["part_empregados"], negativo=True)
    add_item("    Administradores", dados["part_administradores"], negativo=True)
    add_item("    Governo", dados["part_governo"], negativo=True)
    add_spacer_row()

    add_total("LUCRO LÍQUIDO DO EXERCÍCIO", dados["lucro_liquido"])

    # Montar tabela
    table_data = []
    table_styles = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [COR_BRANCO, COR_LINHA_PAR]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#dee2e6")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    idx = 0
    for linha in linhas:
        tipo = linha[0]

        if tipo == "SPACE":
            table_data.append(["", ""])
            table_styles.append(("BACKGROUND", (0, idx), (-1, idx), COR_BRANCO))
            table_styles.append(("ROWHEIGHT", (0, idx), (-1, idx), 6))

        elif tipo == "HEADER":
            table_data.append([linha[1], ""])
            table_styles.append(("BACKGROUND", (0, idx), (-1, idx), COR_HEADER))
            table_styles.append(("TEXTCOLOR", (0, idx), (-1, idx), colors.white))
            table_styles.append(("FONTNAME", (0, idx), (-1, idx), "Helvetica-Bold"))
            table_styles.append(("SPAN", (0, idx), (-1, idx)))

        elif tipo == "ITEM":
            valor = linha[2]
            negativo = linha[3] if len(linha) > 3 else False
            valor_str = f"({fmt_brl(valor)})" if negativo else fmt_brl(valor)
            table_data.append([linha[1], valor_str])
            table_styles.append(("ALIGN", (1, idx), (1, idx), "RIGHT"))
            if negativo and valor != 0:
                table_styles.append(("TEXTCOLOR", (1, idx), (1, idx), colors.HexColor("#c0392b")))

        elif tipo == "SUBTOTAL":
            valor = linha[2]
            table_data.append([linha[1], fmt_brl(valor)])
            table_styles.append(("BACKGROUND", (0, idx), (-1, idx), COR_SUBTOTAL))
            table_styles.append(("FONTNAME", (0, idx), (-1, idx), "Helvetica-Bold"))
            table_styles.append(("ALIGN", (1, idx), (1, idx), "RIGHT"))
            table_styles.append(("LINEABOVE", (0, idx), (-1, idx), 1, colors.HexColor("#1a3a5c")))
            if valor < 0:
                table_styles.append(("TEXTCOLOR", (1, idx), (1, idx), colors.HexColor("#c0392b")))

        elif tipo == "TOTAL":
            valor = linha[2]
            table_data.append([linha[1], fmt_brl(valor)])
            table_styles.append(("BACKGROUND", (0, idx), (-1, idx), COR_TOTAL))
            table_styles.append(("TEXTCOLOR", (0, idx), (-1, idx), colors.white))
            table_styles.append(("FONTNAME", (0, idx), (-1, idx), "Helvetica-Bold"))
            table_styles.append(("FONTSIZE", (0, idx), (-1, idx), 10))
            table_styles.append(("ALIGN", (1, idx), (1, idx), "RIGHT"))
            table_styles.append(("LINEABOVE", (0, idx), (-1, idx), 1.5, colors.HexColor("#0d2137")))

        idx += 1

    table = Table(table_data, colWidths=[col_desc, col_val])
    table.setStyle(TableStyle(table_styles))
    story.append(table)

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(
        f"Documento gerado em {date.today().strftime('%d/%m/%Y')}  |  Todos os valores em R$",
        rodape_style
    ))

    doc.build(story)
    return buffer.getvalue()


# ── Layout Principal ──────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Gerador de DRE",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 Gerador de DRE")
    st.caption("Demonstração do Resultado do Exercício — preencha os campos e baixe o PDF pronto.")

    # Identificação
    st.header("🏢 Identificação")
    col1, col2 = st.columns(2)
    with col1:
        empresa = st.text_input("Nome da empresa *", placeholder="Ex.: Empresa ABC Ltda.")
        cnpj = st.text_input("CNPJ", placeholder="00.000.000/0001-00")
    with col2:
        periodo = st.text_input(
            "Período de referência *",
            placeholder="Ex.: 01/01/2024 a 31/12/2024",
            value=f"01/01/{date.today().year} a 31/12/{date.today().year}",
        )
        responsavel = st.text_input("Responsável / Contador", placeholder="(opcional)")

    st.divider()

    # Bloco 1
    st.header("1. Receita Bruta")
    st.info("Informe a Receita Bruta e os impostos dedutíveis para chegar ao Faturamento Bruto.")
    col1, col2 = st.columns(2)
    with col1:
        receita_bruta = num_input("Receita Bruta (R$)", "receita_bruta",
                                  "Total de vendas antes de qualquer dedução")
        ipi    = num_input("(-) IPI (R$)", "ipi")
        icms_st = num_input("(-) ICMS-ST (R$)", "icms_st")
    with col2:
        pis    = num_input("(-) PIS (R$)", "pis")
        cofins = num_input("(-) COFINS (R$)", "cofins")

    faturamento_bruto = receita_bruta - ipi - icms_st - pis - cofins
    st.metric("📌 Faturamento Bruto", f"R$ {fmt_brl(faturamento_bruto)}")
    st.divider()

    # Bloco 2
    st.header("2. Deduções sobre o Faturamento")
    st.info("Deduções aplicadas sobre o faturamento bruto para obter o Lucro Bruto.")
    col1, col2, col3 = st.columns(3)
    with col1:
        descontos = num_input("Descontos incondicionais (R$)", "descontos")
    with col2:
        vendas_canceladas = num_input("Vendas canceladas (R$)", "vendas_canceladas")
    with col3:
        devolucoes = num_input("Devoluções (R$)", "devolucoes")

    lucro_bruto = faturamento_bruto - descontos - vendas_canceladas - devolucoes
    st.metric("📌 Lucro Bruto", f"R$ {fmt_brl(lucro_bruto)}")
    st.divider()

    # Bloco 3
    st.header("3. Despesas Operacionais")
    st.info("Despesas relacionadas à operação da empresa.")
    col1, col2, col3 = st.columns(3)
    with col1:
        desp_admin    = num_input("Despesas gerais / administrativas (R$)", "desp_admin")
    with col2:
        desp_vendas   = num_input("Despesas com vendas (R$)", "desp_vendas")
    with col3:
        desp_outras_op = num_input("Outras despesas operacionais (R$)", "desp_outras_op")

    resultado_operacional = lucro_bruto - desp_admin - desp_vendas - desp_outras_op
    st.metric("📌 Resultado Operacional", f"R$ {fmt_brl(resultado_operacional)}")
    st.divider()

    # Bloco 4
    st.header("4. Receitas / Despesas Não Operacionais")
    st.info("Use valores positivos para receitas e negativos para despesas.")
    col1, col2 = st.columns(2)
    with col1:
        rec_desp_fin_pos = num_input("Receitas financeiras (R$)", "rec_desp_fin_pos")
        rec_desp_fin_neg = num_input("Despesas financeiras (R$)", "rec_desp_fin_neg")
    with col2:
        outras_rec  = num_input("Outras receitas não operacionais (R$)", "outras_rec")
        outras_desp = num_input("Outras despesas não operacionais (R$)", "outras_desp")

    rec_desp_fin    = rec_desp_fin_pos - rec_desp_fin_neg
    outras_rec_desp = outras_rec - outras_desp
    resultado_antes_ir = resultado_operacional + rec_desp_fin + outras_rec_desp
    st.metric("📌 Resultado Antes do IR / CSLL", f"R$ {fmt_brl(resultado_antes_ir)}")
    st.divider()

    # Bloco 5
    st.header("5. Provisões — IR e CSLL")
    col1, col2 = st.columns(2)
    with col1:
        prov_ir   = num_input("Provisão para o IR (R$)", "prov_ir")
    with col2:
        prov_csll = num_input("Provisão para a CSLL (R$)", "prov_csll")
    st.divider()

    # Bloco 6
    st.header("6. (-) Participações")
    st.info("Participações deduzidas do resultado após o IR/CSLL.")
    col1, col2 = st.columns(2)
    with col1:
        part_debenturistas  = num_input("Debenturistas (R$)", "part_debenturistas")
        part_empregados     = num_input("Empregados (R$)", "part_empregados")
    with col2:
        part_administradores = num_input("Administradores (R$)", "part_administradores")
        part_governo         = num_input("Governo (R$)", "part_governo")

    total_participacoes = (
        part_debenturistas + part_empregados + part_administradores + part_governo
    )
    lucro_liquido = resultado_antes_ir - prov_ir - prov_csll - total_participacoes
    st.divider()

    # Resultado final
    st.header("📊 Resultado Final")
    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento Bruto",     f"R$ {fmt_brl(faturamento_bruto)}")
    col2.metric("Lucro Bruto",           f"R$ {fmt_brl(lucro_bruto)}")
    col3.metric("Resultado Operacional", f"R$ {fmt_brl(resultado_operacional)}")
    st.metric("💰 LUCRO LÍQUIDO DO EXERCÍCIO", f"R$ {fmt_brl(lucro_liquido)}")

    if lucro_liquido < 0:
        st.warning("⚠️ O resultado apurado é um **Prejuízo Líquido**.")
    else:
        st.success("✅ A empresa apresenta **Lucro Líquido** no período.")

    st.divider()

    # Geração de PDF
    st.header("📄 Gerar PDF")
    if not empresa.strip():
        st.error("Preencha o **nome da empresa** antes de gerar o PDF.")
    else:
        dados = {
            "empresa": empresa.strip(), "cnpj": cnpj.strip(),
            "periodo": periodo.strip(), "responsavel": responsavel.strip(),
            "receita_bruta": receita_bruta, "ipi": ipi, "icms_st": icms_st,
            "pis": pis, "cofins": cofins, "faturamento_bruto": faturamento_bruto,
            "descontos": descontos, "vendas_canceladas": vendas_canceladas,
            "devolucoes": devolucoes, "lucro_bruto": lucro_bruto,
            "desp_admin": desp_admin, "desp_vendas": desp_vendas,
            "desp_outras_op": desp_outras_op,
            "resultado_operacional": resultado_operacional,
            "rec_desp_fin": rec_desp_fin, "outras_rec_desp": outras_rec_desp,
            "resultado_antes_ir": resultado_antes_ir,
            "prov_ir": prov_ir, "prov_csll": prov_csll,
            "part_debenturistas": part_debenturistas,
            "part_empregados": part_empregados,
            "part_administradores": part_administradores,
            "part_governo": part_governo, "lucro_liquido": lucro_liquido,
        }

        if st.button("🖨️ Gerar PDF da DRE", type="primary", use_container_width=True):
            with st.spinner("Gerando o PDF..."):
                pdf_bytes = gerar_pdf(dados)
            nome_arquivo = (
                f"DRE_{empresa.strip().replace(' ', '_')}"
                f"_{date.today().strftime('%Y%m%d')}.pdf"
            )
            st.download_button(
                label="⬇️ Baixar PDF",
                data=pdf_bytes,
                file_name=nome_arquivo,
                mime="application/pdf",
                use_container_width=True,
            )
            st.success(f"PDF gerado com sucesso: **{nome_arquivo}**")

    st.divider()
    st.caption(
        "Desenvolvido como ferramenta de apoio. "
        "Consulte sempre um contador habilitado para validações legais."
    )


if __name__ == "__main__":
    main()
