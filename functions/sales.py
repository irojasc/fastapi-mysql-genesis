from reportlab.lib.pagesizes import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.platypus import Flowable
from basemodel.sales import Body_Ticket, Item_Ticket
from service.sales import check_sales_document_status
from decimal import Decimal
from config.db import MIFACT_MIRUC
import io
import base64
import asyncio
import httpx


# Registrar fuente compatible con caracteres Unicode (en caso de español)
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

class SvgFlowable(Flowable):
    def __init__(self, svg_path, width=None, height=None, max_width=120, max_height=60):
        super().__init__()
        self.drawing = svg2rlg(svg_path)

        # Escala automática proporcional
        scale_x = (max_width / self.drawing.width) if self.drawing.width > 0 else 1
        scale_y = (max_height / self.drawing.height) if self.drawing.height > 0 else 1
        self.scale = min(scale_x, scale_y)

        # Ancho y alto finales en puntos
        self.width = self.drawing.width * self.scale
        self.height = self.drawing.height * self.scale

    def draw(self):
        self.canv.saveState()
        # Centra el dibujo horizontalmente dentro del ancho disponible
        x = (self.canv._pagesize[0] - self.width) / 2
        y = 0
        self.canv.translate(x, y)
        self.canv.scale(self.scale, self.scale)
        renderPDF.draw(self.drawing, self.canv, 0, 0)
        self.canv.restoreState()

# 🧩 Función generadora de ticket
def generar_ticket(nombre_archivo, logo_path, items, do_c):
    # """
    # Genera un ticket de venta (80 mm) con ReportLab.
    # - items: lista de diccionarios con keys ['codigo', 'descripcion', 'cantidad', 'pvp', 'descuento', 'total']
    # - resumen: diccionario con ['subtotal', 'descuento', 'igv', 'total']
    # """

    
    def mover_contenido(canvas, doc):
        shift_mm = 5
        canvas.translate(shift_mm, 0)  # mueve 5mm hacia arriba (valor negativo baja)

    def truncar_texto(texto, longitud):
        return texto if len(texto) <= longitud else texto[:longitud-1] + ".."
    
    try:

        #buffer para almacenar pdf
        # Crear buffer en memoria
        buffer = io.BytesIO()

        # Tamaño del ticket
        width = 72 * mm
        # width = 58 * mm
        left_margin = right_margin = top_margin = bottom_margin = 4 * mm
        # printable_width = width - left_margin - right_margin

        # Crear documento
        # doc = SimpleDocTemplate(
        #     r'.\recibo.pdf',
        #     pagesize=(width, 210 * mm),  # largo ajustable
        #     leftMargin= 0 * mm,
        #     rightMargin= 0 * mm,
        #     topMargin=0 * mm,
        #     bottomMargin=0 * mm
        # )

        doc = SimpleDocTemplate(
            buffer,
            pagesize=(width, 210 * mm),  # largo ajustable
            leftMargin= 0 * mm,
            rightMargin= 0 * mm,
            topMargin=0 * mm,
            bottomMargin=0 * mm
        )

        elements = []

        # === Estilos ===
        estilo_descripcion = ParagraphStyle(
            name="descripcion",
            fontName="HeiseiMin-W3",
            fontSize=9,
            leading=9,
            spaceAfter=0,
        )
        estilo_encabezado_bold  = ParagraphStyle(
            'center_title_bold',
            fontName='Helvetica-Bold',
            fontSize=9,
            alignment=1,  # centrado
            leading=10,
            spaceAfter=1,
            spaceBefore=0,
        )

        estilo_datos = ParagraphStyle(
            'datos',
            fontName='HeiseiMin-W3',
            fontSize=8,
            leading=8,
            spaceAfter=0,
            spaceBefore=0,
        )

        estilo_centrado_bold = ParagraphStyle(
            'center_text_bold',
            fontName='Helvetica-Bold',
            fontSize=9,
            alignment=1,
            leading=10,
        )

        estilo_centrado = ParagraphStyle(
            'center_text',
            fontName='HeiseiMin-W3',
            fontSize=8,
            alignment=1,
            leading=9,
        )


        # -----------------------------------------------------
        # 🧾 ENCABEZADO DE DOCUMENTO
        # -----------------------------------------------------
        nombre_negocio = Paragraph("MUSEO LIBRERÍA GÉNESIS", estilo_centrado_bold)
        ruc_negocio = Paragraph(f"""RUC: {MIFACT_MIRUC}""", estilo_centrado)
        elements += [nombre_negocio, ruc_negocio]

        # 🖼️ Logo centrado
        logo = SvgFlowable(logo_path, width=10, height=10)
        elements.append(logo)
        # elements.append(Spacer(1, 2))
        elements.append(Spacer(1, 0))

        titulo = Paragraph("<b>NOTA DE VENTA ELECTRÓNICA</b>", estilo_encabezado_bold)
        serie = Paragraph(f"<b>{do_c['doc_num']}</b>", estilo_encabezado_bold)
        elements += [titulo, serie, Spacer(1, 2)]

        # # Primera fila → fecha de emisión
        # fecha = Paragraph(f"Fecha de emisión: {do_c['doc_date']}  Hora: {do_c['doc_time']}", estilo_datos)
        # elements.append(fecha)
        
        # Segunda fila → cliente y número de documento alineados
        cliente_doc_date = Table(
            [
                [
                    Paragraph(f"Fecha de emisión: {do_c['doc_date']}", estilo_datos),
                    Paragraph(f"Hora: {do_c['doc_time']}", estilo_datos)
                ]
            ],
            colWidths=[40 * mm, 40 * mm],
            hAlign='LEFT'
        )
        cliente_doc_date.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
            ]))

        elements += [cliente_doc_date, Spacer(1, 0)]


        # Segunda fila → cliente y número de documento alineados
        cliente_doc = Table(
            [
                [
                    Paragraph(f"Cliente: {truncar_texto(do_c['card_name'], 27)}", estilo_datos),
                ],
                [
                    Paragraph(f"Doc: {do_c['card_num']}", estilo_datos),
                ]
            ],
            colWidths=[55 * mm, 25 * mm],
            hAlign='LEFT'
        )
        cliente_doc.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))

        elements += [cliente_doc, Spacer(1, 4)]

        # === Cabecera de tabla ===
        headers = ["Descripción", "Cant", "PVP", "Dscto", "Total"]
        tabla_data = [headers]



        # === Contenido dinámico ===
        for item in items:
            descripcion = truncar_texto(item['dscp'], 14)
            codigo = f"<font color='black' size='9'>{item['cod']}</font>"

            # Descripción con código debajo (usamos un Paragraph con salto de línea)
            desc_paragraph = Paragraph(f"{descripcion}<br/>{codigo}", estilo_descripcion)

            fila = [
                desc_paragraph,
                f"{item['qty']}",
                f"{item['pvp']}",
                f"{item['dsct']}",
                f"{item['total_linea']}",
            ]
            tabla_data.append(fila)

        # === Crear tabla ===
        table = Table(tabla_data, colWidths=[width * 0.45,  # descripción
                                            width * 0.10,  # cantidad
                                            width * 0.15,  # pvp
                                            width * 0.13,  # descuento
                                            width * 0.17])  # total

        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'HeiseiMin-W3', 9),
            ('FONT', (0, 1), (-1, -1), 'HeiseiMin-W3', 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.grey),
        ]))

        elements.append(table)
        # elements.append(Spacer(1, 1 * mm))

        # === Pie de página (resumen a la derecha) ===
        resumen_data = [
            ["Subtotal:", f"S/ {do_c['sub_total']}"],
            ["Descuento:", f"S/ {do_c['dscto_total']}"],
            ["IGV:", f"S/ {do_c['tax_total']}"],
            ["Total:", f"S/ {do_c['total']}"],
        ]

        resumen_table = Table(resumen_data, colWidths=[width * 0.75, width * 0.25])
        resumen_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONT', (0, 0), (-1, 2), 'HeiseiMin-W3', 9),
            ('FONT', (-1, -1), (-1, -1), 'HeiseiMin-W3', 10),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))

        elements.append(resumen_table)
     

        # Crear el contenido de la fila
        texto_fila_pago = [
            f"Metodo de pago: ",
            f"{do_c['pay_method']}",
        ]

        tabla_doc_pago = Table([texto_fila_pago], colWidths=[19*mm, 51*mm])
        tabla_doc_pago.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))

        elements.append(Spacer(1, 6))
        elements.append(tabla_doc_pago)



        # Dibujar los cuadrados vacíos como símbolos Unicode
        checkbox_empty = "☐"

        # Crear el contenido de la fila
        texto_fila = [
            f"{checkbox_empty} Boleta",
            f"{checkbox_empty} Factura",
            "DOC: .................................................."
        ]

        tabla_doc = Table([texto_fila], colWidths=[13*mm, 13*mm, 45*mm])
        tabla_doc.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))

        elements.append(Spacer(1, 6))
        elements.append(tabla_doc)

        # === Generar PDF ===
        doc.build(elements, onFirstPage = mover_contenido, onLaterPages=mover_contenido)
        # doc.build(elements, onFirstPage=mover_contenido, onLaterPages=mover_contenido)

        #generar pdf en base64
        # Ir al inicio del buffer
        buffer.seek(0)

        # # 5️⃣ Obtener el contenido binario
        # pdf_bytes = buffer.getvalue()

        # # 6️⃣ Guardar también en disco
        # with open("comprobante.pdf", "wb") as f:
        #     f.write(pdf_bytes)

        # Convertir PDF a base64 (para enviarlo en JSON)
        pdf_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        return True, f"✅ Ticket generado: {nombre_archivo}", pdf_base64
    
    except Exception as e:
        print(f"An error ocurred: {e}")
        return False, f"An error ocurred: {e}", None

def generar_ticket_close(nombre_archivo, items, do_c):
    # """
    # Genera un ticket de venta (80 mm) con ReportLab.
    # - items: lista de diccionarios con keys ['codigo', 'descripcion', 'cantidad', 'pvp', 'descuento', 'total']
    # - resumen: diccionario con ['subtotal', 'descuento', 'igv', 'total']
    # """

    def mover_contenido(canvas, doc):
        shift_mm = 5
        canvas.translate(shift_mm, 0)  # mueve 5mm hacia arriba (valor negativo baja)

    def truncar_texto(texto, longitud):
        return texto if len(texto) <= longitud else texto[:longitud-1] + ".."
    
    try:

        #buffer para almacenar pdf
        # Crear buffer en memoria
        buffer = io.BytesIO()

        # Tamaño del ticket
        width = 72 * mm
        # left_margin = right_margin = top_margin = bottom_margin = 4 * mm
        # printable_width = width - left_margin - right_margin

        # Crear documento
        # doc = SimpleDocTemplate(
        #     r'.\recibo.pdf',
        #     pagesize=(width, 210 * mm),  # largo ajustable
        #     leftMargin= 0 * mm,
        #     rightMargin= 0 * mm,
        #     topMargin=0 * mm,
        #     bottomMargin=0 * mm
        # )

        doc = SimpleDocTemplate(
            buffer,
            pagesize=(width, 210 * mm),  # largo ajustable
            leftMargin= 0 * mm,
            rightMargin= 0 * mm,
            topMargin=0 * mm,
            bottomMargin=0 * mm
        )

        elements = []

        # === Estilos ===
        estilo_descripcion = ParagraphStyle(
            name="descripcion",
            fontName="HeiseiMin-W3",
            fontSize=9,
            leading=9,
            spaceAfter=0,
        )
        
        estilo_encabezado_bold  = ParagraphStyle(
            'center_title_bold',
            fontName='Helvetica-Bold',
            fontSize=9,
            alignment=1,  # centrado
            leading=10,
            spaceAfter=1,
            spaceBefore=0,
        )

        estilo_datos = ParagraphStyle(
            'datos',
            fontName='HeiseiMin-W3',
            fontSize=8,
            leading=8,
            spaceAfter=0,
            spaceBefore=0,
        )

        estilo_centrado_bold = ParagraphStyle(
            'center_text_bold',
            fontName='Helvetica-Bold',
            fontSize=9,
            alignment=1,
            leading=10,
        )

        estilo_centrado = ParagraphStyle(
            'center_text',
            fontName='HeiseiMin-W3',
            fontSize=8,
            alignment=1,
            leading=9,
        )


        # -----------------------------------------------------
        # 🧾 ENCABEZADO DE DOCUMENTO
        # -----------------------------------------------------

        # serie = Paragraph(f"<b>{do_c['doc_num']}</b>", estilo_encabezado_bold)
        # elements += [titulo, serie, Spacer(1, 2)]

        titulo = Paragraph("<b>RESUMEN VENTAS</b>", estilo_encabezado_bold)
        elements += [titulo, Spacer(1, 2)]


        # === Cabecera de tabla ===
        headers = ["N#", "Descripcion", "Cant", "Pago", "Total"]
        tabla_data = [headers]

        # === Contenido dinámico ===
        for item in items:
            descripcion = truncar_texto(item['dscp'], 14)

            # Descripción con código debajo (usamos un Paragraph con salto de línea)
            if item['status'] == 'A': # formato para cuando linea esta anulada
                desc_paragraph = Paragraph(f"<strike>{descripcion}</strike>", estilo_descripcion)
            else:
                desc_paragraph = Paragraph(f"{descripcion}", estilo_descripcion)

            fila = [
                f"{item['enum']}",
                desc_paragraph,
                f"{item['qty']}",
                f"{item['pay_method']}",
                f"{item['total_linea']}"
            ]

            # fila = [
            #     f"{item['enum']}",
            #     desc_paragraph,
            #     f"{item['qty']}",
            #     f"{item['pay_method']}",
            #     f"{item['total_linea']}",
            # ]
            tabla_data.append(fila)

        # === Crear tabla ===
        table = Table(tabla_data, colWidths=[width * 0.10,  # enum
                                            width * 0.45,  #dsct
                                            width * 0.15,  # pvp
                                            width * 0.13,  # descuento
                                            width * 0.17])  # total

        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'HeiseiMin-W3', 9),
            ('FONT', (0, 1), (-1, -1), 'HeiseiMin-W3', 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.grey),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 1 * mm))

        # === Pie de página (resumen a la derecha) ===
        resumen_data = [
            ["Caja apertura:", f"S/ {do_c['caja']}"],
            ["◆ Efectivo ventas:", f"S/ {do_c['cash_teory']}"],
            ["Efectivo diferencia:", f"S/ {do_c['diff']}"],
            ["Efectivo total:", f"S/ {do_c['total']}"],
            ["◆ POS(Maquina) ventas:", f"S/ {do_c['card_total_plus_wallet_machine']}"],
            ["◆ Yape/Plin(A celular) ventas:", f"S/ {do_c['wallet_no_machine_total']}"],
        ]

        resumen_table = Table(resumen_data, colWidths=[width * 0.75, width * 0.25])
        resumen_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONT', (0, 0), (-1, -1), 'HeiseiMin-W3', 9),
            ('FONT', (0, 3), (-1, 3), 'HeiseiMin-W3', 10),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LINEABOVE', (0, 4), (-1, 4), 0.5, colors.black),
        ]))

        elements.append(resumen_table)
     

        # Crear el contenido de la fila
        texto_fila_items2count = [
            f"""Estampilla: Ini. ({do_c["item2Total"]}) - Vent. ({do_c["item2Sold"]}) = Fin ({do_c["item2Total"] - do_c["item2Sold"]})""", #hardcodeado
            "",
        ]

        texto_fila_pago = [
            f"Fecha Caja: ",
            f"{do_c['date']}",
        ]

        # Cajero
        texto_fila_cajero = [
            f"Cajero: ",
            f"{do_c['vendedor']}",
        ]

        tabla_doc_pago = Table([
                                texto_fila_items2count,
                                texto_fila_pago,
                                texto_fila_cajero
                                ], colWidths=[19*mm, 51*mm])
        
        tabla_doc_pago.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))

        elements.append(Spacer(1, 6))
        elements.append(tabla_doc_pago)

        # === Generar PDF ===
        doc.build(elements, onFirstPage = mover_contenido, onLaterPages=mover_contenido)
        # doc.build(elements)

        #generar pdf en base64
        # Ir al inicio del buffer
        buffer.seek(0)

        # # 5️⃣ Obtener el contenido binario
        # pdf_bytes = buffer.getvalue()

        # # # 6️⃣ Guardar también en disco
        # with open(nombre_archivo, "wb") as f:
        #     f.write(pdf_bytes)

        # Convertir PDF a base64 (para enviarlo en JSON)
        pdf_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        return True, f"✅ Ticket generado: {nombre_archivo}", pdf_base64
    
    except Exception as e:
        print(f"An error ocurred: {e}")
        return False, f"An error ocurred: {e}", None



def build_body_ticket(data: list[dict]) -> Body_Ticket:
    if not data:
        return Body_Ticket()

    first = data[0]

    def to_str_decimal(value):
        if isinstance(value, Decimal):
            return value.to_eng_string()
        return str(value) if value is not None else "0.00"

    body = Body_Ticket(
        doc_num=str(first.get("doc_num", "")),
        doc_date=first.get("doc_date").strftime("%Y-%m-%d") if first.get("doc_date") else "",
        doc_time= first.get("doc_date").strftime("%H:%M") if first.get("doc_date") else "",
        card_name=str(first.get("card_name", "")),
        card_num=str(first.get("card_num", "")),
        pay_method=str(first.get("pay_method", "")),
        sub_total=to_str_decimal(first.get("sub_total", Decimal("0.00"))),
        dscto_total=to_str_decimal(first.get("dscto_total", Decimal("0.00"))),
        tax_total=to_str_decimal(first.get("tax_total", Decimal("0.00"))),
        total=to_str_decimal(first.get("total", Decimal("0.00"))),
        items=[
            Item_Ticket(
                id=str(item.get("Id", "0")),
                dscp=str(item.get("dscp", "")),
                cod=str(item.get("cod", "")) if item.get("cod") else "",
                qty=str(item.get("qty", "0")),
                pvp=to_str_decimal(item.get("pvp", Decimal("0.00"))),
                dsct=to_str_decimal(item.get("dsct", Decimal("0.00"))),
                total_linea=to_str_decimal(item.get("total_linea", Decimal("0.00"))),
            )
            for item in data
        ]
    )

    body.doc_type = str(first.get("doc_type", None))
    body.doc_status = str(first.get("doc_status", None))

    return body


def format_to_8digits(n: int, limit: int) -> str:
    # """
    # Formatea un número entero n a una cadena con ceros a la izquierda,
    # usando un límite de dígitos especificado por 'limit'.
    
    # Si el número excede la cantidad de dígitos permitidos, retorna None.
    # """
    if n < 0 or limit <= 0:
        return None  # No aceptamos negativos ni límites inválidos

    num_str = str(n)

    if len(num_str) > limit:
        return None

    return num_str.zfill(limit)


async def sincronizar_documentos_pendientes(client: httpx.AsyncClient = None, docList: list = [], time:str=None):
    
    returned_data = []
    try:
        for index, row in enumerate(docList):
            try:
                json_data, status_code = await check_sales_document_status(client = client, params = row)

                if status_code == 429:
                    print("¡Límite alcanzado! Abortando para intentar en el siguiente turno.")
                    break # Sale del bucle actual para esperar al próximo job (3 o 4 AM)

                if "estado_documento" in json_data and json_data.get("estado_documento", None): #verifica que el estado del json exista
                    estado_documento = int(json_data["estado_documento"]) #convierte a entero el string del estado
                    if row["estado_documento"] != estado_documento: #si es distinto agrega en lista
                        returned_data.append({
                            "DocEntry": row["DocEntry"],
                            "Status": estado_documento,
                            "UpdateDate": time
                        })

                #delay de 3 segundos entre consultas para evitar bloqueo
                await asyncio.sleep(3.0)

            except Exception as e:
                print(f"Error procesando documento numero {index}: {e}")

    except Exception as e:
        print(f"Error sincronizar_documentos_pendientes: {e}")

    finally:
        return returned_data

