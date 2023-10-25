#!/usr/bin/env python
# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.http import request
from odoo.tools.float_utils import float_compare
import unicodedata
'''from .InvoiceLine import Factura  #utils
from .NotaCredito import NotaCredito
from .NotaDebito import NotaDebito
from . import utils
from utils import InvoiceLine as Factura 
from utils import NotaCredito as NotaCredito
from utils import NotaDebito as NotaDebito'''
from . import Factura  #
from . import NotaCredito
from . import NotaDebito
from . import GuiaRemision
#https://stackoverflow.com/questions/16780510/module-object-is-not-callable-calling-method-in-another-file/16780543
from suds.client import Client  #para exportar y la firma 
from suds.wsse import * #para exportar y la firmaa
from signxml import XMLSigner, XMLVerifier, methods  #para exportar y la firmaa
from datetime import datetime, timedelta
from io import StringIO
#import io
import xlwt, xlsxwriter
from xlwt import easyxf
import xml.etree.ElementTree as ET
import requests
import zipfile
import base64

import os
import logging
import json
import math
import time
import calendar
'''import sys 
sys.path.insert(0, 'utils/InvoiceLine')
sys.path.insert(0, 'utils/NotaCredito')
sys.path.insert(0, 'utils/NotaDebito')'''

# mapping invoice type to refund type
TYPE2REFUND = {
    "out_invoice": "out_refund",  # Customer Invoice
    "in_invoice": "in_refund",  # Vendor Bill
    "out_refund": "out_invoice",  # Customer Refund
    "in_refund": "in_invoice",  # Vendor Refund
}

class accountDetraccion(models.Model):
    _name = "account.detraccion"
    _order = "fecha_uso, id desc"
    name = fields.Char("Nombre",compute="_compute_name")
    nombre = fields.Char("Nombre")
    porcentaje = fields.Float("Porcentaje de detraccion")
    monto = fields.Float("Monto")
    fecha_uso = fields.Date("Fecha de inicio de uso",default=lambda self: fields.Datetime.now())
    #@api.one
    def _compute_name(self):
        self.name=str(self.nombre) + ' - ' +str(self.porcentaje)+ '%'
'''
class ActivosFijos(models.Model):
    _name = "account.activos"

    codigo = fields.Text("Código")
    descripcion = fields.Text("Descripción")
    marca = fields.Text("Marca de activo fijo")
    modelo = fields.Text("Modelo del activo fijo")
    serie = fields.Text("Número de serie y/o placa del activo fijo")
    saldo = fields.Float("Saldo inicial")
    adquisicion = fields.Text("Adquisiciones")
    mejora = fields.Text("Mejoras")
    retiro = fields.Text("Retiros y/o bajas")
    otros = fields.Text("Otros ajustes")
    historico = fields.Text("Valor histórico")
    inflacion = fields.Text("Ajuste por inflación")
    ajustado = fields.Text("Valor ajustado")
    fecha_adq = fields.Date("Fecha de adquisición")
    fecha_uso = fields.Date("Fecha de inicio de uso")
    metodo = fields.Text("Método aplicado")
    n_documento = fields.Text("Nro. de documento de autorización")
    porcentaje = fields.Float("Porcentaje de depreciación")
    acumulada = fields.Text("Depreciación acumulada al cierre del ejercicio anterior")
    depreciacion = fields.Text("Depreciación del ejercicio")
    depreciacion_retiro = fields.Text(
        "Depreciación  del ejercicio relacionada con retiros y/o bajas"
    )
    depreciacion_otros = fields.Text("Depreciación relacionada con otros ajustes")
    depreciacion_acumulada = fields.Text("Depreciación acumulada histórica")
    depreciacion_ajuste = fields.Text("Ajuste por inflación de la depreciación")
    depreciacion_acumulada_ajustada = fields.Text(
        "Depreciación acumulada ajustada por inflación"
    )
'''

class accountInvoice(models.Model):
    _inherit = "account.move"

    pruebautils = fields.Text("utils", copy=False)
    documentoXML = fields.Text("Documento XML", default=" ", copy=False)
    documentoXMLcliente = fields.Binary("XML cliente", copy=False)
    documentoXMLcliente_fname = fields.Char(
        "Prueba name", compute="set_xml_filename", copy=False
    )
    documentoZip = fields.Binary("Documento Zip", default="", copy=False)
    documentoEnvio = fields.Text("Documento de Envio", copy=False)
    paraEnvio = fields.Text("XML para cliente", copy=False)
    documentoRespuesta = fields.Text("Documento de Respuesta XML", copy=False)
    documentoRespuestaZip = fields.Binary("CDR SUNAT", copy=False)
    documentoEnvioTicket = fields.Text("Documento de Envio Ticket", copy=False)
    numeracion = fields.Char("Número de factura", copy=False)
    mensajeSUNAT = fields.Char("Respuesta SUNAT", copy=False)
    codigoretorno = fields.Char("Código retorno", default="0000", copy=False)
    estado_envio = fields.Boolean("Enviado a SUNAT", default=False, copy=False)
    operacionTipo = fields.Selection(
        string="Tipo de operación",
        selection=[
            ("0101", "Venta interna"),
            ("0200", "Exportación de bienes"),
            ("0401", "Ventas no domiciliados que no califican como exportación"),
        ],
        default="0101",
    )
    forma_de_pago = fields.Selection(
        string="Forma de Pago",
        selection=[
            ("Contado", "Contado"),
            ("Credito", "Credito")
        ],
        default="Contado",
    )
    termino_pago_sunat = fields.One2many('termino.pago.sunat','account_inv', string='Datos de termino de Pago')  
    date_invoice = fields.Date("Fecha de Factura",default=lambda self: fields.Datetime.now())
    date_due = fields.Date("Fecha de Vencimiento",default=lambda self: fields.Datetime.now())

    #@api.multi
    #@api.onchange("forma_de_pago")
    @api.onchange("date_due")
    def onchange_forma_de_pago(self):
        #fecha1=datetime.now()
        if self.date_invoice:
            f_inicio=str(self.date_invoice)
            f_fin=str(self.date_due)
            if f_fin!='False':
                fecha1=datetime.strptime(f_inicio, "%Y-%m-%d")
                fecha2 = datetime.strptime(f_fin,"%Y-%m-%d")
                dias = (fecha2-fecha1).days
                #if self.forma_de_pago=='Credito':
                if self.detraccion==True:
                    monto_neto=self.amount_total-round(self.amount_total*(self.detraccion_porcen/100),0)
                else:
                    monto_neto=self.amount_total
                if dias>0:
                    #mobile_id=self.search([('mobile','=',self.mobile)])
                    vals = {'invoice_date_due':self.date_due, #self.date_due,
                            'amount': monto_neto, #self.amount_total,
                            'account_inv': self.id
                            }
                    vals2 = {'invoice_date_due':self.date_due, #self.date_due,
                            'amount': monto_neto
                            }
                    self.forma_de_pago='Credito'
                    exite_termino=self.env['termino.pago.sunat'].search([('account_inv','=',self._origin.id)], limit=1)
                    if exite_termino.id !=False:
                        self.env['termino.pago.sunat'].search([('account_inv','=',self._origin.id)]).write(vals2)
                    else:
                        self.termino_pago_sunat |= self.env['termino.pago.sunat'].new(vals)
                    #raise Warning(self._origin.id)
                    #obj = 
                    #self.env['termino.pago.sunat'].sudo().create(vals)
                    #return obj
                    #raise ValidationError(_('cambio a credito'))

    @api.model
    def create(self, vals):
        if vals['origin']:
            vals['forma_de_pago']=self.env["sale.order"].search([["name", "=", vals['origin']]]).forma_de_pago
            
        record = super(accountInvoice, self).create(vals)
        if vals['origin']:
            val = {}
            values2 = self.env['termino.pago.sunat'].search([["sale_ord.name", "=", vals['origin']]])
            for record2 in values2:
                val['account_inv'] = record.id#vals['id']
                record2.write(val)
        #self._actualizar_pago_term_sunat()
        return record
    # invoice_type_code = fields.Selection(string="Tipo de Comprobante", store=True, related="journal_id.invoice_type_code_id", readonly=True)
    # invoice_type_code = fields.Char(string="Tipo de Comprobante", default=_set_invoice_type_code, readonly = True)

    # Para documentos de proveedor
    def _list_invoice_type(self):
        catalogs = self.env["einvoice.catalog.01"].search([])
        list = []
        for cat in catalogs:
            list.append((cat.code, cat.name))
        return list

    tipo_documento = fields.Selection(
        string="Tipo de Documento", selection=_list_invoice_type, default="01"
    )
    muestra = fields.Boolean("Muestra", default=False)
    send_route = fields.Selection(
        string="Ruta de envío", store=True, related="company_id.send_route", readonly=True
    )

    response_code = fields.Char("response_code", copy=False)
    referenceID = fields.Char("Referencia", copy=False)
    motivo = fields.Text("Motivo")

    total_venta_gravado = fields.Monetary(
        "Gravado", default=0.0, compute="_compute_total_venta"
    )
    total_venta_inafecto = fields.Monetary(
        "Inafecto", default=0.0, compute="_compute_total_venta"
    )
    total_venta_exonerada = fields.Monetary(
        "Exonerado", default=0.0, compute="_compute_total_venta"
    )
    total_venta_gratuito = fields.Monetary(
        "Gratuita", default=0.0, compute="_compute_total_venta"
    )
    total_descuentos = fields.Monetary(
        "Total Descuentos", default=0.0, compute="_compute_total_venta"
    )
    journal_id=fields.Many2one("account.journal",domain="[('invoice_type_code_id','=','type_code')]", limit=1)#domain="[('invoice_type_code_id','=',type_code)]"

    digestvalue = fields.Char("DigestValue")
    final = fields.Boolean("Es final?", default=False, copy=False)
    detraccion = fields.Boolean("Detracción", default=False)
    detraccion_id=fields.Many2one("account.detraccion","Seleccione la detracción")
    detraccion_porcen = fields.Float("Detraccion %",compute="_compute_Detraccion")
    
    def _compute_Detraccion(self):
        for record in self:
            #record.detraccion_porcen=self.env["account.detraccion"].search([], limit=1).porcentaje
            record.detraccion_porcen=record.detraccion_id.porcentaje
    # #@api.one 
    # def _set_invoice_type_code(self):
    #     prueba = self.journal_id.invoice_type_code_id
    #     return prueba

    invoice_type_code = fields.Char(string="Tipo de Comprobante", default="01")

    def set_xml_filename(self):
        self.documentoXMLcliente_fname = str(self.number) + ".xml"

    def _compute_zip(self):
        self.documentoRespuestaZip = ET.fromstring(str(self.documentoRespuesta))[1][0][
            0
        ].text

    def _compute_number_begin(self):
        if self.number:
            if "F" in self.number:
                return True
            else:
                return False

    @api.onchange("operacionTipo")
    def validacion_afectacion(self):
        if self.type == "out_invoice":
            if self.invoice_line_ids:
                for line in self.invoice_line_ids:
                    if self.operacionTipo == "0200":
                        line.tipo_afectacion_igv = 16
                    else:
                        line.tipo_afectacion_igv = 1

    @api.onchange("muestra")
    def comment_gratutito(self):
        if self.type == "out_invoice":
            if self.muestra == True:
                self.comment = "Por transferencia a título gratuito de muestras."
                afectacion = 17
            else:
                self.comment = ""
                afectacion = 1

            if self.invoice_line_ids:
                for line in self.invoice_line_ids:
                    line._compute_price()
                    line.tipo_afectacion_igv = afectacion

    ## MODIFICACIONES DANIEL
    def enviar_correo(self):
        template = self.env.ref("account.email_template_edi_invoice", False)
        mail_id = self.env["mail.template"].sudo().browse(template.id).send_mail(self.id)
        mail = self.env["mail.mail"].sudo().browse(mail_id)
        mail.send()

    ## MODIFICACION DANIEL

    def _list_reference_code_credito(self):
        catalogs = self.env["einvoice.catalog.09"].search([])
        list = []
        for cat in catalogs:
            list.append((cat.code, cat.name))
        return list

    def _list_reference_code_debito(self):
        catalogs = self.env["einvoice.catalog.10"].search([])
        list = []
        for cat in catalogs:
            list.append((cat.code, cat.name))
        return list

    response_code_credito = fields.Selection(
        string="Código de motivo", selection=_list_reference_code_credito
    )
    response_code_debito = fields.Selection(
        string="Código de motivo", selection=_list_reference_code_debito
    )
    ##################################### 
    ###################################### 
    
    @api.returns("self")
    def refund(self, date_invoice=None, date=None, description=None, journal_id=None):
        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self._prepare_refund(
                invoice,
                date_invoice=date_invoice,
                date=date,
                description=description,
                journal_id=journal_id,
            )
            refund_invoice = self.create(values)
            invoice_type = {
                "out_invoice": ("customer invoices refund"),
                "in_invoice": ("vendor bill refund"),
            }
            message = _(
                "This %s has been created from: <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>"
            ) % (invoice_type[invoice.type], invoice.id, invoice.number)
            refund_invoice.message_post(body=message)
            new_invoices += refund_invoice
        return new_invoices

    

    @api.model
    def default_get(self, fields_list):
        res = super(accountInvoice, self).default_get(fields_list)

        journal_id = self.env["account.journal"].search(
            [["invoice_type_code_id", "=", self._context.get("type_code")]], limit=1
        )
        res["journal_id"] = journal_id.id
        return res

    
    #@api.multi
    def firmar(self):  #hace la firma
        #data_unsigned = ET.fromstring(self.documentoXML.encode("utf-8").strip()) 
        data_unsigned = ET.fromstring(self.documentoXML.encode("utf-8").strip())
        #ET.tostring(signed_root).decode("utf-8")
        #xml_file = xml_file.encode("utf-8")
        #self.documentoXMLcliente = base64.b64encode(xml_file)
        #
        namespaces = {
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "ccts": "urn:un:unece:uncefact:documentation:2",
            "ds": "http://www.w3.org/2000/09/xmldsig#",
            "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
            "qdt": "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2",
            "sac": "urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1",
            "udt": "urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }#
        

        if self.invoice_type_code == "01" or self.invoice_type_code == "03":
            if self.type == "out_invoice":
                namespaces.update(
                    {"": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"}
                )
            elif self.type == "out_refund":
                namespaces.update(
                    {"": "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"}
                )
        elif self.invoice_type_code == "07":
            namespaces.update(
                {"": "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"}
            )
        elif self.invoice_type_code == "08":
            namespaces.update(
                {"": "urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2"}
            )
        else : 
            if self.type == "out_invoice":
                namespaces.update(
                    {"": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"}
                )
            elif self.type == "out_refund":
                namespaces.update(
                    {"": "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"}
                )

        #
        for prefix, uri in namespaces.items():#iteritems  items viewitems
            ET.register_namespace(prefix, uri) #no esta funcionando 
            #ET._namespace_map[uri] = prefix
            #ET.register_namespace("20521467984-False-FV/2020/0032.xml", "/var/lib/odoo/")#20521467984-False-FV/2020/0032.xml

        uri = "/var/lib/odoo/"  #
        
        #lis_numer=str(self.number).split("/")
        name_file = (
            self.company_id.partner_id.vat
            + "-" + str(self.invoice_type_code) + "-" + str(self.number)
        )
        #+ "-" + str(self.invoice_type_code) + "-" + str(self.number)
        #+ str(lis_numer[2]) 
        file = open(uri + name_file + ".xml", "w")#name_file=20521467984-False-FV/2020/0036.xml  + name_file  

        signed_root = XMLSigner(
            method=methods.enveloped,
            digest_algorithm="sha1",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        ).sign(
            data_unsigned,
            key=str(self.company_id.private),
            cert=str(self.company_id.public),
        )

        signed_root[0][0][0][0].set("Id", "SignatureMT")

        self.digestvalue = signed_root[0][0][0][0][0][2][2].text
        #element = ET.fromstring(signed_root)  
        #file.write(tostring(element))#str(ET.tostring(signed_root))  ET.tostring(signed_root)
        file.write(ET.tostring(signed_root).decode("utf-8"))
        file.close()

        xfile = open(uri + name_file + ".xml", "r")
        xml_file = xfile.read()
        xml_file = xml_file.encode("utf-8")
        self.documentoXMLcliente = base64.b64encode(xml_file) #str(xml_file) 
        xfile.close()

        zf = zipfile.ZipFile(uri + name_file + ".zip", mode="w")
        try:
            zf.write(uri + name_file + ".xml", arcname=name_file + ".xml")
        except Exception:
            zf.close()
        zf.close()

        f = open(uri + name_file + ".zip", "rb")
        data_file = f.read()
        self.documentoZip = base64.b64encode(data_file)
        self.documentoXML = ET.tostring(signed_root)

        f.close()

        FacturaObject = Factura.Factura()
        EnvioXML = FacturaObject.sendBill(
            username=self.company_id.partner_id.vat + self.company_id.sunat_username,
            password=self.company_id.sunat_password,
            namefile=name_file + ".zip",
            contentfile=str(self.documentoZip),
        )
        self.documentoEnvio = EnvioXML.toprettyxml("        ")

    #@api.multi
    def enviar(self):
        url = self.company_id.send_route

        r = requests.post(
            url=url,
            data=self.documentoEnvio,
            headers={"Content-Type": "text/xml"},
            verify=False,
        )

        try:
            self.documentoRespuestaZip = ET.fromstring(r.text)[0][0][0].text
        except Exception:
            self.documentoRespuestaZip = "" 

        self.documentoRespuesta = r.text

    #@api.multi
    def descargarRespuesta(self):
        name_file = (
            "R-"
            + self.company_id.partner_id.vat
            + "-"
            + str(self.journal_id.invoice_type_code_id)
            + "-"
            + str(self.number)
        )
        url = self.env["ir.config_parameter"].search([["key", "=", "web.base.url"]])[
            "value"
        ]
        file_url = (
            url
            + "/web/content/account.move/"
            + str(self.id)
            + "/documentoRespuestaZip/"
            + name_file
            + ".zip"
        )
        return {"type": "ir.actions.act_url", "url": file_url, "target": "new"}

    # Llamar desde cronjob para pasar number ==> numeracion
    def number_to_numeracion(self):
        facturas = self.search([])
        for f in facturas:
            f.numeracion = f.number

    # Llamar desde cronjob para realizar consulta masiva a SUNAT
    def _envio_masivo(self):
        facturas = self.search(
            [
                ["codigoretorno", "=", False],
                ["state", "in", ["open", "paid"]],
                ["journal_id.invoice_type_code_id", "=", "01"],
            ]
        )
        for f in facturas:
            FacturaObject = Factura.Factura()
            EnvioXML = FacturaObject.getStatus(
                username=str(f.company_id.sunat_username),
                password=str(f.company_id.sunat_password),
                ruc=str(f.company_id.partner_id.vat),
                tipo=str(f.invoice_type_code),
                numero=f.number,
            )
            f.documentoEnvioTicket = EnvioXML.toprettyxml("        ")

            url = "https://www.sunat.gob.pe/ol-it-wsconscpegem/billConsultService"

            r = requests.post(
                url=url, data=f.documentoEnvioTicket, headers={"Content-Type": "text/xml"}
            )

            f.mensajeSUNAT = ET.fromstring(r.text.encode("utf-8"))[0][0][0][1].text
            f.codigoretorno = ET.fromstring(r.text.encode("utf-8"))[0][0][0][0].text

            if f.codigoretorno in ("0001", "0002", "0003"):
                f.estado_envio = True

    # Genera XML para consulta a SUNAT
    #@api.multi
    def estadoTicket(self):
        FacturaObject = Factura.Factura()
        EnvioXML = FacturaObject.getStatus(
            username=str(self.company_id.sunat_username),
            password=str(self.company_id.sunat_password),
            ruc=str(self.company_id.partner_id.vat),
            tipo=str(self.invoice_type_code),
            numero=self.number,
        )
        self.documentoEnvioTicket = EnvioXML.toprettyxml("        ")
        self.enviarTicket()

    # Envia consulta a SUNAT
    #@api.multi
    def enviarTicket(self):
        # url = "https://www.sunat.gob.pe/ol-it-wsconscpegem/billConsultService"
        url = "https://e-factura.sunat.gob.pe/ol-it-wsconscpegem/billConsultService"

        r = requests.post(
            url=url,
            data=self.documentoEnvioTicket,
            headers={"Content-Type": "text/xml"}
        )

        self.mensajeSUNAT = ET.fromstring(r.text.encode("utf-8"))[0][0][0][1].text
        self.codigoretorno = ET.fromstring(r.text.encode("utf-8"))[0][0][0][0].text

        if self.codigoretorno in ("0001", "0002", "0003"):
            self.estado_envio = True

    # Validacion de documento
    #@api.multi
    def action_invoice_open(self):#cambio

        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != "open")
        if to_open_invoices.filtered(lambda inv: inv.state not in ["proforma2", "draft"]):
            raise UserError(
                _("Invoice must be in draft or Pro-forma state in order to validate it.")
            )
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()

        if self.type == "out_refund":
            self.invoice_type_code = "07"
        else:
            self.invoice_type_code = self.journal_id.invoice_type_code_id

        if self.journal_id.invoice_type_code_id:
            if self.invoice_type_code in ("01", "03"):
                if self.type == "out_invoice":
                    self.generarFactura()
                elif self.type == "out_refund":
                    self.generarNotaCredito()
            elif self.invoice_type_code == "07":
                self.generarNotaCredito()
            elif self.invoice_type_code == "08":
                self.generarNotaDebito()
            elif self.invoice_type_code == "09":
                self.generarGuiaRemision()

            self.firmar()

        response = to_open_invoices.invoice_validate()

        self.numeracion = self.number
        return response

    # line = super(SaleOrderLine, self).create(values)
    def elimina_tildes(self, cadena):
        #s = ''.join((c for c in unicodedata.normalize('NFD',unicode(cadena)) if unicodedata.category(c) != 'Mn'))
        s=unicodedata.normalize('NFKD', cadena).encode('ascii','ignore')
        return s

    