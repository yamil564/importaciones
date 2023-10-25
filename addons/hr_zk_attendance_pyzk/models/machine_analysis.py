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

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    device_id = fields.Char(string='ID de dispositivo biométrico') 
    empresa = fields.Char(string='Empresa')  
    descuentohora = fields.Char(string='Descuento x Hora',compute='_get_descuento',inverse='_set_descuento',store=True)
    sueldo = fields.Char(string='Sueldo')
    
    #debe ser 1500 debe ser 6.25
    #l-v 8:30 , s 4:30 , acomodar sabado a 5 dias l-v = 9 horas
    # 9 horas x26 dias(mensual) = 234 horas mensual
    #su sueldo es "S" la tardanza por hora es "S"/234 
    ##@api.one
    #nuevo: 8 horas por 30 dias= "S"/240
    @api.depends('sueldo')
    def _get_descuento(self):
        #for record in self:
        #    record.descuentohora = str(float(record.sueldo)/234)
        for record in self:
            if record.sueldo:
                record.descuentohora = str(round(float(record.sueldo)/240,2))

    def _set_descuento(self):
        pass

    @api.constrains('device_id')
    def check_unique_deviceid(self):
        records = self.env['hr.employee'].search([('device_id', '=', self.device_id),('device_id', '!=', False ),('id', '!=', self.id)])
        if records:
            raise UserError(_('Ya existe otro usuario con el mismo ID de dispositivo biométrico.'))


class ZkMachine(models.Model):
    _name = 'zk.machine.attendance'
    _inherit = 'hr.attendance'
    _order = 'punching_time desc'

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """overriding the __check_validity function for employee attendance."""
        pass

    device_id = fields.Char(string='ID de dispositivo biométrico')
    punch_type = fields.Selection([('0', 'Check In'),
                                   ('1', 'Check Out'),
                                   ('2', 'Break Out'),
                                   ('3', 'Break In'),
                                   ('4', 'Overtime In'),
                                   ('5', 'Overtime Out')],
                                  string='Tipo de marcacion')

    #attendance_type = fields.Selection([('1', 'Finger'),
    #                                    ('15', 'Face'),
    #                                    ('2','Type_2'),
    #                                    ('3','Password'),
    #                                    ('4','Card')], string='Categoria')
    punching_time = fields.Datetime(string='Fecha- Hora - Ingreso y Salida')
    address_id = fields.Many2one('res.partner', string='Dirección de trabajo')
    prueba=fields.Char(string='Prueba')
    permiso = fields.Many2one('motivo.falta', string='Motivo')

    #tengo el listado de fechas, si alguna de ellas no se encuentra en la asistencia
    #de un usuario se agregara, a traves de un cront todos los dias en la noche
    #lista_fechas = [(inicio + timedelta(days=d)).strftime("%Y-%m-%d")
    #                for d in range((fin - inicio).days + 1)] 
    #print(lista_fechas)
    #se tiene que seleccionar todos los usuarios, luego recorro cada uno de ellos
    #luego recorro las fechas de cada uno de ellos


class ReportZkDevice(models.Model):
    _name = 'zk.report.daily.attendance'
    _auto = False
    _order = 'punching_time desc'

    name = fields.Many2one('hr.employee', string='Empleado')
    punching_day = fields.Date(string='Fecha actualizacion')
    address_id = fields.Many2one('res.partner', string='Dirección de trabajo')
    #attendance_type = fields.Selection([('1', 'Dedo'),
    #                                    ('15', 'Cara'),('2','Type_2'),('3','Contraseña'),
    #                                    ('4','Tarjeta')],string='Categoria')
    punch_type = fields.Selection([('0', 'Registrarse'),
                                   ('1', 'Check Out'),
                                   ('2', 'Break Out'),
                                   ('3', 'Break In'),
                                   ('4', 'Entrada de tiempo extra'),
                                   ('5', 'Tiempo extra fuera')], string='Tipo de marcacion')
    punching_time = fields.Datetime(string='Fecha- Hora - Ingreso y Salida')
    punching_date = fields.Date(string='Fecha')

    fechai=fields.Datetime(string='Hora I')
    fechas=fields.Datetime(string='Hora S')
    horasTardanza = fields.Char(string='Horas Tardanza', compute="_compute_time")
    tardanza = fields.Char(string='Tardanza', compute="_compute_time")
    timei = fields.Char(string='Hora Ingreso', compute="_compute_time")
    times = fields.Char(string='Hora Salida', compute="_compute_time")
    total = fields.Char(string='Total S/.', compute="_compute_time")
    descuentohora = fields.Char(string='Precio/Hora')
    tolerancia = fields.Selection([('1', 'Temprano'),
                                        ('2', 'Tolerable'),
                                        ('3','Tarde'),
                                        ('4','Falto'),
                                        ('5','Permiso')],string='Tolerancia',compute="_compute_time")
    empresa = fields.Char(string='Empresa')
    permiso = fields.Many2one('motivo.falta', string='Motivo')
    
    def _compute_time(self):
        for record in self:
            time_local = 'America/Lima'
            time_fmt = "%Y-%m-%d %H:%M:%S"
            #raise UserError(record.permiso)
            if record.fechai:
                arrive_dt=datetime.strptime(record.fechai, DEFAULT_SERVER_DATETIME_FORMAT)
                testDt=pytz.utc.localize(arrive_dt)
                TestDt = testDt.astimezone(pytz.timezone(time_local))
                #Arrive=TestDt.strftime(time_fmt)
                Arrive=record.fechai
                record.timei = Arrive[10:]
                Left=record.fechas
                record.times = Left[10:]
                #calcular las horas de tardanza
                record.tolerancia='1'
                hora='0'
                minuto='00'
                segundo='00'
                if int(Arrive[10:13])>=8:
                    hora=abs(int(Arrive[10:13])-8)
                    if int(Arrive[14:16])>=30 and int(Arrive[14:16])<=35:
                        minuto='00'
                        segundo='00'
                        record.tolerancia='2'
                    elif int(Arrive[14:16])>35 :
                        minuto=abs(int(Arrive[14:16])-30)
                        segundo=abs(int(Arrive[17:19])-60)
                        record.tolerancia='3'
                elif int(Arrive[10:13])==0:
                    record.tolerancia='4'
                tardanza=str(hora)+':'+str(minuto)+':'+str(segundo)
                if int(Arrive[10:13])>=8:
                    if int(Arrive[14:16])>=35:
                        hora=hora+1
            if record.permiso:
                record.tolerancia='5'
            record.horasTardanza=hora
            record.tardanza=tardanza
            record.total=float(record.descuentohora)*int(hora)

    #z.punching_time as punching_time,
    #ORDER BY z.punching_time DESC;
    #ProgrammingError: column e.descuentohora does not exist --> por uso de mayuscula
    def init(self):
        tools.drop_view_if_exists(self._cr, 'zk_report_daily_attendance')
        self._cr.execute("""
            create or replace view zk_report_daily_attendance as (
                select
                    min(z.id) as id,
                    z.employee_id as name,
                    z.write_date as punching_day,
                    z.address_id as address_id,
                    split_part(array_to_string(array_agg(z.punching_time ORDER BY z.punching_time), ',') , ',', 1) as fechai,
                    split_part(array_to_string(array_agg(z.punching_time ORDER BY z.punching_time), ',') , ',', 2) as fechas,
                    date(z.punching_time)  as punching_time,
                    date(z.punching_time)  as punching_date,
                    z.punch_type as punch_type,
                    z.permiso as permiso,
                    e.descuentohora as descuentohora,
                    e.empresa as empresa
                from zk_machine_attendance z
                    join hr_employee e on (z.employee_id=e.id)
                GROUP BY
                    z.employee_id,
                    date(z.punching_time),
                    z.write_date,
                    z.address_id,
                    e.descuentohora,
                    z.punch_type,
                    z.permiso,
                    e.empresa
            )
        """)


