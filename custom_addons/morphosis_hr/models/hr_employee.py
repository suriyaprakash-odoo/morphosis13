from odoo import fields, models, api, _


class Employee(models.Model):
    _inherit = 'hr.employee'

    is_worker = fields.Boolean('Is a Worker')
    is_supervisor = fields.Boolean('Is a Supervisor')


class EmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    is_worker = fields.Boolean('Is a Worker')
    is_supervisor = fields.Boolean('Is a Supervisor')
