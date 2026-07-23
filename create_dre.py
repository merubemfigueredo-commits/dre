import streamlit as st
from fpdf import FPDF # usa fpdf2
from io import BytesIO
from datetime import date

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
# ── PDF ───────────────────────────────────────────────────────────────────────
def gerar_pdf(dados: dict) -> BytesIO:
    """Gera o PDF da DRE usando fpdf2 - versão compatível com Streamlit Cloud"""
    pdf = FPDF()
    pdf.add_page()
    
    # Usa fonte core que aceita latin-1 sem quebrar
    pdf.set_font("Helvetica", size=12)

    # Função auxiliar pra limpar acentos e evitar erro de encode
    def clean(text):
        return text.encode('latin-1', 'replace').decode('latin-1')

    # Título
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, clean("DEMONSTRACAO DO RESULTADO DO EXERCICIO - DRE"), ln=True, align='C')
    pdf.ln(5)
    
    # Identificação
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, clean(f"Empresa: {dados['empresa']}"), ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 6, clean(f"CNPJ: {dados['cnpj']}"), ln=True)
    pdf.cell(0, 6, clean(f"Periodo: {dados['periodo']}"), ln=True)
    if dados['responsavel']:
        pdf.cell(0, 6, clean(f"Responsavel: {dados['responsavel']}"), ln=True)
    pdf.ln(5)

    # Função auxiliar pra linha
    def linha(desc, valor):
        pdf.cell(140, 6, clean(desc), border=0)
        pdf.cell(50, 6, f"R$ {fmt_brl(valor)}", border=0, align='R', ln=True)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, clean("1. RECEITA BRUTA"), ln=True)
    pdf.set_font("Helvetica", size=11)
    linha("Receita Bruta", dados['receita_bruta'])
    linha("(-) IPI", -dados['ipi'])
    linha("(-) ICMS-ST", -dados['icms_st'])
    linha("(-) PIS", -dados['pis'])
    linha("(-) COFINS", -dados['cofins'])
    pdf.set_font("Helvetica", "B", 11)
    linha("= FATURAMENTO BRUTO", dados['faturamento_bruto'])
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, clean("2. DEDUCOES"), ln=True)
    pdf.set_font("Helvetica", size=11)
    linha("Descontos", -dados['descontos'])
    linha("Vendas canceladas", -dados['vendas_canceladas'])
    linha("Devolucoes", -dados['devolucoes'])
    pdf.set_font("Helvetica", "B", 11)
    linha("= LUCRO BRUTO", dados['lucro_bruto'])
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, clean("3. DESPESAS OPERACIONAIS"), ln=True)
    pdf.set_font("Helvetica", size=11)
    linha("Despesas Admin", -dados['desp_admin'])
    linha("Despesas Vendas", -dados['desp_vendas'])
    linha("Outras Despesas Op", -dados['desp_outras_op'])
    pdf.set_font("Helvetica", "B", 11)
    linha("= RESULTADO OPERACIONAL", dados['resultado_operacional'])
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, clean("4. RESULTADO NAO OPERACIONAL"), ln=True)
    pdf.set_font("Helvetica", size=11)
    linha("Receitas/Despesas Fin", dados['rec_desp_fin'])
    linha("Outras Rec/Desp", dados['outras_rec_desp'])
    pdf.set_font("Helvetica", "B", 11)
    linha("= RESULTADO ANTES IR/CSLL", dados['resultado_antes_ir'])
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, clean("5. PROVISOES"), ln=True)
    pdf.set_font("Helvetica", size=11)
    linha("Provisao IR", -dados['prov_ir'])
    linha("Provisao CSLL", -dados['prov_csll'])
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, clean("6. PARTICIPACOES"), ln=True)
    pdf.set_font("Helvetica", size=11)
    linha("Debenturistas", -dados['part_debenturistas'])
    linha("Empregados", -dados['part_empregados'])
    linha("Administradores", -dados['part_administradores'])
    linha("Governo", -dados['part_governo'])
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"LUCRO LIQUIDO: R$ {fmt_brl(dados['lucro_liquido'])}", ln=True, align='C')

    # CORREÇÃO PRINCIPAL AQUI: gera direto em bytes
    pdf_bytes = pdf.output()
    return BytesIO(pdf_bytes)
    # -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
