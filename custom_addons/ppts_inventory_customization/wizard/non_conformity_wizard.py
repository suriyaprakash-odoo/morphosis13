from odoo import api, fields, models,_
from odoo.exceptions import UserError

class NonConformity(models.TransientModel):
    _name = 'non.conformity.wizard'

    conformity_type = fields.Selection([('dangerous','Dangerous Material'),('content_mismatch','Content Mismatch'),('quantity','Incorrect Quantity')],string="Non Conformity Type",required=1)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    quarantine_location = fields.Many2one('stock.location',string="Location to Move",required=1,domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)

    def move_to_quarantine(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            container_id = self.env['project.container'].browse(active_id)
            if container_id:
                try:
                    template_id = self.env.ref('ppts_inventory_customization.non_conformity_notification_email')
                except ValueError:
                    template_id = False
                if container_id.project_id.user_id.partner_id.email:
                    container_id.state = 'non_conformity'
                    container_id.location_id = self.quarantine_location.id
                    container_id.non_conformity_type = self.conformity_type
                    type = dict(self._fields['conformity_type'].selection).get(self.conformity_type)
                    template_id.with_context({'type': type}).send_mail(container_id.id, force_send=True)
                else:
                    raise UserError(_('Please enter email address for %s') % container_id.project_id.user_id.partner_id.name)


