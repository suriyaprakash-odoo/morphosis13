from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError

class LogisticsManagement(models.Model):
    _inherit = 'logistics.management'

    refining_containers = fields.One2many("refining.containers","logistics_id", string="Refining Containers")
    is_refining = fields.Boolean("Is Refining")

class RefiningContainers(models.Model):
    _inherit = 'refining.containers'

    logistics_id = fields.Many2one("logistics.management")

