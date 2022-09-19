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


class EcologicReport(models.TransientModel):
    _name = 'ecologic.report'

    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')


    def view_ecologic_report(self):
        print(self.from_date,'--self.from_date--')
        print(self.to_date,'--self.to_date--')
        project_obj = self.env['project.entries'].search([('creation_date', '<=', self.to_date),('creation_date', '>=', self.from_date),('is_ecologic', '=', True)])

        print(project_obj,'--project_obj--')
        ecologic_report = []
        for project in project_obj:
            container_obj = self.env['project.container'].search([('project_id', '=', project.id)])
            stock_container_obj = self.env['stock.container'].search([('project_id', '=', project.id)])
            print(container_obj,'--container_obj--')
            if container_obj:
                for container in container_obj:
                    ecologic_report_obj = self.env['ecologic.report.wizard'].create({
                            'command' : project.command,
                            'partner_name' : project.partner_id.name,
                            'container_name' : container.name,
                            'num_demande' : project.num_demande,
                            'origin_zip' : project.partner_id.zip,
                            'origin_city' : project.partner_id.city,
                            'operation' : '',
                            'reception_date' : container.picking_id.exit_date_time,
                            'date_operation' : project.date_reception,
                            'ecologic_code': container.sub_product_id.product_ecologic_code,
                            'weight' : container.net_weight/1000,
                            'declared' : container.declared
                        })
                    ecologic_report.append(ecologic_report_obj.id)
            if stock_container_obj:
                for rc in stock_container_obj:
                    ecologic_report_obj = self.env['ecologic.report.wizard'].create({
                            'command' : project.command,
                            'partner_name' : project.partner_id.name,
                            'container_name' : rc.name,
                            'num_demande' : project.num_demande,
                            'origin_zip' : project.partner_id.zip,
                            'origin_city' : project.partner_id.city,
                            'operation' : '',
                            'reception_date' : rc.picking_id.exit_date_time,
                            'date_operation' : project.date_reception,
                            'ecologic_code': rc.content_type_id.product_ecologic_code,
                            'weight' : rc.gross_weight/1000,
                            'declared' : ''
                        })
                    ecologic_report.append(ecologic_report_obj.id)

        print(ecologic_report,'--ecologic_report--')

        return {
            'name': "Ecologic Report",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'ecologic.report.wizard',
            'target': 'current',
            'domain': [('id', '=', [x for x in ecologic_report])],
            'views_id':False,
            'views':[(self.env.ref('ppts_logistics.ecologic_report_tree_view').id or False, 'tree')],
        }


class EcologicReportWizard(models.TransientModel):
    _name = 'ecologic.report.wizard'

    command = fields.Char('Reference')
    partner_name = fields.Char('societe')
    container_name = fields.Char('Container Name')
    num_demande = fields.Char('ID Demande')
    origin_zip = fields.Char('Origin Zip')
    origin_city = fields.Char('Origin City')
    operation = fields.Selection([
        ('sale', 'Sale'),
        ('treated', 'Treated')
        ], string="Operation")
    reception_date = fields.Date('Date RI')
    date_operation = fields.Date('Date Operation')
    ecologic_code = fields.Char('Article')
    weight = fields.Float('Weight(Tonne)')
    declared = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
        ], string="Declear?")
