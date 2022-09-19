from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning


class UpdateChronopost(models.TransientModel):
    _name = "update.chronopost.bulk"

    barcode = fields.Char("Barcode")
    line_ids = fields.One2many("chronopost.bulk.line","chronopost_line_id",string="Chronopost Lines")

    @api.onchange('barcode')
    def onchange_barcode(self):
        if self.barcode:
            chronopost_line = self.env["carton.line"].search([('name','=',self.barcode)])
            for line in chronopost_line:
                shipping_id = self.env["stock.picking"].search([('project_entry_id','=',line.carton_id.id),('state','=','assigned'),('is_registered_package','=',True)],limit=1)
                container_id = self.env["project.container"].search([('chronopost_number','=',line.id)],limit=1)
                dest_location_id = self.env['stock.location'].search([('chronopost_location', '=', True), ('company_id', '=', shipping_id.company_id.id)], limit=1)
                transport = self.env['res.partner'].search([('is_chronopost', '=', True)], limit=1)
                container_line_list = []
                container_line_list.append((0, 0, {
                    'project_id': line.carton_id.id,
                    'container_id': container_id.id,
                    'not_received': container_id.not_received,
                    'not_received_reason': container_id.not_received_reason,
                    'have_batteries': container_id.have_batteries,
                    'batteries_weight': container_id.batteries_weight,
                    'shipping_id':shipping_id.id,
                    'chronopost_number': line.name,
                    'source_location_id': shipping_id.location_id.id,
                    'destination_location_id': dest_location_id.id,
                    'logistics_partner_id':transport.id
                }))

                self.line_ids = container_line_list

    def register_chronopost_bulk(self):
        if self.line_ids:
            for line in self.line_ids:

                if (not line.batteries_weight) and line.have_batteries:
                    raise Warning("Please fill the batteries Weight")

                line.shipping_id.transporter_partner_id = line.logistics_partner_id.id

                if not line.not_received:
                    line.container_id.location_id = line.destination_location_id.id
                else:
                    line.container_id.state = 'close'

                line.container_id.not_received = line.not_received
                line.container_id.not_received_reason = line.not_received_reason
                line.container_id.have_batteries = line.have_batteries
                line.container_id.batteries_weight = line.batteries_weight
 
                line.shipping_id.state = 'production'

        return {'type': 'ir.actions.act_window_close'}

class ChronopostContainerLine(models.TransientModel):
    _name = "chronopost.bulk.line"

    project_id = fields.Many2one("project.entries", string="Project")
    container_id = fields.Many2one('project.container', string="Container")
    shipping_id = fields.Many2one("stock.picking", string="Shipment ID")
    chronopost_number = fields.Char('Chronopost Barcode')
    source_location_id = fields.Many2one('stock.location', string='Source', domain="[('usage','=','internal'),('chronopost_location','=',True)]")
    destination_location_id = fields.Many2one('stock.location', string='Destination', domain="[('usage','=','internal'),('chronopost_location','=',True)]")
    chronopost_line_id = fields.Many2one('update.chronopost.bulk', string='Chronopost ref')
    logistics_partner_id = fields.Many2one('res.partner', string='Transporter', domain="[('is_chronopost', '=', True)]")
    
    not_received = fields.Boolean('Not Received')
    not_received_reason = fields.Char('Reason')
    have_batteries = fields.Boolean('Batteries')
    batteries_weight = fields.Float('Batteries Weight', digits=(12,4))
    # barcode_available = fields.Boolean("Barcode Available")