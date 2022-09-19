from odoo import fields, models, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    precious_metal = fields.Selection([
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('palladium', 'Palladium'),
        ('platinum', 'Platinum'),
        ('copper', 'Copper'),
        ('rhodium', 'Rhodium'),
        ('ruthenium', 'Ruthenium'),
        ('iridium', 'Iridium')
    ], string='Precious Metal')

    is_metal = fields.Boolean(related='categ_id.is_metal', string= "Metal")
    reuse_container = fields.Boolean(related='categ_id.reuse_container', string="Reusable Container")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    precious_metal = fields.Selection([
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('palladium', 'Palladium'),
        ('platinum', 'Platinum'),
        ('copper', 'Copper'),
        ('rhodium', 'Rhodium'),
        ('ruthenium', 'Ruthenium'),
        ('iridium', 'Iridium')
    ], string='Precious Metal')

    is_metal = fields.Boolean(related='categ_id.is_metal', string= "Metal")
    reuse_container = fields.Boolean(related='categ_id.reuse_container', string="Reusable Container")

class ProductTemplate(models.Model):
    _inherit = 'product.category'

    is_metal = fields.Boolean("Is Metal?")
    precious_location_id = fields.Many2one("stock.location", string="Metal Location")
    reuse_container = fields.Boolean("Reusable Container")