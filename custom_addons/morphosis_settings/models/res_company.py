from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    contract_rate = fields.Monetary('Contract Rate', currency_field='currency_id')
    ea_rate = fields.Monetary('EA Rate', currency_field='currency_id')
    standard_rate = fields.Monetary('Standard Rate', currency_field='currency_id')
    standard_unloading_rate = fields.Monetary('Unloading Charges', currency_field='currency_id')
    standard_reception_rate = fields.Monetary('Reception Charges', currency_field='currency_id')
 
    margin_percentage = fields.Integer('Sale Margin(%)')

    sale_margin_a = fields.Integer('Sals Margin A(%)')
    sale_margin_b = fields.Integer('Sals Margin B(%)')
    sale_margin_c = fields.Integer('Sals Margin C(%)')

    purchase_threshold_percentage = fields.Integer('Approval Threshold(%)')
    purchase_limit = fields.Integer("Purchase Limit")

    cross_dock_cost = fields.Monetary('Cross Dock Cost', currency_field='currency_id')
    vrac_cost = fields.Monetary('Vrac Cost', currency_field='currency_id')
    
    # dedection_percentage = fields.Float('Pourcentage restitution')
    # buy_price_discount = fields.Float('Pourcentage remise contre prix LME')

    tolerance_percentage = fields.Integer(string="Container Tolerance(%)")


class AccountJournal(models.Model):
    _inherit = "account.journal"

    code = fields.Char(string='Short Code', size=9, required=True, help="The journal entries of this journal will be named using this prefix.")