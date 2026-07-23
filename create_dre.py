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
if st.button("Gerar PDF do DRE"):
    pdf = FPDF()
    pdf.add_page()
    
    # Config pra aceitar acentos
    pdf.set_font("Arial", size=12)
    
    # Título
    pdf.cell(200, 10, txt="Demonstração do Resultado do Exercício - DRE", ln=True, align='C')
    pdf.ln(10)
    
    # Exemplo: você pode pegar dados do seu app e jogar aqui
    # pdf.cell(200, 10, txt=f"Receita Bruta: R$ {receita}", ln=True)
    
    pdf.cell(200, 10, txt="Este é um exemplo de DRE gerado pelo sistema", ln=True)
    
    # Gera o PDF em memória
    pdf_output = pdf.output(dest='S').encode('latin-1')
    
    st.download_button(
        label="Baixar PDF",
        data=pdf_output,
        file_name="DRE.pdf",
        mime="application/pdf"
    )

if __name__ == "__main__":
    main()
