from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    sale_order_line_id = fields.Many2one(comodel_name="sale.order.line")


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    is_project = fields.Boolean('Is project create?')
    pricing_type = fields.Selection([
      ('fixed' , 'Fixed Price'),
      ('variable' , 'Variable Price')
      ], string="Pricing", default='fixed')
    is_fifteen_days = fields.Boolean("Is 15 days notice?")
    is_analysis = fields.Boolean("Is subject to analysis?")
    is_internal_purchase = fields.Boolean("Is internal Purchase?")
    project_entry_id = fields.Many2one("project.entries","Project ID")
    is_sorted = fields.Boolean('Is Sorted/treated')
    mask_po_line_ids = fields.One2many('mask.po.line','mask_po_line_id', string='Mask PO line ref')
    mask_po_total = fields.Monetary('Total', currency_field='currency_id', compute='_compute_mask_po_amount')

    include_logistics = fields.Boolean('Does not Include Logistics')


    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')


    @api.onchange("account_analytic_id")
    def onchange_account_analytic_id(self):
        for purchase in self:
            if purchase.account_analytic_id:
                for line in purchase.order_line:
                    line.sudo().update({
                        'account_analytic_id': purchase.account_analytic_id.id,
                    })
                

    def _compute_mask_po_amount(self):
      for po in self:
        total_price = 0.0
        if po.mask_po_line_ids:
          for line in po.mask_po_line_ids:
            total_price += line.price_subtotal
            po.mask_po_total = total_price
        else:
          po.mask_po_total = 0.0

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.new', sequence_date=seq_date) or '/'
        if vals.get('opportunity_id'):
            purchase_obj = self.env['purchase.order'].search([('opportunity_id' , '=' , int(vals.get('opportunity_id')))])
            for rec in purchase_obj:
              project_obj = self.env['project.entries'].search([('origin' , '=' , rec.id)])
              if project_obj.status == 'reject':
                raise UserError('The project is already rejected.So you cant create purchase order for the Lead.')

        res = super(PurchaseOrder, self).create(vals)

        if not res.is_internal_purchase:
            for line in res.order_line:
                product_qty = line.product_qty
                price_unit = line.price_unit
                line.onchange_product_id()
                line.product_qty = product_qty
                line.price_unit = price_unit

        if res.project_entry_id:
            self.env["project.purchase.orders"].create({'purchase_id':res.id,'amount':res.amount_total,'untaxed_amount':res.amount_untaxed,'project_id':res.project_entry_id.id})
        

        if vals.get('account_analytic_id'):
            for line in res.order_line:
                line.sudo().update({
                    'account_analytic_id': res.account_analytic_id.id,
                })
        
        if not res.is_transport_rfq:
            for line in res.order_line:
                if line.display_type==False:
                    if not line.account_analytic_id:
                        raise Warning("Analytic account not selected in order line.")

        return res

    def write(self,vals):
      res = super(PurchaseOrder, self).write(vals)
      if self.project_entry_id:
        project_purchase_obj = self.env['project.purchase.orders'].search([('purchase_id' , '=' , self.id)])
        if project_purchase_obj:
          project_purchase_obj.amount = self.amount_total
          project_purchase_obj.untaxed_amount = self.amount_untaxed

      if vals.get('account_analytic_id'):
        for line in self.order_line:
            line.sudo().update({
                'account_analytic_id': self.account_analytic_id.id,
            })
        
      return res


    def action_create_project_entry(self):

        ctx = dict()

        for rec in self:
            
            product_line_list = []
            refining_sample_list = []
            if rec.opportunity_id.lead_type == 'refining_purchase':
                if rec.opportunity_id.sample_line_ids:
                    for sample_line in rec.opportunity_id.sample_line_ids:
                        refining_sample_list.append([0, 0, {
                                'product_id' : sample_line.product_id.id,
                                'name' : sample_line.name.id,
                                'quantity' : sample_line.quantity,
                                'expected_result' : sample_line.expected_result,
                                'actual_result' : sample_line.actual_result,
                            }])

            for record in rec.order_line:
                if record.crm_product_line_id:
                    product_line_list.append([0, 0, {
                                            'product_id': record.crm_product_line_id.product_id.id,
                                            'name': record.crm_product_line_id.description or '',
                                            'product_qty': record.crm_product_line_id.quantity,
                                            'product_uom': record.crm_product_line_id.uom_id.id,
                                            'price_unit': record.crm_product_line_id.price_per_ton,
                                            'is_malus': record.crm_product_line_id.is_malus,
                                            # 'price': record.crm_product_line_id.price,
                                            'offer_price': record.crm_product_line_id.offer_price if not record.crm_product_line_id.is_service else 0,
                                            'malus': record.crm_product_line_id.return_price,
                                            'margin_class': record.crm_product_line_id.margin_class,
                                            'charge_malus': record.crm_product_line_id.charge_malus,
                                            'malus_demand': record.crm_product_line_id.malus_demand,
                                            'is_service': record.crm_product_line_id.is_service,
                                            'estimated_service_cost': record.crm_product_line_id.estimated_service_cost,
                                            # 'expexted_margin_percentage': record.crm_product_line_id.expexted_margin_percentage,
                                            'computed_margin_percentage': record.crm_product_line_id.computed_margin_percentage,
                                            'line_origin':record.line_origin,
                                            # 'taxes_id':[],
                                            'purchase_order_line_id':record.id,
                                            'container_type_line_ids':[],
                                            'account_analytic_id': record.account_analytic_id.id if record.account_analytic_id else False,
                                        }])
                else:
                    product_line_list.append([0, 0, {
                                            'product_id':record.product_id.id,
                                            'name':record.name or '',
                                            'product_qty':record.product_qty,
                                            'product_uom':record.product_uom.id,
                                            'price_unit':record.price_unit,
                                            # 'taxes_id':[(6, 0, record.taxes_id.ids)],
                                            # 'price_subtotal':record.price_subtotal,
                                            'line_origin':record.line_origin,
                                            'purchase_order_line_id':record.id,
                                            'container_type_line_ids':[],
                                            'account_analytic_id': record.account_analytic_id.id if record.account_analytic_id else False,
                                            }])

                
        for rec in self:
            product_list = [(0, 0, {
                'product_id':record.product_id.id,
                }) for record in rec.order_line]

        ctx = ({
            'default_partner_id':self.partner_id.id,
            'default_partner_ref':self.partner_ref or '',
            'default_user_id':self.user_id.id,
            'default_origin':self.id,
            'default_company_id':self.company_id.id,
            'default_include_logistics':self.include_logistics,
            # 'default_is_fifteen_days':self.is_fifteen_days,
            'default_is_offer_subject_to_analysis': True if self.pricing_type == 'variable' else False,
            'default_quoted_price':self.amount_total,
            'default_initial_offer_price':self.amount_total,
            'default_target_price':self.amount_total if self.pricing_type == 'fixed' else 0.00,
            'default_status':'quote',
            'default_forcased_transport_cost':self.opportunity_id.estimated_transport_cost,
            'default_estimated_extra_purchase_cost':self.opportunity_id.estimated_additional_purchase,
            'default_estimated_extra_sales':self.opportunity_id.estimated_additional_sale,
            'default_margin_class':self.opportunity_id.margin_class if self.opportunity_id else '' ,
            'default_pricing_type':self.pricing_type,
            'default_project_entry_ids':product_line_list,
            'default_is_ecologic':self.opportunity_id.is_ecologic_pricelist,
            'default_sample_line_ids':refining_sample_list,
            # 'default_container_type_line_ids':product_list
            })

        form_id = self.env.ref('ppts_project_entries.project_entries_form_view').id
        
        return{
              'name': _('Project Entry'),
              'type':'ir.actions.act_window',
              'view_type':'form',
              'view_mode':'form',
              'res_model':'project.entries',
              'views_id':False,
              'views':[(form_id or False, 'form')],
              'target':'current',
              'context':ctx,
              }
              
    def action_view_project_entry(self):

      return{
          'name': _('Project Entry'),
          'type':'ir.actions.act_window',
          'view_type':'form',
          'view_mode':'tree,form',
          'res_model':'project.entries',
          'domain' : [('origin', '=', self.id)],
          'views_id':False,
          'views':[(self.env.ref('ppts_project_entries.project_entries_tree_view').id or False, 'tree'),
                   (self.env.ref('ppts_project_entries.project_entries_form_view').id or False, 'form')],
          }

    def action_send_mask_rfq(self):
        '''
        This function opens a window to compose an email, with the demand for logistics template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('ppts_project_entries', 'email_template_mask_purchase_done')[1]
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

    def update_po_price(self):
        for line in self.order_line:
            if line.product_id.type != 'service':
                line.price_unit = self.mask_po_total/line.product_qty

class MaskPoLine(models.Model):
  _name = 'mask.po.line'

  name = fields.Char(string="Notes")

  sequence = fields.Integer(string="sequence", default=1)

  product_id = fields.Many2one('product.product', string='Product')
  description = fields.Char(string="Description")
  product_qty = fields.Float(string='Quantity',digits=(12,6) )
  product_uom = fields.Many2one('uom.uom', string='UoM')
  price_unit = fields.Float('Unit Price')
  taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
  price_subtotal = fields.Float(compute='_compute_subtotal', string='Subtotal', store=True)
  mask_po_line_id = fields.Many2one('purchase.order', string='Purchase Order ref')

  display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
  
#   update_name_field = fields.Boolean(compute="_compute_name_field")

  @api.model
  def create(self, vals):
      res = super(MaskPoLine, self).create(vals)
      res.name = str(res.product_id.name) +' - '+ str(res.product_id.product_template_attribute_value_ids.name)
      res.description = str(res.product_id.name) +' - '+ str(res.product_id.product_template_attribute_value_ids.name)

      return res

  @api.onchange('product_id')
  def onchange_product_id(self):
    if self.product_id:
      self.name = str(self.product_id.name) +' - '+ str(self.product_id.product_template_attribute_value_ids.name)
      self.description = str(self.product_id.name) +' - '+ str(self.product_id.product_template_attribute_value_ids.name)
      self.price_unit = self.product_id.lst_price
      self.product_uom = self.product_id.uom_id.id

  @api.depends('product_qty','price_unit')
  def _compute_subtotal(self):
    for line in self:
      if not line.name:
        line.name = str(line.product_id.name) +' - '+ str(line.product_id.product_template_attribute_value_ids.name)
        line.description = str(line.product_id.name) +' - '+ str(line.product_id.product_template_attribute_value_ids.name)
    #   update_name_field = line.update_name_field
      line.price_subtotal = line.product_qty * line.price_unit

#   def _compute_name_field(self):
#       count = 0
#       for line in self:
#           line.update_name_field = True
          
#           if line.display_type==False:
#             count+=1
#             line.description = str(line.product_id.name) +' - '+ str(line.product_id.product_template_attribute_value_ids.name)
#             line.name = line.description
