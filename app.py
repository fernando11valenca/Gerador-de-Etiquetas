import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
import io

st.set_page_config(page_title="Gerador Etiquetas Copel", page_icon="⚡")
st.title("🖨️ Gerador de Etiquetas Operacionais (IT-056)")
st.write("Faça o upload da planilha Excel para gerar as etiquetas em PDF (200x104mm).")

def draw_scaled_text(c, text, x, y, max_width, font_name, max_font_size, align='center'):
    font_size = max_font_size
    while stringWidth(text, font_name, font_size) > max_width and font_size > 10:
        font_size -= 2
    c.setFont(font_name, font_size)
    if align == 'center':
        c.drawCentredString(x, y, text)
    elif align == 'right':
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)

arquivo = st.file_uploader("Arraste ou selecione a Planilha", type=["csv", "xlsx"])

if arquivo is not None:
    try:
        if arquivo.name.endswith('.csv'):
            df = pd.read_csv(arquivo, sep=None, engine='python')
        else:
            df = pd.read_excel(arquivo)
            
        st.success(f"Planilha carregada com {len(df)} linhas!")
        
        if st.button("Gerar PDF"):
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=(200*mm, 104*mm))
            font_bold = "Helvetica-Bold"
            font_regular = "Helvetica"

            for idx, row in df.iterrows():
                tipo = str(row.get('TIPO', '')).strip().upper()
                numero = str(row.get('NÚMERO', '')).strip()
                cto = str(row.get('CTO', '')).strip() if pd.notna(row.get('CTO')) else ""
                equipamento = str(row.get('EQUIPAMENTO', '')).strip() if pd.notna(row.get('EQUIPAMENTO')) else ""
                tensao = str(row.get('TENSÃO', '')).strip() if 'TENSÃO' in df.columns and pd.notna(row.get('TENSÃO')) else "230 kV"

                if not tipo or tipo == 'NAN' or not numero or numero == 'NAN':
                    continue

                c.setLineWidth(1)
                c.rect(5*mm, 5*mm, 190*mm, 94*mm)

                if tipo == 'SECCIONADORA':
                    draw_scaled_text(c, numero, 100*mm, 55*mm, 180*mm, font_bold, 150, align='center')
                    draw_scaled_text(c, cto, 190*mm, 22*mm, 120*mm, font_bold, 90, align='right')
                    c.setFont(font_regular, 30)
                    if "ENTRADA" in equipamento.upper() and " " in equipamento:
                        parts = equipamento.split(" ", 1)
                        c.drawString(8*mm, 17*mm, parts[0])
                        c.drawString(8*mm, 7*mm, parts[-1])
                    else:
                        c.drawString(8*mm, 8*mm, equipamento)

                elif tipo == 'DISJUNTOR':
                    draw_scaled_text(c, numero, 100*mm, 55*mm, 180*mm, font_bold, 150, align='center')
                    draw_scaled_text(c, cto, 100*mm, 22*mm, 180*mm, font_bold, 90, align='center')

                elif tipo in ['TP', 'TC', 'TPC']:
                    draw_scaled_text(c, numero, 100*mm, 60*mm, 180*mm, font_bold, 140, align='center')
                    c.setFont(font_bold, 60)
                    tw = stringWidth(tensao, font_bold, 60)
                    box_w = tw + 20*mm
                    c.setFillColorRGB(0, 0, 0)
                    c.rect(100*mm - (box_w/2), 29*mm, box_w, 24*mm, fill=1)
                    c.setFillColorRGB(1, 1, 1)
                    c.drawCentredString(100*mm, 35*mm, tensao)
                    c.setFillColorRGB(0, 0, 0) 
                    draw_scaled_text(c, cto, 100*mm, 12*mm, 160*mm, font_regular, 35, align='center')

                elif tipo == 'ATERRAMENTO':
                    draw_scaled_text(c, numero, 100*mm, 55*mm, 180*mm, font_bold, 150, align='center')
                    draw_scaled_text(c, cto, 190*mm, 22*mm, 120*mm, font_bold, 90, align='right')
                    c.setFont(font_regular, 30)
                    tw = stringWidth("ATERRAMENTO", font_regular, 30)
                    c.setFillColorRGB(0, 0, 0)
                    c.rect(6*mm, 6*mm, tw + 6*mm, 14*mm, fill=1)
                    c.setFillColorRGB(1, 1, 1)
                    c.drawString(9*mm, 9*mm, "ATERRAMENTO")
                    c.setFillColorRGB(0, 0, 0) 

                elif tipo in ['TRANSFORMADOR', 'BANCO DE TRANSFORMADOR', 'BANCO DE CAPACITOR', 'REATOR']:
                    draw_scaled_text(c, numero, 100*mm, 45*mm, 180*mm, font_bold, 140, align='center')
                    if tipo == 'BANCO DE TRANSFORMADOR' and equipamento:
                        c.setFont(font_regular, 30)
                        c.drawString(8*mm, 10*mm, equipamento)

                c.setFillColorRGB(0, 0, 0)
                c.rect(172*mm, 6*mm, 22*mm, 14*mm, fill=1)
                c.setFillColorRGB(1, 1, 1)
                c.setFont(font_bold, 25)
                c.drawCentredString(183*mm, 9*mm, "TRA")
                c.setFillColorRGB(0, 0, 0)
                c.showPage()

            c.save()
            buffer.seek(0)
            
            st.success("✅ PDF Gerado com Sucesso! Pronto para baixar.")
            st.download_button(label="⬇️ Baixar PDF das Etiquetas", data=buffer, file_name="Etiquetas_Copel.pdf", mime="application/pdf")
            
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
