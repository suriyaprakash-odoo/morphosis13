from odoo import api, fields, models,_
from odoo.exceptions import UserError

class ReconfirmWizard(models.TransientModel):
    _name = 'reconfirm.wizard'

    sort_possible = fields.Selection([('possible','Possible'),('not_possible','Not Possible')],default="possible", string="Sorting Possible?",required=True)
    supplier_agreed = fields.Boolean("Supplier Agreed?")
    return_container = fields.Boolean("Return Container?")
    penalty_amount =fields.Float("Penalty Amount")
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    location_id = fields.Many2one("stock.location", string="Location to Move",domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)

    def reconfirm_container(self):
        active_id = self.env.context.get('active_id')
        container_id = self.env['project.container'].browse(active_id)
        if self.sort_possible == 'possible':
            if not container_id.action_type == 'cross_dock':
                if self.supplier_agreed:
                    try:
                        template_id = self.env.ref('ppts_inventory_customization.non_conformity_reconfirm_email')
                    except ValueError:
                        template_id = False
                    if container_id.project_id.user_id.partner_id.email:
                        container_id.state = 'confirmed'
                        container_id.reconfirmed = True
                        container_id.penalty_amount = self.penalty_amount
                        container_id.location_id = self.location_id.id
                        # container_id.non_conformity_type = self.conformity_type
                        type = dict(container_id._fields['state'].selection).get(container_id.state)
                        template_id.with_context({'type': type}).send_mail(container_id.id, force_send=True)
                    else:
                        raise UserError(_('Please enter email address for %s') % container_id.project_id.user_id.partner_id.name)
                else:
                    raise UserError(_('Supplier should be agreed to continue further'))
            else:
                vals = {
                        'content_type_id' : container_id.sub_product_id.id,
                        'container_type_id' : container_id.container_type_id.id,
                        'tare_weight' : container_id.container_type_id.tare_weight,
                        'max_weight' : container_id.container_type_id.capacity_weight,
                        'location_id' : self.location_id.id,
                        'related_company_id' : container_id.company_id.id,
                        'project_id' : container_id.project_id.id,
                        'picking_id' : container_id.picking_id.id,
                        'net_weight_dup' : container_id.net_gross_weight,
                        'total_number_of_pieces_dup' :container_id.quantity,
                        'container_specific' : 'count' if container_id.quantity != 0 else 'weight',
                        'cross_dock' : True,
                        'penalty_amount' : self.penalty_amount,
                        'partner_id': container_id.partner_id.id,
                        'source_container_id' : container_id.id
                    }
                recipient_container_obj = self.env['stock.container'].create(vals)
                recipient_container_obj.close_container()
                container_id.reconfirmed = True
                container_id.penalty_amount = self.penalty_amount
                container_id.location_id = self.location_id.id
                container_id.state = 'close'
        else:
            if self.return_container:
                try:
                    template_id = self.env.ref('ppts_inventory_customization.non_conformity_return_email')
                except ValueError:
                    template_id = False
                if container_id.project_id.user_id.partner_id.email:
                    container_id.state = 'return'
                    container_id.location_id = self.location_id.id
                    template_id.send_mail(container_id.id, force_send=True)
            else:
                raise UserError(_('Return Container should be selected to continue further'))