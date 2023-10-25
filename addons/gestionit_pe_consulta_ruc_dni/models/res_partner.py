# -*- coding: utf-8 -*-
from openerp import models, fields, api
from odoo.exceptions import UserError, ValidationError
import requests
import json
import logging
import re
_logger = logging.getLogger(__name__)

patron_ruc = re.compile("[12]\d{10}$")
patron_dni = re.compile("\d{8}$")


class ResPartner(models.Model):
    _inherit = "res.partner"

    registration_name = fields.Char('Name', size=128, index=True)
    estado_contribuyente = fields.Char(string='Estado del Contribuyente')
    msg_error = fields.Char(readonly=True)

    l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type',
                                                        string="Tipo de documento de identidad", index=True, auto_join=True,
                                                        default=lambda self: self.env.ref('gestionit_pe_consulta_ruc_dni.it_RUC', raise_if_not_found=False),
                                                        help="Tipo de documento de identidad")

    street_invoice_ids = fields.One2many("res.partner","parent_id",string="Facturación",domain=[("type","=","invoice")])
    street_delivery_ids = fields.One2many("res.partner","parent_id",string="Direcciones",domain=[("type","in",["delivery","other","private"])])

    @api.model
    def default_get(self,field_list):
        res = super(ResPartner, self).default_get(field_list)
        if self.env.context.get("no_doc"):
            res.update({"l10n_latam_identification_type_id": self.env.ref("l10n_pe.it_NDTD").id,"vat":res.get("vat","0")})
        return res

    def _get_name(self):
        partner = self
        name = partner.name or ''
        name = super(ResPartner, self)._get_name()
        if self._context.get("show_vat_first") and partner.vat:
            name = "%s ‒ %s" % (partner.vat, name)
        return name

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        return super(ResPartner, self).with_context(show_vat=True).onchange_partner_id()

    
    @api.model
    def _check_valid_ruc(self,ruc):
        if patron_ruc.match(ruc or ""):
            vat_arr = [int(c) for c in ruc]
            arr = [5,4,3,2,7,6,5,4,3,2]
            s = sum([vat_arr[r]*arr[r] for r in range(0,10)])
            num_ver = (11-s%11)%10
            if vat_arr[10] != num_ver:
                return False
        else:
            return False
        return True
    
    @api.constrains('name','vat','l10n_latam_identification_type_id','type')
    def _check_valid_numero_documento(self):
        for record in self:
            #if self.env.context.get("show_vat",False):
            vat_str = (record.vat or "").strip()
            vat_code = record.l10n_latam_identification_type_id.l10n_pe_vat_code
            if record.l10n_latam_identification_type_id and record.type in ["contact"] : #and not record.commercial_partner_id
                if vat_code == "6":
                    if not record._check_valid_ruc(vat_str):
                        raise UserError("El número de RUC ingresado es inválido.")
                if vat_code == "1":
                    if not patron_dni.match(vat_str):
                        raise UserError("El número de DNI ingresado es inválido")
                if vat_code == 'A':
                    if not bool(re.compile("\d{15}$").match(record.vat or '')):
                        raise UserError("El tipo de Documento CÉDULA DIPLOMÁTICA debe ser numérico y tener 15 dígitos.")   
                    
            if self.env.user.has_group('base.group_user') and self.env.user.active:
                if vat_code in ('A','1','4','5','6') and not record.parent_id:
                    customers = self.env['res.partner'].search([('vat', '!=', False),('vat', '!=', ''), ('vat', '=', vat_str), ('id', '!=', record.id)])
                    if customers.exists():
                        raise ValidationError('Ya existe un cliente con el mismo Número de Documento.')

                
    @api.model
    def create(self, values):
        if  self.env.context.get('show_vat',False) and not values.get("vat"):
            if self._check_valid_ruc(values.get("name")):
                values.update(l10n_latam_identification_type_id=self.env["l10n_latam.identification.type"].search([('l10n_pe_vat_code','=',"6")],limit=1).id,
                                vat=values.get("name"))
                res = super(ResPartner, self).create(values)
                res.update_document()
                return res
            
            if patron_dni.match(values.get("name")):
                values.update(l10n_latam_identification_type_id=self.env["l10n_latam.identification.type"].search([('l10n_pe_vat_code','=',"1")],limit=1).id,
                                vat=values.get("name"))
                res = super(ResPartner, self).create(values)
                res.update_document()
                return res

            if not (patron_dni.match(values.get("name")) or self._check_valid_ruc(values.get("name"))):
                values.update(l10n_latam_identification_type_id=self.env["l10n_latam.identification.type"].search([('l10n_pe_vat_code','=',"0")],limit=1).id)

        return super(ResPartner, self).create(values)
    

    @api.onchange("street","type")
    def get_name_street(self):
        if self.type == "delivery" and not self.name:
            self.name = self.street or "-"


    @api.onchange('l10n_latam_identification_type_id', 'vat')
    def vat_change(self):
        self.update_document()

    @api.model
    def request_migo_dni(self, dni):
        user_id = self.env.context.get('uid', False)
        if user_id:
            user = self.env["res.users"].sudo().browse(user_id)
            url = user.company_id.api_migo_endpoint + "dni"
            token = user.company_id.api_migo_token
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            data = {
                "token": token,
                "dni": dni
            }
            res = requests.request(
                "POST", url, headers=headers, data=json.dumps(data),timeout=3)
            res = res.json()

            if res.get("success", False):
                return res.get("nombre", False)
            return None
        except Exception as e:
            return None

    @api.model
    def request_migo_ruc(self, ruc):
        company = self.env.company
        errors = []

        if company:
            if not company.api_migo_endpoint:
                errors.append("Debe configurar el end-point del API")
            if not company.api_migo_token:
                errors.append("Debe configurar el token del API")
            if len(errors) > 0:
                raise UserError("\n".join(errors))
            else:
                url = company.api_migo_endpoint + "ruc"
                token = company.api_migo_token

                try:
                    headers = {
                        'Content-Type': 'application/json'
                    }
                    data = {
                        "token": token,
                        "ruc": ruc
                    }
                    res = requests.request("POST", url, headers=headers, data=json.dumps(data),timeout=3)
                    res = res.json()
                    if res.get("success", False):
                        return res
                    return None
                except Exception as e:
                    return None

        return None

    """
    @api.model
    def _esrucvalido(self, vat_str):
        if patron_ruc.match(vat_str) :
            vat_arr = [int(c) for c in vat_str]
            arr = [5,4,3,2,7,6,5,4,3,2]
            s = sum([vat_arr[r]*arr[r] for r in range(0,10)])
            num_ver = (11-s%11)%10
            if vat_arr[10] != num_ver:
                return False
            return True
        else:
            return False
    """
    def update_document(self):
        self.ensure_one()
        if not self.vat:
            return False
        else:
            self.vat = self.vat.strip()

        self.msg_error = ""
        if self.l10n_latam_identification_type_id.l10n_pe_vat_code == '1':
            #VALIDACIÓN DNI
            if not patron_dni.match(self.vat):
                self.msg_error = 'El DNI no tiene un formato válido. El formato de DNI consta de 8 números.'
                return False
            else:
                nombre_entidad = self.request_migo_dni(self.vat)
                if nombre_entidad:
                    self.name = nombre_entidad
                    self.company_type = "person"
                    self.registration_name = nombre_entidad
                    return True
                else:
                    self.name = " - "
                    self.registration_name = " - "
                    return False

        elif self.l10n_latam_identification_type_id.l10n_pe_vat_code == '6':
            #VALIDACIÓN RUC
            if not self._check_valid_ruc(self.vat):
                self.msg_error = "El RUC no tiene un formato válido."
                return False
            else:
                d = self.request_migo_ruc(self.vat)
                if not d or not d.get("success",False) or not d.get("nombre_o_razon_social",False) or not d.get("nombre_o_razon_social",False) != "":
                    self.name = " - "
                    self.msg_error = "El RUC no ha sido encontrado. Ingrese de forma manual los datos de la empresa."
                    return False
                
                ditrict_obj = self.env['res.country.state']
                dist_id = ditrict_obj.search([('code', '=', d['ubigeo'])], limit=1)

                self.estado_contribuyente = d['estado_del_contribuyente']
                self.name = d['nombre_o_razon_social']
                self.registration_name = d['nombre_o_razon_social']
                self.ubigeo = d["ubigeo"]
                self.street = d['direccion']
                self.is_company = True
                self.company_type = "company"
                
                if dist_id:
                    self.district_id = dist_id.id
                    self.province_id = dist_id.province_id.id
                    self.state_id = dist_id.state_id.id
                    self.country_id = dist_id.country_id.id
                return True
        return False

    def _onchange_country(self):
        return
