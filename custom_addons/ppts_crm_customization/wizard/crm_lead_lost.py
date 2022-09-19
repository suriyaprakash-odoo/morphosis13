# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'
    _description = 'Get Lost Reason'

    def action_lost_reason_apply(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        if leads.lead_type == 'sales':
            for line in leads.product_lines:
                if line.container_ids:
                    for rec in line.container_ids:
                        if rec.state == 'lead':
                            rec.state = 'to_be_sold'
        return leads.action_set_lost(lost_reason=self.lost_reason_id.id)
