from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import math

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    lead_type = fields.Selection([('sales', 'Sales'), ('purchase', 'Purchase'), ('refining_purchase', 'Refining Purchase')])
    po_quotation_count = fields.Integer(compute='_compute_po_data', string="Number of Quotations")
    po_order_count = fields.Integer(compute='_compute_po_data', string="Number of Sale Orders")
    po_amount_total = fields.Monetary(compute='_compute_po_data', string="Sum of Orders", help="Untaxed Total of Confirmed Orders", currency_field='company_currency')
    product_lines = fields.One2many("crm.product.line", "lead_id", string="Product Lines")
    estimated_transport_cost = fields.Float('Estimated Transport Cost')
    estimated_additional_purchase = fields.Float('Estimated Additional Purchase')
    estimated_additional_sale = fields.Float('Estimated Additional Sale')
    # is_approval = fields.Boolean('Approval required', compute="_compute_approval")
    is_approval = fields.Boolean('Approval required')
    is_approved = fields.Boolean('Approved')
    is_approval_mail_sent = fields.Boolean('Approval Mail Sent')
    is_rejected = fields.Boolean('Rejected')
    total_offer_price = fields.Monetary(string='Total Offer Price', currency_field='company_currency', compute="_compute_total_offer_without_transport")
    total_target_price = fields.Monetary('Total Target Price', currency_field='company_currency', compute="_compute_target_price_without_transport")
    cash_margin = fields.Monetary('Cash Margin', currency_field='company_currency', compute="_compute_cash_margin")
    margin_percentage = fields.Integer('Margin(%)', compute="_compute_margin_percentage")
    total_offer_price_transport = fields.Monetary(string='Total Offer Price with Transport', currency_field='company_currency', compute="_compute_total_offer")
    total_target_price_transport = fields.Monetary('Total Target Price with Transport', currency_field='company_currency', compute="_compute_target_price")
    margin_class = fields.Selection([
        ('class_a' , 'Class A'),
        ('class_b' , 'Class B'),
        ('class_c' , 'Class C')
        ], string = "Margin Class")

    project_count = fields.Integer('Project Count', compute="_compute_project_count")
    partner_ref = fields.Char('Vendor Reference')

    is_ecologic_pricelist = fields.Boolean(string="Is Ecologic?",default=False)

    sample_line_ids = fields.One2many('refining.sample','sample_line_id', string='Refining Sample')

    # @api.onchange('product_lines')
    # def onchange_product_lines_service(self):
    #     if self.product_lines:
    #         service_cost = 0.0
    #         for line in self.product_lines:
    #              service_cost += (line.estimated_service_cost * line.quantity)
    #         self.estimated_additional_sale = service_cost

    @api.onchange('partner_id')
    def onchange_partner_in_picking(self):
        if self.partner_id:
            if self.partner_id.short_code:
                short_code = self.partner_id.short_code + '/'
            else:
                short_code = ''
            if self.partner_id.ref:
                ref = self.partner_id.ref + '/'
            else:
                ref = ''
            self.partner_ref = ref + short_code + str(self.partner_id.lot_sequence_number)

    # @api.model
    # def create(self,vals):
    #     res = super(CrmLead, self).create(vals)
    #     if res.partner_id.short_code:
    #         res.partner_ref = str(res.partner_id.short_code)+'/0'+str(res.partner_id.lot_sequence_number)
    #     else:
    #         res.partner_ref = 'Lot/0'+str(res.partner_id.lot_sequence_number)
    #     res.partner_id.lot_sequence_number += 1
    #
    #     return res

    # def write(self,vals):
    #     res = super(CrmLead, self).write(vals)

    #     print(res)

    #     purchase_order_obj = self.env['purchase.order'].search([('opportunity_id' , '=' , self.id)])

    #     if self.product_lines:
    #         for crm_line in self.product_lines:
    #             if purchase_order_obj:
    #                 for po_line in purchase_order_obj.order_line:
    #                     if po_line.product_id == crm_line.product_id:
    #                         po_line.product_qty = crm_line.quantity
    #                         po_line.price_unit = crm_line.offer_price
                        
    #     return res


    def _compute_project_count(self):
        for lead in self:
            purchase_order_obj = self.env['purchase.order'].search([('opportunity_id', '=', lead.id)])
            if purchase_order_obj:
                for order in purchase_order_obj:
                    if order.is_project == True:
                        lead.project_count += 1
                    else:
                        lead.project_count = lead.project_count
            else:
                lead.project_count = 0

    @api.depends('product_lines.offer_price','estimated_transport_cost')
    def _compute_total_offer(self):
        for rec in self:
            total_price = 0.00
            service_charges = 0.00
            for line in rec.product_lines:
                # service_charges += (line.estimated_service_cost * line.quantity)
                if line.is_malus:
                    total_price -= (line.malus_demand * line.quantity)
                elif line.is_service:
                    qty = 1
                    if line.quantity:
                        qty = line.quantity
                    service_charges += (line.estimated_service_cost * qty)
                else:
                    total_price += (line.offer_price * line.quantity)
                    
            final_total_offer_price = 0.00
            if rec.lead_type == 'purchase':
                final_total_offer_price = (total_price + rec.estimated_additional_sale) - (rec.estimated_transport_cost + rec.estimated_additional_purchase) - service_charges
            elif rec.lead_type == 'sales':
                final_total_offer_price = (total_price + rec.estimated_transport_cost + rec.estimated_additional_sale) - (rec.estimated_additional_purchase) + service_charges
            elif rec.lead_type == 'refining_purchase':
                final_total_offer_price = (total_price + rec.estimated_additional_sale) - (rec.estimated_transport_cost + rec.estimated_additional_purchase) - service_charges
            else:
                final_total_offer_price = 0.00
            
            if final_total_offer_price != 0.00:
                rec.update({
                    'total_offer_price_transport': final_total_offer_price
                })
            else:
                rec.update({
                    'total_offer_price_transport': 0.00
                })

    @api.depends('product_lines.price','estimated_transport_cost')
    def _compute_target_price(self):
        for rec in self:
            total_price = 0.00
            service_charges = 0.00
            for line in rec.product_lines:
                # service_charges += (line.estimated_service_cost * line.quantity)
                if not line.is_malus:
                    total_price += (line.price * line.quantity)
                elif line.is_service:
                    qty = 1
                    if line.quantity:
                        qty = line.quantity
                    service_charges += (line.estimated_service_cost * qty)
                else:
                    total_price = total_price
            final_total_target_price = 0.00

            if rec.lead_type == 'purchase' or rec.lead_type == 'refining_purchase':
                final_total_target_price = (total_price + rec.estimated_additional_sale) - (rec.estimated_transport_cost + rec.estimated_additional_purchase)
            elif rec.lead_type == 'sales':
                final_total_target_price = (total_price + rec.estimated_transport_cost + rec.estimated_additional_sale) - (rec.estimated_additional_purchase)
            else:
                final_total_target_price = 0.00

            if final_total_target_price != 0.00:
                rec.update({
                    'total_target_price_transport': final_total_target_price
                })
            else:
                rec.update({
                    'total_target_price_transport': 0.00
                })

    @api.depends('product_lines.offer_price')
    def _compute_total_offer_without_transport(self):
        for rec in self:
            total_price = 0.00
            service_charges = 0.00
            for line in rec.product_lines:
                # service_charges += (line.estimated_service_cost * line.quantity)
                if line.is_malus:
                    total_price -= (line.malus_demand * line.quantity)
                elif line.is_service:
                    qty = 1
                    if line.quantity:
                        qty = line.quantity
                    service_charges += (line.estimated_service_cost * qty)
                else:
                    total_price += (line.offer_price * line.quantity)

            if rec.lead_type in ('purchase','refining_purchase'):
                total_offer_price = total_price + rec.estimated_additional_sale - rec.estimated_additional_purchase - service_charges   
            else:
                total_offer_price = total_price + rec.estimated_additional_sale - rec.estimated_additional_purchase  + service_charges

            rec.total_offer_price = total_offer_price

    @api.depends('product_lines.price')
    def _compute_target_price_without_transport(self):
        for rec in self:
            total_price = 0.00
            service_charges = 0.00
            for line in rec.product_lines:
                # service_charges += (line.estimated_service_cost * line.quantity)
                if not line.is_malus:
                    total_price += (line.price * line.quantity)
                elif is_service:
                    service_charges += (line.estimated_service_cost * line.quantity)
                else:
                    total_price = total_price
            if total_price != 0.00:
                rec.update({
                    'total_target_price': (total_price + rec.estimated_additional_sale) - rec.estimated_additional_purchase
                })
            else:
                rec.update({
                    'total_target_price': rec.estimated_additional_sale - rec.estimated_additional_purchase
                })

    @api.depends('total_offer_price_transport', 'total_target_price_transport')
    def _compute_cash_margin(self):
        for rec in self:
            total_sale_price = 0
            total_ecologic_price = 0
            margin = 0
            process_cost = 0.0
            for line in rec.product_lines:

                if not line.is_malus:
                    total_sale_price += (line.product_id.lst_price * line.quantity)
                    total_ecologic_price += (line.product_id.ecologic_price * line.quantity)
                else:
                    total_sale_price -= ((line.malus_demand - line.return_price) * line.quantity) 
                process_cost += line.process_cost

            if total_sale_price != 0 and rec.total_offer_price_transport != 0:
                if rec.is_ecologic_pricelist:
                    margin = abs(total_sale_price - total_ecologic_price) - rec.estimated_transport_cost
                else:
                    margin = (total_sale_price - rec.total_offer_price_transport) - process_cost - rec.estimated_transport_cost
                rec.update({
                    'cash_margin': margin
                })
            else:
                rec.cash_margin = 0.00

    @api.depends('total_offer_price_transport', 'total_target_price_transport')
    def _compute_margin_percentage(self):
        for rec in self:
            total_sale_price = 0
            margin_per = 0
            process_cost = 0.0
            transport_cost = 0.0
            for line in rec.product_lines:
                product_price = line.product_id.ecologic_price if rec.is_ecologic_pricelist else line.product_id.lst_price

                if not line.is_malus:
                    total_sale_price += (product_price * line.quantity)
                else:
                    total_sale_price -= ((line.malus_demand - line.return_price) * line.quantity)
                process_cost += line.process_cost
            if total_sale_price != 0 and rec.total_offer_price_transport != 0:                
                margin_per = ((((total_sale_price - rec.total_offer_price_transport) - process_cost - rec.estimated_transport_cost) / total_sale_price) * 100)
                rec.update({
                    'margin_percentage': margin_per
                })
            else:
                rec.margin_percentage = 0.00

    @api.onchange('total_offer_price_transport')
    def onchange_product_lines(self):
        if self.total_offer_price_transport:
            self.planned_revenue = self.total_offer_price_transport

    def action_view_project_entry(self):
        project_list = []
        purchase_order_obj = self.env['purchase.order'].search([('opportunity_id', '=', self.id)])
        if purchase_order_obj:
            for order in purchase_order_obj:
                if order.is_project == True:
                    project_obj = self.env['project.entries'].search([('origin', '=', order.id)])
                    project_list.append(project_obj.id)

        return {
            'name': _('Project Entry'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'project.entries',
            'domain': [('id', 'in', project_list)],
            'views_id': False,
            'views': [(self.env.ref('ppts_project_entries.project_entries_tree_view').id or False, 'tree'),
                      (self.env.ref('ppts_project_entries.project_entries_form_view').id or False, 'form')],
        }

    def action_new_quotation(self):
        action = self.env.ref("sale_crm.sale_action_quotations_new").read()[0]
        line_vals = []
        for line in self.product_lines:
            if line.quantity != 0:
                line_vals.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.description,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.offer_price,
                    'product_uom': line.uom_id.id,
                    'container_id': line.container_ids.ids or False
                }))
            else:
                raise ValidationError('Please update the quantity in all lines')

        action['context'] = {
            'search_default_opportunity_id': self.id,
            'default_opportunity_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_team_id': self.team_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_name': self.name,
            'default_source_id': self.source_id.id,
            'default_order_line': line_vals,
            'default_amount_from_offer': self.total_offer_price_transport,
        }
        return action

    # @api.depends('product_lines')
    # def _compute_approval(self):
    #     for rec in self:
    #         if rec.lead_type == 'purchase':
    #             if rec.total_target_price_transport < rec.company_id.purchase_limit:
    #                 if rec.total_offer_price_transport > rec.total_target_price_transport:
    #                     diff_percent = (((rec.total_offer_price_transport - rec.total_target_price_transport) / rec.total_target_price_transport) * 100)
    #                     if abs(diff_percent) > rec.company_id.purchase_threshold_percentage:
    #                         rec.is_approval = True
    #                     else:
    #                         rec.is_approval = False
    #                 else:
    #                     rec.is_approval = False
    #             else:
    #                 rec.is_approval = True
    #         else:
    #             if rec.total_offer_price_transport < rec.total_target_price_transport:
    #                 rec.is_approval = True
    #             else:
    #                 rec.is_approval = False

    def _compute_po_data(self):
        for lead in self:
            total = 0.0
            po_quotation_count = 0
            po_order_count = 0
            company_currency = lead.company_currency or self.env.company.currency_id
            lead_ids = self.env['purchase.order'].search([('opportunity_id', '=', lead.id)])
            for order in lead_ids:
                if order.state in ('draft', 'sent'):
                    po_quotation_count += 1
                if order.state not in ('draft', 'sent', 'cancel'):
                    po_order_count += 1
                    total += order.currency_id._convert(
                        order.amount_untaxed, company_currency, order.company_id, order.date_order or fields.Date.today())
            lead.po_amount_total = total
            lead.po_quotation_count = po_quotation_count
            lead.po_order_count = po_order_count

    def action_purchase_quotations_new(self):
        action = self.env.ref("purchase.purchase_rfq").read()[0]

        line_vals = []
        # if self.product_lines:
        #     for line in self.product_lines:
        #         if line.offer_price <= 0.0:
        #             raise UserError(_('Please enter the offer price'))

        for line in self.product_lines:
            if line.quantity != 0:
                if line.is_malus:
                    price_unit = float('-'+str(line.malus_demand))
                elif line.is_service:
                    price_unit = float('-'+str(line.estimated_service_cost))
                else:
                    price_unit = line.offer_price
                line_vals.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.description,
                    'product_qty': line.quantity,
                    'price_unit': price_unit,
                    'product_uom': line.uom_id.id,
                    'date_planned': datetime.now(),
                    'crm_product_line_id':line.id,
                    'line_origin':line.line_origin
                }))
            else:
                raise ValidationError('Please update the quantity in all lines')
        action['domain'] = [('opportunity_id', '=', self.id)]
        action['context'] = {
            'default_opportunity_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_team_id': self.team_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_order_line': line_vals,
            'default_amount_from_offer': self.total_offer_price_transport,
            'default_partner_ref': self.partner_ref,
        }
        return action

    def action_view_purchase_quotation(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        line_vals = []
        for line in self.product_lines:
            if line.quantity != 0:
                line_vals.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.description,
                    'product_qty': line.quantity,
                    'price_unit': line.offer_price,
                    'product_uom': line.uom_id.id,
                    'date_planned': datetime.now(),
                    'crm_product_line_id':line.id,
                    'line_origin':line.line_origin
                }))
            else:
                raise ValidationError('Please update the quantity in all lines')
        action['context'] = {
            'default_opportunity_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_team_id': self.team_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_order_line': line_vals,
            'default_amount_from_offer': self.total_offer_price_transport,
            'default_partner_ref': self.partner_ref,
        }
        action['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent'])]
        quotations = self.env['purchase.order'].search([('opportunity_id', '=', self.id)]).filtered(lambda l: l.state in ('draft', 'sent'))
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = quotations.id
        return action

    def action_view_purchase_order(self):
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['context'] = {
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id,
        }
        action['domain'] = [('opportunity_id', '=', self.id), ('state', 'not in', ('draft', 'sent', 'cancel'))]
        orders = self.mapped('order_ids').filtered(lambda l: l.state not in ('draft', 'sent', 'cancel'))
        if len(orders) == 1:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = orders.id
        return action

    # def send_for_approval(self):
    #     template_id = self.env.ref('ppts_crm_customization.email_template_approve_lead').id
    #     mail_template = self.env['mail.template'].browse(template_id)

    #     sent_template_id = self.env.ref('ppts_crm_customization.email_template_approval_sent').id
    #     sent_mail_template = self.env['mail.template'].browse(sent_template_id)

    #     if mail_template and sent_mail_template:
    #         self.is_approval_mail_sent = True
    #         mail_template.send_mail(self.id, force_send=True)
    #         sent_mail_template.send_mail(self.id, force_send=True)

    # def approve_lead(self):
    #     template_id = self.env.ref('ppts_crm_customization.email_template_lead_approved').id
    #     mail_template = self.env['mail.template'].browse(template_id)

    #     if mail_template:
    #         self.is_approved = True
    #         mail_template.send_mail(self.id, force_send=True)

    # def reject_lead(self):
    #     template_id = self.env.ref('ppts_crm_customization.email_template_lead_rejected').id
    #     mail_template = self.env['mail.template'].browse(template_id)

    #     if mail_template:
    #         self.is_rejected = True
    #         mail_template.send_mail(self.id, force_send=True)


class CrmLines(models.Model):
    _name = "crm.product.line"

    lead_id = fields.Many2one("crm.lead", string="CRM Ref")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    product_id = fields.Many2one("product.product", string="Product", required=True)
    description = fields.Char("Description", required=True)
    quantity = fields.Float("Quantity", digits=(12,4))
    process_type = fields.Many2many('process.type', string="Process")
    estimated_transport_cost = fields.Monetary(string="Estimated Transport Cost", currency_field='currency_id')
    price = fields.Monetary(string='Target Sale/Purchase Price', currency_field='currency_id')
    offer_price = fields.Monetary(string='Offer Price', currency_field='currency_id')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    container_ids = fields.Many2many("stock.container", string="Containers")
    production_cost = fields.Monetary(string='Production Cost', currency_field='currency_id', compute='_compute_production_price')
    parent_lead_type = fields.Selection([('sales', 'Sales'), ('purchase', 'Purchase'), ('refining_purchase', 'Refining Purchase')], string="Lead Type")
    price_per_ton = fields.Monetary(string='Price per UdM', currency_field='currency_id')
    expexted_margin_percentage = fields.Integer('Company Margin(%)', compute='_compute_margin_class')
    computed_margin_percentage = fields.Integer('Offer Margin(%)')
    process_cost = fields.Float("Process Cost",compute='_compute_process_cost')
    return_price = fields.Monetary('Malus', currency_field='currency_id')
    charge_malus = fields.Monetary('Charge Malus', currency_field='currency_id')
    malus_demand = fields.Monetary('Malus Demandé', currency_field='currency_id')
    is_malus = fields.Boolean('Is Malus')
    margin_class = fields.Selection([
        ('class_a' , 'Class A'),
        ('class_b' , 'Class B'),
        ('class_c' , 'Class C')
        ], string = "Margin Class")
    line_origin = fields.Char('Origin',default='crm')
    is_service = fields.Boolean("Is Service")
    estimated_service_cost = fields.Float("Estimated Service Cost")

    is_ecologic_pricelist = fields.Boolean(string="Is Ecologic Pricelist?")

    # @api.onchange('parent_lead_type')
    # def onchage_parent_lead_type(self):
    #     if self.parent_lead_type:
    #         if self.parent_lead_type == 'service':
    #             self.is_service = True

    # @api.model
    # def create(self, vals):
    #     res = super(CrmLines, self).create(vals)

    #     for record in res:  
    #         line_vals = []  
    #         if not record.line_origin == 'purchase':
    #             line_vals.append((0, 0, {
    #                 'product_id': record.product_id.id,
    #                 'name': record.description,
    #                 'product_qty': record.quantity,
    #                 'price_unit': record.offer_price if not record.is_malus else float('-'+str(record.malus_demand)),
    #                 'product_uom': record.uom_id.id,
    #                 'date_planned': datetime.now(),
    #                 'crm_product_line_id':record.id,
    #                 'line_origin':record.line_origin
    #             }))

    #         purchase_obj = self.env['purchase.order'].search([('opportunity_id' , '=' ,record.lead_id.id)])
    #         if purchase_obj:
    #             for order in purchase_obj:
    #                 order.order_line = line_vals

    #     return res


    def write(self,vals):
        res = super(CrmLines, self).write(vals)
        if vals.get('quantity'):

            po_sql_query = '''
                update purchase_order_line set product_qty = %s where id = %s
            '''

            project_sql_query = '''
                update project_entries_line set product_qty = %s where id = %s
            '''

            purchase_line_obj = self.env['purchase.order.line'].search([('crm_product_line_id' , '=' , self.id)])
            if purchase_line_obj:
                self.env.cr.execute(po_sql_query, (self.quantity,purchase_line_obj.id,))
                if not self.is_malus:
                    purchase_line_obj.price_subtotal = (self.quantity * self.offer_price)
                else:
                    purchase_line_obj.price_subtotal = (float('-'+str((self.malus_demand * self.quantity))))

                project_line_obj = self.env['project.entries.line'].search([('purchase_order_line_id' , '=' , purchase_line_obj.id)])
                if project_line_obj:
                    self.env.cr.execute(project_sql_query, (self.quantity,project_line_obj.id,))


        if vals.get('offer_price'):

            po_sql_query = '''
                update purchase_order_line set price_unit = %s where id = %s
            '''

            project_sql_query = '''
                update project_entries_line set offer_price = %s where id = %s
            '''

            purchase_line_obj = self.env['purchase.order.line'].search([('crm_product_line_id' , '=' , self.id)])
            if purchase_line_obj:  
                self.env.cr.execute(po_sql_query, (self.offer_price,purchase_line_obj.id,))
                if not self.is_malus:
                    purchase_line_obj.price_subtotal = (self.quantity * self.offer_price)
                else:
                    purchase_line_obj.price_subtotal = (float('-'+str((self.malus_demand * self.quantity))))

                project_line_obj = self.env['project.entries.line'].search([('purchase_order_line_id' , '=' , purchase_line_obj.id)])
                if project_line_obj:
                    self.env.cr.execute(project_sql_query, (self.offer_price,project_line_obj.id,))


        if vals.get('malus_demand'):

            po_sql_query = '''
                update purchase_order_line set price_unit = %s where id = %s
            '''

            project_sql_query = '''
                update project_entries_line set malus_demand = %s where id = %s
            '''

            purchase_line_obj = self.env['purchase.order.line'].search([('crm_product_line_id' , '=' , self.id)])
            if purchase_line_obj:  
                self.env.cr.execute(po_sql_query, (float('-'+str(self.malus_demand)),purchase_line_obj.id,))
                if not self.is_malus:
                    purchase_line_obj.price_subtotal = (self.quantity * self.offer_price)
                else:
                    purchase_line_obj.price_subtotal = (float('-'+str((self.malus_demand * self.quantity))))

                project_line_obj = self.env['project.entries.line'].search([('purchase_order_line_id' , '=' , purchase_line_obj.id)])
                if project_line_obj:
                    self.env.cr.execute(project_sql_query, (self.malus_demand,project_line_obj.id,))

        return res

    @api.onchange('product_id')
    def onchage_product_id(self):
        if self.product_id:
            res={'domain':{'container_ids': "[('id', '=', False)]"}}
            if self.product_id.container_product_ids:
                containers_list = []
                for line in self.product_id.container_product_ids:
                    containers_list.append(line.container_id.id)
                if len(containers_list) > 1:
                    if containers_list:
                        res['domain']['container_ids'] = "[('id', 'in', %s)]" % containers_list
                    else:
                        res['domain']['container_ids'] = []
                else:

                    if containers_list:
                        res['domain']['container_ids'] = "[('id', '=', %s)]" % containers_list[0]
                    else:
                        res['domain']['container_ids'] = []
            print(res)

            return res

    @api.depends('margin_class')
    def _compute_margin_class(self):
        for rec in self:
            expexted_margin_percentage = 0 
            if rec.margin_class == 'class_a':
                expexted_margin_percentage = rec.lead_id.company_id.sale_margin_a
            elif rec.margin_class == 'class_b':
                expexted_margin_percentage = rec.lead_id.company_id.sale_margin_b
            else:
                expexted_margin_percentage = rec.lead_id.company_id.sale_margin_c
            rec.update({
                'expexted_margin_percentage': expexted_margin_percentage
            })


    @api.depends('process_type')
    def _compute_process_cost(self):
        for rec in self:
            process_cost = 0.0
            for line in rec.process_type:
                process_cost += line.estimated_production_cost
            rec.update({
                'process_cost': process_cost * rec.quantity
            })

    @api.onchange('container_ids')
    def onchange_container_ids(self):
        if self.container_ids:
            weight = final_weight = 0.0
            for line in self.container_ids:
                weight += line.net_weight

            if line.content_type_id.uom_id.name == 'Tonne':
                final_weight = weight / 1000
            else:
                final_weight = weight

            self.quantity = final_weight

    @api.depends('container_ids.forecast_sale_price')
    def _compute_production_price(self):
        for lead_line in self:
            production_cost = 0.0
            if lead_line.lead_id.lead_type == 'sales':
                for line in lead_line.container_ids:
                    production_cost += line.forecast_sale_price
                lead_line.update({
                    'production_cost': production_cost
                })
            else:
                lead_line.update({
                    'production_cost': 0.00
                })

    @api.onchange('product_id', 'quantity','return_price')
    def onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.uom_id = self.product_id.uom_id.id
            self.price_per_ton = self.product_id.ecologic_price if self.is_ecologic_pricelist else self.product_id.lst_price
            self.return_price = self.product_id.malus
            self.charge_malus = self.product_id.charge_malus
            if self.quantity != 0 and not self.is_service:
                if math.ceil(self.price_per_ton) != 0:
                    if self.lead_id.lead_type == 'purchase' or self.lead_id.lead_type == 'refining_purchase':
                        if not self.is_malus:
                            if self.process_type:
                                production_cost = 0.00
                                for rec in self.process_type:
                                    production_cost = production_cost + rec.estimated_production_cost

                                    if production_cost != 0:
                                        if self.is_ecologic_pricelist:
                                            self.price = self.price_per_ton - production_cost
                                        else:
                                            if self.margin_class == 'class_a':
                                                self.price = (((self.price_per_ton) *(1 - (self.lead_id.company_id.sale_margin_a / 100))) -(production_cost))
                                            if self.margin_class == 'class_b':
                                                self.price = (((self.price_per_ton) *(1 - (self.lead_id.company_id.sale_margin_b / 100))) -(production_cost))
                                            if self.margin_class == 'class_c':
                                                self.price = (((self.price_per_ton) *(1 - (self.lead_id.company_id.sale_margin_c / 100))) -(production_cost))
                                    else:
                                        if self.is_ecologic_pricelist:
                                            self.price = self.price_per_ton
                                        else:
                                            if self.margin_class == 'class_a':
                                                self.price = ((self.price_per_ton) * (1 - (self.lead_id.company_id.sale_margin_a / 100)))
                                            if self.margin_class == 'class_b':
                                                self.price = ((self.price_per_ton) * (1 - (self.lead_id.company_id.sale_margin_b / 100)))
                                            if self.margin_class == 'class_c':
                                                self.price = ((self.price_per_ton) * (1 - (self.lead_id.company_id.sale_margin_c / 100)))
                                # if self.return_price:
                                #     self.price = self.price - abs(self.return_price)
                            else:
                                if self.is_ecologic_pricelist:
                                    self.price = self.price_per_ton
                                else:
                                    if self.margin_class == 'class_a':
                                        self.price = ((self.price_per_ton) * (1 - (self.lead_id.company_id.sale_margin_a / 100)))
                                    if self.margin_class == 'class_b':
                                        self.price = ((self.price_per_ton) * (1 - (self.lead_id.company_id.sale_margin_b / 100)))
                                    if self.margin_class == 'class_c':
                                        self.price = ((self.price_per_ton) * (1 - (self.lead_id.company_id.sale_margin_c / 100)))
                                    # if self.return_price:
                                    #     self.price = self.price - abs(self.return_price)
                        else:
                            if self.process_type:
                                production_cost = 0.00
                                for rec in self.process_type:
                                    production_cost = production_cost + rec.estimated_production_cost
                                    if production_cost != 0:
                                        self.price = self.price_per_ton - abs(self.return_price) - production_cost
                                    else:
                                        self.price = self.price_per_ton - abs(self.return_price)
                    else:
                        self.price = self.price_per_ton
                else:
                    raise UserError('Please update the public/ecologic price of the product')
            else:
                self.price = 0.0

    # @api.onchange('return_price')
    # def onchange_return_price(self):
    #     self.price = self.price - abs(self.return_price)

    @api.onchange('offer_price', 'price','malus_demand')
    def onchange_offer_margin(self):
        if self.parent_lead_type == 'purchase' or self.parent_lead_type == 'refining_purchase':
            if not self.is_malus:
                if self.offer_price != 0 and self.quantity:

                    product_price = self.product_id.ecologic_price if self.is_ecologic_pricelist else self.product_id.lst_price
                    
                    if math.ceil(product_price) != 0:
                        production_cost = 0
                        for rec in self.process_type:
                               production_cost += rec.estimated_production_cost
                        if self.is_ecologic_pricelist:
                            self.computed_margin_percentage = ((self.product_id.lst_price - self.offer_price)/self.product_id.ecologic_price) * 100
                        else:
                            self.computed_margin_percentage = ((((product_price - self.offer_price) - (production_cost)) / product_price) * 100)
                    else:
                        raise UserError('Please update the public/ecologic price of the product')
            # else:
            #     if self.malus_demand != 0 and self.quantity != 0:
            #         print(self.malus_demand,'------',self.quantity)
            #         if self.product_id.lst_price != 0:
            #             production_cost = 0
            #             for rec in self.process_type:
            #                    production_cost += rec.estimated_production_cost
            #             self.computed_margin_percentage = ((((abs(self.return_price) - abs(self.malus_demand)) - (production_cost)) / abs(self.return_price)) * 100)    
            #         else:
            #             raise UserError('Please update the public price of the product')

    @api.onchange('process_type')
    def onchange_process_type(self):
        if not self.quantity == 0:
            product_price = self.product_id.ecologic_price if self.is_ecologic_pricelist else self.product_id.lst_price
            if self.lead_id.lead_type == 'purchase' or self.lead_id.lead_type == 'refining_purchase':
                production_cost = 0.00
                if self.process_type:
                    for rec in self.process_type:
                        production_cost = production_cost + rec.estimated_production_cost
                        if production_cost != 0:
                            if self.is_ecologic_pricelist:
                                self.price = product_price - production_cost
                            else:
                                if self.margin_class == 'class_a':
                                    self.price = (((product_price) * (1 - (self.lead_id.company_id.sale_margin_a / 100))) - (production_cost)
                                )
                                if self.margin_class == 'class_b':
                                    self.price = (((product_price) * (1 - (self.lead_id.company_id.sale_margin_b / 100))) - (production_cost)
                                )
                                if self.margin_class == 'class_c':
                                    self.price = (((product_price) * (1 - (self.lead_id.company_id.sale_margin_c / 100))) - (production_cost)
                                )
                        else:
                            if self.is_ecologic_pricelist:
                                self.price = product_price
                            else:
                                if self.margin_class == 'class_a':
                                    self.price = ((product_price) * (1 - (self.lead_id.company_id.sale_margin_a / 100)))
                                if self.margin_class == 'class_b':
                                    self.price = ((product_price) * (1 - (self.lead_id.company_id.sale_margin_b / 100)))
                                if self.margin_class == 'class_c':
                                    self.price = ((product_price) * (1 - (self.lead_id.company_id.sale_margin_c / 100)))
                else:
                    if self.is_ecologic_pricelist:
                        self.price = product_price
                    else:
                        if self.margin_class == 'class_a':
                            self.price = ((product_price) * (1 - (self.lead_id.company_id.sale_margin_a / 100)))
                        if self.margin_class == 'class_b':
                            self.price = ((product_price) * (1 - (self.lead_id.company_id.sale_margin_b / 100)))
                        if self.margin_class == 'class_c':
                            self.price = ((product_price) * (1 - (self.lead_id.company_id.sale_margin_c / 100)))
            else:
                self.price = (product_price)
        else:
            self.price = 0.0


class RefiningSample(models.Model):
    _name = 'refining.sample'

    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Many2one('stock.production.lot', string='Lot/Serial Number', domain="[('product_id','=',product_id)]")
    quantity = fields.Float('Quantity', digits=(12,4))
    expected_result = fields.Float('Expected Result', digits=(12,4))
    actual_result = fields.Float('Actual Result', digits=(12,4))
    sample_line_id = fields.Many2one("crm.lead", string="CRM Ref")