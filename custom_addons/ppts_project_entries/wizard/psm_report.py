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


class PSMReport(models.TransientModel):
    _name = 'psm.report'

    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')


    def view_psm_report(self):
        print(self.from_date,'--self.from_date--')
        print(self.to_date,'--self.to_date--')
        project_obj = self.env['project.entries'].search([('creation_date', '<=', self.to_date),('creation_date', '>=', self.from_date),('is_registered_package', '=', True)])

        print(project_obj,'--project_obj--')
        psm_report = []
        for project in project_obj:
            container_obj = self.env['project.container'].search([('project_id', '=', project.id)])
            print(container_obj,'--container_obj--')
            if container_obj:
                for container in container_obj:
                    container_registration = ''
                    if container.chronopost_number and container.have_batteries:
                        container_registration = 'yes_battries'
                    elif container.chronopost_number and not container.have_batteries:
                        container_registration = 'yes'
                    else:
                        container_registration = 'no'
                    psm_report_obj = self.env['psm.wizard.report'].create({
                            'project_name' : project.name,
                            'container_name' : container.name,
                            'container_registration' : container_registration,
                            'state' : container.state,
                            'po_updated' : 'yes' if project.origin.is_sorted else 'no'
                        })
                    psm_report.append(psm_report_obj.id)

        print(psm_report,'--psm_report--')

        return {
            'name': "PSM Report",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'psm.wizard.report',
            'target': 'current',
            'domain': [('id', '=', [x for x in psm_report])],
            'views_id':False,
            'views':[(self.env.ref('ppts_project_entries.psm_report_tree_view').id or False, 'tree')],
        }


class PsmWizardReport(models.TransientModel):
    _name = 'psm.wizard.report'

    project_name = fields.Char(string="Project")
    container_name = fields.Char(string="Container")
    container_registration = fields.Selection([
        ('yes' , 'Yes'),
        ('no' , 'No'),
        ('yes_battries' , 'Yes(Battery)')
    ],string="Register")
    state = fields.Selection([
            ('new', 'New'), 
            ('confirmed', 'Confirmed'),
            ('planned','Planned'), 
            ('in_progress', 'Production'), 
            ('non_conformity', 'Non Conformity'), 
            ('dangerous', 'Quarantine'), 
            ('close', 'Closed'), 
            ('return', 'Return')], 
            string="Status")
    po_updated = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
        ], string="PO Updated?")