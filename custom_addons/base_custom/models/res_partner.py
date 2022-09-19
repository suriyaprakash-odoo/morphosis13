from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_transporter = fields.Boolean('Is Transporter')
    short_code = fields.Char('Short Name', size=10)
    lot_sequence_number = fields.Integer('Lot Number', default="01")
    recipit = fields.Char('Récipissé')
    recipit_expiration = fields.Date("Date d'expiration")
    unknown_location = fields.Boolean("Unknown Location")
    is_prospect = fields.Boolean('Is Prospect')
    is_chronopost = fields.Boolean("Chronopost")


    client_d3e = fields.Boolean("Client D3E")

    morning_opening_hours_start = fields.Char('Morning Opening Hours Start')
    morning_opening_hours_end = fields.Char('Morning Opening Hours End')
    evening_opening_hours_start = fields.Char('Evening Opening Hours Start')
    evening_opening_hours_end = fields.Char('Evening Opening Hours End')

    is_tail_lift = fields.Boolean('Tail-Lift')
    hayons = fields.Selection([('hayons', 'Hayons'), ('hayons_t', 'Hayons + transpalette'),
                               ('hayons_te', 'Hayons + transpalette electrique')])
    
    grid_rotation = fields.Char('rotation de grille')

    client_ecologic = fields.Boolean(default=False, string="Client Ecologic")
    client_affinage = fields.Boolean(default=False, string="Client Affinage")