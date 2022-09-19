from odoo import fields, models, api, _
from datetime import datetime
import xlwt
import base64
from odoo.exceptions import UserError

class ProjectDocs(models.Model):
    _name = 'project.docs'

    name = fields.Char("Document Description", required=True)
    project_file = fields.Binary("Document", required=True)
