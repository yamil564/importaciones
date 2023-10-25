# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class VehicleSaleOrder(models.Model):
    _inherit = 'stock.picking'

    #transportista = fields.Many2one('transport.transportista', string="Conductor", required=True,default=lambda self: self.env['transport.transportista'].search([],limit=1))
    entreg_tercero = fields.Boolean(default=False,string="Entregar a Terceros")
    tercera_persona = fields.Many2one('res.partner', string="Tercero")
    puerto_embar=fields.Many2one('puerto.aeropuerto.embarque', string="Puerto/aeropuerto de embarque")
    puerto_desembar=fields.Many2one('puerto.aeropuerto.desembarque', string="Puerto/aeropuerto de desembarque")
    contenedor=fields.Many2one('transport.contenedor', string="Datos del Contenedor")
    transport_date = fields.Date(string="Fecha de inicio del traslado",default=lambda self: fields.Datetime.now(), required=True)#default=lambda self: self.min_date
    motivo_traslado=fields.Many2one('einvoice.catalog.20', string="Motivo del Traslado", required=True, default=lambda self: self.env['einvoice.catalog.20'].search([],limit=1))
    modalidad_traslado=fields.Many2one('einvoice.catalog.18', string="Modalidad del Traslado", required=True, default=lambda self: self.env['einvoice.catalog.18'].search([],limit=1))
    Indicador_de_transbordo=fields.Boolean(default=False, string="¿Transbordo programado?") 
    #peso_bruto = fields.Char(string="Peso bruto total de la GRE")
    #unidad_peso_bruto = fields.Many2one('einvoice.catalog.03', string="Unidad de medida del peso bruto total de la GRE")
    descripcion_motivo_traslado = fields.Char(default="-",string="Descripcion de motivo de Traslado")#Orden de entrega 
    required_condition=fields.Boolean(default=False, string="required condition") 
    
    #@api.multi
    @api.onchange('motivo_traslado')
    def onchange_motivo_tras(self):
        for rec in self:
            if rec.motivo_traslado.code=='08':
                rec.required_condition = True
            else:
                rec.required_condition = False
    

class DatosDelContenedor(models.Model):
    _name = 'transport.contenedor'

    name = fields.Char(string="Numero de Contenedor", required=True)
    Descripcion = fields.Char(string="Descripcion")