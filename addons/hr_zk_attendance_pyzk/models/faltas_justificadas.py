# -*- coding: utf-8 -*-
###################################################################################
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import pytz
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

class ZkMachine(models.Model):
    _name = 'faltas.justificadas'
    
    name = fields.Char(string='Descripcion', required=True)
    motivo = fields.Many2one('motivo.falta', string='Motivo de la falta')
    autorizado_por = fields.Many2one('res.users', 'Autorizado Por')
    empleado = fields.Many2one('hr.employee', 'Empleado')
    fechainicio =  fields.Date(string='Fecha de inicio')
    fechafin =  fields.Date(string='Fecha de finalizacion')