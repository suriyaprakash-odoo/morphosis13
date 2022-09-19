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


class IncomingShipmentReport(models.TransientModel):
    _name = 'incoming.shipment.report'

    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')


    def view_incoming_shipment_report(self):
        shipment_obj = self.env['stock.picking'].search([('entry_date_time', '<=', self.to_date),('entry_date_time', '>=', self.from_date),('picking_type_code', '=', 'incoming')])

        incoming_shipment_report = []
        for shipment in shipment_obj:
            container_obj = self.env['project.container'].search([('picking_id', '=', shipment.id)])
            rc_obj = self.env['stock.container'].search([('picking_id', '=', shipment.id)])
            if container_obj:
                for container in container_obj:
                    incoming_shipment_report_obj = self.env['incoming.shipment.wizard.report'].create({
                            'project_name' : container.project_id.name,
                            'shipment_name' : container.picking_id.name,
                            'donor_container_name' : container.name,
                            'recipent_container_name' : '',
                            'container_type_name' : container.sub_product_id.name,
                            'gross_weight' : container.gross_weight,
                            'net_weight' : container.net_gross_weight
                        })
                    incoming_shipment_report.append(incoming_shipment_report_obj.id)
            if rc_obj:
                for rc in rc_obj:
                    incoming_shipment_report_obj = self.env['incoming.shipment.wizard.report'].create({
                            'project_name' : rc.project_id.name,
                            'shipment_name' : rc.picking_id.name,
                            'donor_container_name' : '',
                            'recipent_container_name' : rc.name,
                            'container_type_name' : rc.content_type_id.name,
                            'gross_weight' : rc.gross_weight,
                            'net_weight' : rc.net_weight
                        })
                    incoming_shipment_report.append(incoming_shipment_report_obj.id)


        return {
            'name': "Incoming Report",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'incoming.shipment.wizard.report',
            'target': 'current',
            'domain': [('id', '=', [x for x in incoming_shipment_report])],
            'views_id':False,
            'views':[(self.env.ref('ppts_project_entries.incoming_shipment_report_tree_view').id or False, 'tree')],
        }


class IncomingShipmentWizardReport(models.TransientModel):
    _name = 'incoming.shipment.wizard.report'

    project_name = fields.Char(string="Project")
    shipment_name = fields.Char(string='Shipment')
    donor_container_name = fields.Char(string='Donor Container')
    recipent_container_name = fields.Char(string='Recipient Container')
    container_type_name = fields.Char(string="Content Type")
    gross_weight = fields.Float(string='Gross Weight')
    net_weight = fields.Float(string='Net Weight')