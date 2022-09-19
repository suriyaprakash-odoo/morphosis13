from odoo import fields, models, api, _
from odoo.exceptions import UserError

class FractionTemplate(models.Model):
    _name = 'fraction.template'

    name = fields.Char("Template Name")
    main_product_id = fields.Many2one("product.template", string="Primary Type")
    product_ids = fields.Many2many("product.product", string="Secondary Type")


# class FractionTemplateLine(models.Model):
#     _name = "fraction.template.line"
#
#     product_id = fields.Many2one("product.product", string="Secondary Type")