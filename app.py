import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
import io

st.set_page_config(page_title="Gerador Etiquetas Copel", page_icon="⚡")
st.title("🖨️ Gerador de Etiquetas Operacionais (IT-056)")
st.write("Faça o upload da planilha Excel ou CSV para gerar as etiquetas em formato PDF.")

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
            c = canvas.Canvas(buffer)
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

                # Definição dinâmica do tamanho da página
                is_tp_family = (tipo in ['TP', 'TC', 'TPC'])
                page_w = 160*mm if is_tp_family else 200*mm
                page_h = 104*mm
                
                c.setPageSize((page_w, page_h))
                c.setLineWidth(1)
                c.rect(5*mm, 5*mm, page_w - 10*mm, page_h - 10*mm)

                # DESENHO DOS CAMPOS
                if tipo == 'SECCIONADORA':
                    draw_scaled_text(c, numero, page_w/2, 55*mm, page_w - 20*mm, font_bold, 150, align='center')
                    draw_scaled_text(c, cto, page_w - 10*mm, 22*mm, page_w - 80*mm, font_bold, 90, align='right')
                    c.setFont(font_regular, 30)
                    if "ENTRADA" in equipamento.upper() and " " in equipamento:
                        parts = equipamento.split(" ", 1)
                        c.drawString(8*mm, 17*mm, parts[0])
                        c.drawString(8*mm, 7*mm, parts[-1])
                    else:
                        c.drawString(8*mm, 8*mm, equipamento)

                elif tipo == 'DISJUNTOR':
                    draw_scaled_text(c, numero, page_w/2, 55*mm, page_w - 20*mm, font_bold, 150, align='center')
                    draw_scaled_text(c, cto, page_w/2, 22*mm, page_w - 20*mm, font_bold, 90, align='center')

                elif is_tp_family:
                    # Medidas para 160x104mm (TP, TC, TPC)
                    draw_scaled_text(c, numero, page_w/2, 60*mm, page_w - 20*mm, font_bold, 130, align='center')
                    c.setFont(font_bold, 60)
                    tw = stringWidth(tensao, font_bold, 60)
                    box_w = tw + 20*mm
                    box_h = 24*mm
                    box_x = (page_w/2) - (box_w/2)
                    
                    c.setFillColorRGB(0, 0, 0)
                    c.rect(box_x, 32*mm, box_w, box_h, fill=1)
                    c.setFillColorRGB(1, 1, 1)
                    c.drawCentredString(page_w/2, 38*mm, tensao)
                    c.setFillColorRGB(0, 0, 0) 
                    
                    # CTO / Barra principal: Limitando a largura para não invadir a margem
                    draw_scaled_text(c, cto, page_w/2, 14*mm, page_w - 40*mm, font_bold, 30, align='center')

                elif tipo == 'ATERRAMENTO':
                    draw_scaled_text(c, numero, page_w/2, 55*mm, page_w - 20*mm, font_bold, 150, align='center')
                    draw_scaled_text(c, cto, page_w - 10*mm, 22*mm, page_w - 80*mm, font_bold, 90, align='right')
                    c.setFont(font_regular, 30)
                    tw = stringWidth("ATERRAMENTO", font_regular, 30)
                    c.setFillColorRGB(0, 0, 0)
                    c.rect(6*mm, 6*mm, tw + 6*mm, 14*mm, fill=1)
                    c.setFillColorRGB(1, 1, 1)
                    c.drawString(9*mm, 9*mm, "ATERRAMENTO")
                    c.setFillColorRGB(0, 0, 0)

                elif tipo in ['TRANSFORMADOR', 'BANCO DE TRANSFORMADOR', 'BANCO DE CAPACITOR', 'REATOR']:
                    draw_scaled_text(c, numero, page_w/2, 45*mm, page_w - 20*mm, font_bold, 140, align='center')
                    if tipo == 'BANCO DE TRANSFORMADOR' and equipamento:
                        c.setFont(font_regular, 30)
                        c.drawString(8*mm, 10*mm, equipamento)

                # Caixa TRA (Posição dinâmica baseada na largura da página)
                c.setFillColorRGB(0, 0, 0)
                c.rect(page_w - 27*mm, 6*mm, 22*mm, 14*mm, fill=1)
                c.setFillColorRGB(1, 1, 1)
                c.setFont(font_bold, 25)
                c.drawCentredString(page_w - 16*mm, 9*mm, "TRA")
                c.setFillColorRGB(0, 0, 0)
                
                c.showPage()

            c.save()
            buffer.seek(0)
            
            st.success("✅ PDF Gerado com Sucesso!")
            st.download_button(label="⬇️ Baixar PDF das Etiquetas", data=buffer, file_name="Etiquetas_Copel.pdf", mime="application/pdf")
            
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
