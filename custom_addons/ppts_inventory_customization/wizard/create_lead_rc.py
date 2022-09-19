from odoo import api, fields, models,_
from odoo.exceptions import UserError


class CreateLeadDC(models.TransientModel):
    _name = 'create.lead.rc'

    partner_id = fields.Many2one("res.partner",string="Customer")
    name = fields.Char("Name of the Lead")
    container_ids = fields.Many2many("stock.container",string='Selected Containers')
    lead_id = fields.Many2one("crm.lead",string="Lead ID")
    note = fields.Char("")

    def action_create_lead(self):
        for record in self:
            lead_vals = {
                'name': record.name,
                'partner_id': record.partner_id.id or False,
                'product_lines': [],
                'type': 'opportunity',
                'lead_type': 'sales',
            }

            rc_product_list = []
            for line in self.container_ids:
                # weight += line.net_weight

                # if line.content_type_id.uom_id.name == 'Tonne':
                #     final_weight = weight / 1000
                # else:
                #     final_weight = weight

                if line.content_type_id.id not in rc_product_list:
                    rc_product_list.append(line.content_type_id.id)
                # line.state = 'lead'
            product_container_list = []
            product_container_dict = {}
            rc_vals = []
            for rec in rc_product_list:
                weight = 0.0
                final_weight = 0.0
                no_of_pieces = 0.0
                rc_line = {}
                container_obj = self.env['stock.container'].search([('content_type_id' , '=' , rec),('id' , 'in' , self.container_ids.ids)])
                product_obj = self.env['product.product'].search([('id' , '=' , rec)])
                for line in container_obj:
                    if line.container_specific == "weight":
                        weight += line.net_weight

                        if line.content_type_id.uom_id.name == 'Tonne' or line.content_type_id.uom_id.name == 'tonne':
                            final_weight = weight / 1000
                        else:
                            final_weight = weight
                    else:
                        final_weight += line.total_number_of_pieces
                    

                rc_line.update({
                    'product_id': product_obj.id,
                    'description': product_obj.name,
                    'uom_id': product_obj.uom_id.id,
                    'quantity': final_weight,
                    'container_ids': container_obj.ids,
                    'parent_lead_type': 'sales',
                    'price': product_obj.lst_price,
                    'price_per_ton': product_obj.lst_price
                })
                rc_vals.append((0, 0, rc_line))
            lead_vals['product_lines'] = rc_vals
            lead_id = self.env["crm.lead"].create(lead_vals)
            if lead_id:
                self.lead_id = lead_id
                self.note = 'CRM Lead is created click this button to open'
            view_id = self.env.ref('ppts_inventory_customization.create_leads_wizard_form').id
            return {
                'name': ('Create Lead'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'create.lead.rc',
                'views': [(view_id, 'form')],
                'view_id': view_id,
                'target': 'new',
                'res_id': self.ids[0],
            }

    def action_open_lead(self):
        if self.lead_id:
            action = self.env.ref('crm.crm_lead_action_pipeline').read()[0]
            action['views'] = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]
            action['res_id'] =self.lead_id.id
            return action
