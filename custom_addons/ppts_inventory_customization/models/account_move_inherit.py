from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class AccountmoveInherit(models.Model):
    _inherit = 'account.move'

    def open_purchase_order_view(self):
        form_id = self.env.ref('purchase.purchase_order_form').id

        res_id = self.env['purchase.order'].sudo().search([('name','=',self.invoice_origin)],limit=1)
        
        return{
              'name': _('Purchase Order'),
              'type':'ir.actions.act_window',
              'view_type':'form',
              'view_mode':'form',
              'res_model':'purchase.order',
              'res_id':res_id.id if res_id else False,
              'views_id':False,
              'views':[(form_id or False, 'form')],
              'target':'current',
              }