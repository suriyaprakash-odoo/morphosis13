from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from dateutil import relativedelta
from odoo.exceptions import UserError

from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    transport_rfq_count = fields.Integer('RFQ Count',compute='compute_transport_rfq_count', default=0)
    is_transport_rfq = fields.Boolean('Is Transport RFQ?')
    logistics_id = fields.Many2one('logistics.management','Transport Request ref')

    def compute_transport_rfq_count(self):
        for rec in self:
            transport_rfq_obj = self.env['purchase.order'].search([('origin' , '=' , rec.name)])
            if transport_rfq_obj:
                rec.transport_rfq_count = len(transport_rfq_obj)
            else:
                rec.transport_rfq_count = 0

    def action_view_transport_rfq(self):

        return{
            'name': _('Transport RFQ'),
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'purchase.order',
            'domain' : [('origin', '=', self[0].name)],
            'views_id':False,
            'views':[(self.env.ref('purchase.purchase_order_tree').id or False, 'tree'),
                     (self.env.ref('purchase.purchase_order_form').id or False, 'form')],
            }

    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        project_obj = self.env['project.entries'].search([('origin' , '=' , self.id)])

        # transport_obj = self.env['logistics.management'].search([('origin' , '=' , project_obj.id),('status' , '=' , 'approved')])

        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)

        transport_po_obj = self.env['purchase.order'].search([('origin' , '=' , project_obj.origin.name)])
        if project_obj.is_transport == True:
            return {
                'picking_type_id': self.picking_type_id.id,
                'partner_id': self.partner_id.id,
                'vendor_ref': self.partner_ref,
                'include_logistics':self.include_logistics,
                'project_entry_id':project_obj.id,
                # 'transporter_partner_id':transport_obj.partner_id.id or '',
                # 'gross_weight':transport_obj.gross_weight or '',
                # 'weight_uom_id':transport_obj.weight_uom_id.id or '',
                # 'pickup_date_type':transport_obj.pickup_date_type,
                # 'pickup_date':transport_obj.pickup_date,
                # 'pickup_earliest_date':transport_obj.pickup_earliest_date,
                # 'pickup_latest_date':transport_obj.pickup_latest_date,
                # 'expected_delivery':transport_obj.expected_delivery,
                # 'no_of_container':transport_obj.no_of_container or '',
                'user_id': False,
                'date': self.date_order,
                'origin': self.name,
                'location_dest_id': self._get_destination_location(),
                'location_id': self.partner_id.property_stock_supplier.id,
                'company_id': self.company_id.id,
                'logistics_updated':True,
                'transport_po_id':transport_po_obj.id
            }
        if project_obj.is_registered_package == True:
            return{
                'picking_type_id': self.picking_type_id.id,
                'partner_id': self.partner_id.id,
                'vendor_ref': self.partner_ref,
                'project_entry_id':project_obj.id,
                'include_logistics':self.include_logistics,
                'user_id': False,
                'date': self.date_order,
                'origin': self.name,
                'location_dest_id': self._get_destination_location(),
                'location_id': self.partner_id.property_stock_supplier.id,
                'company_id': self.company_id.id,
                'is_registered_package':project_obj.is_registered_package,            
            }
        elif self.is_internal_purchase == True:
            return {
                'picking_type_id': self.picking_type_id.id,
                'partner_id': self.partner_id.id,
                'project_entry_id':project_obj.id,
                'include_logistics':self.include_logistics,
                'user_id': False,
                'date': self.date_order,
                'origin': self.name,
                'location_dest_id': self._get_destination_location(),
                'location_id': self.partner_id.property_stock_supplier.id,
                'company_id': self.company_id.id,
                'is_internal_purchase':self.is_internal_purchase,
            }
        else:
            return {
                'picking_type_id': self.picking_type_id.id,
                'partner_id': self.partner_id.id,
                'project_entry_id':project_obj.id,
                'include_logistics':self.include_logistics,
                'user_id': False,
                'date': self.date_order,
                'origin': self.name,
                'location_dest_id': self._get_destination_location(),
                'location_id': self.partner_id.property_stock_supplier.id,
                'company_id': self.company_id.id,
            }


    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase')[1]
            elif self.is_transport_rfq:
                template_id = ir_model_data.get_object_reference('ppts_logistics', 'email_template_transport_purchase_order')[1]
            else:
                template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase_done')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'active_model': 'purchase.order',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })

        # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_template(template.lang, ctx['default_model'], ctx['default_res_id'])

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Request for Quotation')
        elif self.is_transport_rfq:
            ctx['model_description'] = _('Order Details')
        else:
            ctx['model_description'] = _('Purchase Order')

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