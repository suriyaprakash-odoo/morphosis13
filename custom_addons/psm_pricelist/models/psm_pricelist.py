from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError

class PsmPricelist(models.Model):
    _name = 'psm.pricelist'
    _description = 'Morphosis PSM Pricelists'

    name = fields.Char("Name")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("Date End")
    active = fields.Boolean("Active?", default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    pricelist_line = fields.One2many("psm.pricelist.lines","pricelist_id", string="Pricelist Line")


class PricelistProducts(models.Model):
    _name = 'psm.pricelist.lines'

    product_id = fields.Many2one("product.product", string="Product")
    price = fields.Float("Price")
    pricelist_id = fields.Many2one("psm.pricelist")



class UpdatePurchaseWizard(models.TransientModel):
    _inherit = "update.purchase.order"

    psm_pricelist = fields.Many2one("psm.pricelist",string="PSM Pricelist")

    @api.onchange('psm_pricelist')
    def onchange_psm_pricelist(self):
        if self.psm_pricelist:
            if self.non_po_line_ids:
                print(len(self.non_po_line_ids))
                for line in self.non_po_line_ids:
                    price_line = self.env["psm.pricelist.lines"].search([('product_id','=',line.product_id.id),('pricelist_id','=',self.psm_pricelist.id)])
                    print(price_line.price)
                    line.offer_price = price_line.price
