from odoo import fields, models, api, _
from datetime import datetime

class ProjectEntries(models.Model):
    _inherit = 'project.entries'

    lab_report_id = fields.Many2one("laboratory.report", string="Lab report Id")
    lab_test = fields.Boolean("Request Laboratory Test")


    def create_lab_report_request(self):

        vals = ({'default_partner_id': self.partner_id.id, 'default_project_id':self.id, 'default_sent_date': datetime.now().date()})

        report_ids = self.env["laboratory.report"].search([('project_id','=',self.id)])

        return {
            'name': "Laboratory Test Report",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'laboratory.report',
            'target': 'current',
            'context': vals,
            'view_mode': 'tree,form',
            'domain': [('id', 'in', report_ids.ids)],
        }
    

    def action_alert_laboratory_notification(self):
        '''
        This function opens a window to compose an email, with the laboratory notification template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('laboratory_report', 'email_template_alert_laboratory_notification')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})

        ctx.update({
            'default_model': 'project.entries',
            'active_model': 'project.entries',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'default_attachment_ids': [],
            'model_description': 'Laboratory Notification',
            'force_email': True,
        })

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }