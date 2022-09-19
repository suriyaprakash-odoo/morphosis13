from odoo import api, fields, models


class CloseFractionWizard(models.TransientModel):
    _name = 'close.fraction.wizard'

    container_id = fields.Many2one("project.container", string="Source Container")
    fraction_line = fields.One2many("close.fractions.line", "wizard_id", string="Fractions")
    select_all = fields.Boolean("Select All")

    @api.onchange('select_all')
    def _onchange_select_all(self):
        if self.fraction_line:
            if self.select_all:
                for line in self.fraction_line:
                    line.close = True
            else:
                for line in self.fraction_line:
                    line.close = False

    def action_close_fractions_line(self):
        for fraction in self.fraction_line:
            if fraction.close:
                fraction.fraction_id.close_fraction()



class FractionsLine(models.TransientModel):
    _name = 'close.fractions.line'

    fraction_id = fields.Many2one("project.fraction",string="Fraction ID")
    main_product_id = fields.Many2one("product.template", string="Primary Type")
    sub_product_id = fields.Many2one("product.product", string="Secondary Type")
    fraction_weight = fields.Float("Fraction Weight(Kg)", digits=(12, 4))
    number_of_pieces = fields.Integer("Number of pieces")
    recipient_container_id = fields.Many2one("stock.container", "Destination Container")
    wizard_id = fields.Many2one("close.fraction.wizard",string="Wizard ID")
    close = fields.Boolean("Close?")