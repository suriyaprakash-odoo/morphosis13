from odoo import fields, models, api, _
from odoo.exceptions import UserError
import base64
import io
import itertools

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
from datetime import datetime


class OutgoingShipmentReport(models.TransientModel):
    _name = 'outgoing.shipment.report'

    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')


    def view_outgoing_shipment_report(self):
        shipment_obj = self.env['stock.picking'].search([('sale_logistics_exit_date_time', '<=', self.to_date),('sale_logistics_exit_date_time', '>=', self.from_date),('picking_type_code', '=', 'outgoing'),('state', '=', 'done')])

        outgoing_shipment_report = []
        container_id = []
        for shipment in shipment_obj:
            for line in shipment.move_ids_without_package:
                for container in line.container_ids:
                    if container.id not in container_id:
                        container_id.append(container.id)
            # container_obj = self.env['project.container'].search([('picking_id', '=', shipment.id)])
            # rc_obj = self.env['stock.container'].search([('picking_id', '=', shipment.id)])
        for con_id in container_id:
            container_obj = self.env['stock.container'].browse(int(con_id))
            if container_obj:
                for container in container_obj:
                    move_obj = self.env['stock.move'].search([('container_ids', 'in', container.id)], limit=1)
                    print('---',move_obj.picking_id.name,'---')
                    outgoing_shipment_report_obj = self.env['outgoing.shipment.wizard.report'].create({
                            'sale_order_name' : move_obj.picking_id.origin,
                            'shipment_name' : move_obj.picking_id.name,
                            'recipent_container_name' : container.name,
                            'content_type_name' : container.content_type_id.name,
                            'gross_weight' : container.gross_weight,
                            'net_weight' : container.net_weight
                        })
                    outgoing_shipment_report.append(outgoing_shipment_report_obj.id)

        return {
            'name': "Outgoing Report",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'outgoing.shipment.wizard.report',
            'target': 'current',
            'domain': [('id', '=', [x for x in outgoing_shipment_report])],
            'views_id':False,
            'views':[(self.env.ref('ppts_project_entries.outgoing_shipment_report_tree_view').id or False, 'tree')],
        }


class OutgoingShipmentWizardReport(models.TransientModel):
    _name = 'outgoing.shipment.wizard.report'

    sale_order_name = fields.Char(string="Sale Order")
    shipment_name = fields.Char(string='Shipment')
    donor_container_name = fields.Char(string='Donor Container')
    recipent_container_name = fields.Char(string='Recipient Container')
    content_type_name = fields.Char(string="Content Type")
    gross_weight = fields.Float(string='Gross Weight')
    net_weight = fields.Float(string='Net Weight')