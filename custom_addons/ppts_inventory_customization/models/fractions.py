from odoo import fields, models, api, _
from odoo.exceptions import UserError
import math
import logging

_logger = logging.getLogger(__name__)

class ProjectFractions(models.Model):
    _name = 'project.fraction'
    _description = 'Project Fractions'

    name = fields.Char("Name")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    project_id = fields.Many2one("project.entries",string="Project ID")
    partner_ref = fields.Char('Vendor Reference')
    source_container_id = fields.Many2one("project.container", string="Source Container")

    container_weight = fields.Float("CT Remaining Weight(Kg)", compute="_compute_container_remaining_weight",readonly="1", force_save="1")
    container_weight_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    supplier_id = fields.Many2one("res.partner",string="Supplier")
    sales_team_id = fields.Many2one("res.users", string="Operator")
    worker_id = fields.Many2one("hr.employee", string="Operator")
    main_product_id = fields.Many2one("product.template",string="Primary Type")
    sub_product_id = fields.Many2one("product.product", string="Secondary Type",domain="[('product_tmpl_id','=',main_product_id)]")
    fraction_weight = fields.Float("Fraction Weight(Kg)", digits=(12,4))
    fraction_weight_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    number_of_pieces = fields.Integer("Number of pieces")
    labour_cost_dup = fields.Float("Labour Cost")
    unloading_cost_dup = fields.Float("Unloading Cost")
    reception_cost_dup = fields.Float("Reception Cost")
    tranport_cost_dup = fields.Float("Transport Cost")
    additional_purchase_cost_dup = fields.Float("Additional Purchase Cost")
    purchase_cost_dup = fields.Float("Purchase Cost")
    labour_cost = fields.Monetary('Labour Cost', currency_field='currency_id', compute='_compute_labour_cost')
    state = fields.Selection([('new', 'New'), ('closed', 'Close')], default='new')
    waste_code = fields.Char(string="Standard waste code")
    client_waste_code = fields.Char("Client waste Code")
    recipient_container_id = fields.Many2one("stock.container", "Destination Container",
                                             domain="[('is_container_full','=',False),'|',('content_type_id','=',sub_product_id),('primary_content_type_id','=',main_product_id),('state','in',('open','second_process'))]")
    production_cost = fields.Monetary('Production Cost', currency_field='currency_id', compute='_compute_production_cost')
    is_scrap = fields.Boolean(string="Is Scrap?")
    scrap_txt = fields.Char(default="Select scrap product below")
    fraction_by = fields.Selection([
        ('weight' , 'Weight'),
        ('count' , 'Count')
        ],string="Fraction By",default="weight")
    cross_dock = fields.Boolean("Cross Dock?")
    is_vrac = fields.Boolean('Is Vrac?')
    second_process = fields.Boolean("Second Process")
    remaining_rc_weight = fields.Float("Remaining Recipient Weight(Kg)", compute='_compute_remaining_weight')
    company_id = fields.Many2one('res.company', string="Company")
    rc_name = fields.Char("Recipient Name", compute="_fraction_name")
    fraction_production_cost = fields.Float('Fraction Production Cost', currency_field='currency_id', compute='_compute_fraction_production_cost')

    # @api.model
    # def default_get(self, fields_name):
    #     res = super(ProjectFractions, self).default_get(fields_name)
    #     if self._context.get('default_source_container_id'):
    #         source_id = self.env['project.container'].sudo().browse(self._context.get('default_source_container_id'))
            # res.update({'worker_id': source_id.operator_id.ids})
        # return res

    @api.onchange('source_container_id')
    def get_container_remaining_weight(self):

        if self.source_container_id:
            get_fractions = self.env['project.fraction'].sudo().search([('source_container_id','=',self.source_container_id.id)])
            total_fraction_weight = 0
            for fraction_id in get_fractions:
                total_fraction_weight += fraction_id.fraction_weight
            self.container_weight = self.source_container_id.net_gross_weight - total_fraction_weight
            res = {'domain': {
                'worker_id': "[('id', '=', False)]",
            }}
            if self.source_container_id.operator_ids:
                res['domain']['worker_id'] = "[('id', 'in', %s)]" % self.source_container_id.operator_ids.ids
            else:
                res['domain']['worker_id'] = []
            return res

    @api.onchange('recipient_container_id')
    def onchange_recipient_container_id(self):
        if self.recipient_container_id:
            self.main_product_id = self.recipient_container_id.content_type_id.product_tmpl_id.id
            self.sub_product_id = self.recipient_container_id.content_type_id.id

    def _compute_container_remaining_weight(self):
        for fraction in self:
            get_fractions = self.env['project.fraction'].sudo().search([('source_container_id','=',fraction.source_container_id.id)])

            total_fraction_weight = 0
            for fraction_id in get_fractions:
                total_fraction_weight += fraction_id.fraction_weight
            
            if fraction.second_process:
                fraction.container_weight = fraction.internal_project_id.net_weight - fraction.fraction_weight
            else:
                fraction.container_weight = fraction.source_container_id.net_gross_weight - total_fraction_weight

    def _compute_fraction_production_cost(self):
        for fraction in self:        
            product_uom = 'weight'
            for line in fraction.project_id.project_entry_ids:
                if line.product_id.fraction_by_count:
                    product_uom = 'count'
                else:
                    product_uom = 'weight'
            if product_uom == 'weight':
                quantity = 0.0
                for line in fraction.project_id.project_entry_ids:
                    quantity += line.product_qty

                if fraction.project_id.extra_purchase_cost != 0.0 and quantity != 0.0:
                    additional_cost = fraction.project_id.extra_purchase_cost / quantity
                else:
                    additional_cost = 0.0

                if fraction.source_container_id.picking_id.unloading_charges != 0.0 and quantity != 0.0:
                    unloading_cost = fraction.source_container_id.picking_id.unloading_charges / quantity
                else:
                    unloading_cost = 0.0

                if fraction.source_container_id.picking_id.reception_charges != 0.0 and quantity != 0.0:
                    reception_cost = fraction.source_container_id.picking_id.reception_charges / quantity
                else:
                    reception_cost = 0.0

                sale_price = 0.0
                if fraction.sub_product_id.uom_id.name == 'Tonne':
                    fraction_weight = fraction.fraction_weight / 1000
                else:
                    fraction_weight = fraction.fraction_weight

                if fraction.project_id.is_ecologic:
                    sale_price = fraction_weight * fraction.sub_product_id.ecologic_price
                else:
                    sale_price = fraction_weight * fraction.sub_product_id.lst_price
                calc_offer_price = 0.0
                if fraction.project_id.margin_class == 'class_a':
                    calc_offer_price = (sale_price * (1 - (fraction.project_id.company_id.sale_margin_a / 100)))
                if fraction.project_id.margin_class == 'class_b':
                    calc_offer_price = (sale_price * (1 - (fraction.project_id.company_id.sale_margin_b / 100)))
                if fraction.project_id.margin_class == 'class_c':
                    calc_offer_price = (sale_price * (1 - (fraction.project_id.company_id.sale_margin_c / 100)))

                sale_obj = self.env['sale.order'].search([('project_entree_id', '=', fraction.project_id.id)])
                final_sales_cost = 0.0
                if sale_obj:
                    additional_sales_cost = 0.0
                    for so in sale_obj:
                        additional_sales_cost += so.amount_total
                    if additional_sales_cost != 0.0:
                        if quantity != 0.0:
                            final_sales_cost = additional_sales_cost / quantity
                        else:
                            final_sales_cost = 0.0
                    else:
                        final_sales_cost = 0.00
                else:
                    final_sales_cost = 0.00

                fraction.fraction_production_cost = (calc_offer_price + additional_cost + unloading_cost + reception_cost + fraction.labour_cost) - (final_sales_cost * fraction_weight)
            else:
                quantity = 0.0
                for line in fraction.project_id.project_entry_ids:
                    quantity += line.product_qty

                if fraction.project_id.extra_purchase_cost != 0.0 and quantity != 0.0:
                    additional_cost = fraction.project_id.extra_purchase_cost / quantity
                else:
                    additional_cost = 0.0

                if fraction.source_container_id.picking_id.unloading_charges != 0.0 and quantity != 0.0:
                    unloading_cost = fraction.source_container_id.picking_id.unloading_charges / quantity
                else:
                    unloading_cost = 0.0

                if fraction.source_container_id.picking_id.reception_charges != 0.0 and quantity != 0.0:
                    reception_cost = fraction.source_container_id.picking_id.reception_charges / quantity
                else:
                    reception_cost = 0.0
               
                sale_price = 0.0
                
                number_of_pieces = fraction.number_of_pieces

                if fraction.project_id.is_ecologic:
                    sale_price = number_of_pieces * fraction.sub_product_id.ecologic_price
                else:
                    sale_price = number_of_pieces * fraction.sub_product_id.lst_price

                calc_offer_price = 0.0
                if fraction.project_id.margin_class == 'class_a':
                    calc_offer_price = (sale_price * (1 - (fraction.project_id.company_id.sale_margin_a / 100)))
                if fraction.project_id.margin_class == 'class_b':
                    calc_offer_price = (sale_price * (1 - (fraction.project_id.company_id.sale_margin_b / 100)))
                if fraction.project_id.margin_class == 'class_c':
                    calc_offer_price = (sale_price * (1 - (fraction.project_id.company_id.sale_margin_c / 100)))

                sale_obj = self.env['sale.order'].search([('project_entree_id', '=', fraction.project_id.id)])
                final_sales_cost = 0.0
                if sale_obj:
                    additional_sales_cost = 0.0
                    for so in sale_obj:
                        additional_sales_cost += so.amount_total
                    if additional_sales_cost != 0.0:
                        if quantity != 0.0:
                            final_sales_cost = additional_sales_cost / quantity
                        else:
                            final_sales_cost = 0.0
                    else:
                        final_sales_cost = 0.00
                else:
                    final_sales_cost = 0.00

                fraction.fraction_production_cost = (calc_offer_price + additional_cost + unloading_cost + reception_cost + fraction.labour_cost) - (final_sales_cost * number_of_pieces)


    @api.depends('recipient_container_id')
    def _fraction_name(self):
        for fraction in self:
            fraction.update({
                'rc_name': fraction.recipient_container_id.name,
            })

    @api.depends('recipient_container_id')
    def _compute_remaining_weight(self):
        for fraction in self:
            remaining_weight = 0
            if fraction.recipient_container_id:
                    remaining_weight = self.recipient_container_id.max_weight - self.recipient_container_id.net_weight
            fraction.update({
                'remaining_rc_weight': remaining_weight,
            })

    # @api.onchange('recipient_container_id')
    # def onchange_recipient_container_id(self):
    #     if self.recipient_container_id:
    #         print("--------------------sss")
    #         self.write({
    #                 'recipient_container_id': self.recipient_container_id.id
    #             })

    @api.onchange('number_of_pieces')
    @api.depends('number_of_pieces')
    def onchange_number_of_pieces(self):

        if self.number_of_pieces:
            if self.sub_product_id.product_template_attribute_value_ids.uom_id.uom_type == 'bigger':
                final_weight = (self.sub_product_id.product_template_attribute_value_ids.piece_weight / self.sub_product_id.product_template_attribute_value_ids.uom_id.factor_inv) * self.number_of_pieces
            elif self.sub_product_id.product_template_attribute_value_ids.uom_id.uom_type == 'smaller':
                final_weight = ((self.sub_product_id.product_template_attribute_value_ids.piece_weight / self.sub_product_id.product_template_attribute_value_ids.uom_id.factor) * self.number_of_pieces)
            else:
                final_weight = self.sub_product_id.product_template_attribute_value_ids.piece_weight * self.number_of_pieces

            self.fraction_weight = final_weight

    @api.onchange('sub_product_id')
    def onchange_sub_product_id(self):
        if self.sub_product_id.product_waste_code:
            self.waste_code = self.sub_product_id.product_waste_code

        if self.sub_product_id.fraction_by_count:
            self.fraction_by = 'count'
        else:
            self.fraction_by = 'weight'

    @api.onchange('source_container_id')
    def _onchange_project_id(self):
        if self.source_container_id:
            return {
                'domain': {'worker_id': [('id', 'in', self.source_container_id.worker_ids.ids)]},
            }

    @api.onchange('is_scrap')
    def _onchange_scrap(self):
        if self.is_scrap:
            return {
                'domain': {'recipient_container_id': [('is_scrap_container', '=', True)]},
            }

    # @api.onchange('is_vrac')
    # def _onchange_vrac(self):
    #     if self.is_vrac:
    #         return {
    #             'domain': {'recipient_container_id': [('is_vrac', '=', True)]},
    #         }

    def _compute_labour_cost(self):
        for fraction in self:
            if fraction.is_vrac:
                if fraction.company_id.vrac_cost:
                    qty = 0.0
                    if fraction.sub_product_id.uom_id.name == 'Tonne':
                        qty = fraction.fraction_weight / 1000
                    # elif fraction.sub_product_id.uom_id.uom_type == 'kg':
                    #     qty = fraction.fraction_weight * 1000
                    else:
                        qty = fraction.fraction_weight
                    fraction.update({
                        'labour_cost': fraction.company_id.vrac_cost * qty,
                        'labour_cost_dup': fraction.company_id.vrac_cost * qty
                    })
                else:
                    fraction.update({
                        'labour_cost': 0.0,
                        'labour_cost_dup': 0.0
                    })
            else:
                if fraction.source_container_id.total_time == 0.0:
                    real_time = fraction.source_container_id.manual_time
                else:
                    real_time = fraction.source_container_id.total_time

                hr, min = divmod(real_time, 60)
                hours = float(("%02d" % (hr)))
                minutes = float(("%02d" % (min)))
                hourly_amount = 0.0
                if fraction.source_container_id.standard_rate:
                    hourly_amount += self.env.company.standard_rate
                else:
                    hourly_amount = hourly_amount
                if fraction.source_container_id.ea_rate:
                    hourly_amount += self.env.company.ea_rate
                else:
                    hourly_amount = hourly_amount
                if fraction.source_container_id.contractor_rate:
                    hourly_amount += self.env.company.contract_rate
                else:
                    hourly_amount = hourly_amount
                total_hourly_rate = ((hours) * hourly_amount) + (minutes * hourly_amount * (1.0 / 60))

                # if fraction.fraction_by =='weight':
                if math.ceil(fraction.source_container_id.net_gross_weight) != 0:
                    fraction_hourly_rate = (fraction.fraction_weight/fraction.source_container_id.net_gross_weight)*total_hourly_rate
                else:
                    fraction_hourly_rate = 0.0
                fraction.update({
                        'labour_cost' : fraction_hourly_rate,
                        'labour_cost_dup': fraction_hourly_rate
                    })
                # else:
                #     if fraction.source_container_id.quantity != 0:
                #         fraction_hourly_rate = (fraction.number_of_pieces/fraction.source_container_id.quantity)*total_hourly_rate
                #     else:
                #         fraction_hourly_rate = 0.0
                #     fraction.update({
                #             'labour_cost' : fraction_hourly_rate
                #         })



    @api.depends('labour_cost', 'source_container_id.container_cost')
    def _compute_production_cost(self):
        for fraction in self:
            if fraction.second_process:
                if fraction.source_container_id.child_container_ids:
                    container_cost = 0.00
                    weight = 0.00
                    for line in fraction.source_container_id.child_container_ids:
                        container_cost += line.parent_rc_id.forecast_sale_price
                        weight += line.parent_rc_id.gross_weight
                    fraction.production_cost = ((container_cost * fraction.fraction_weight)/(weight)) + fraction.labour_cost
                    # fraction.fraction_weight * container_cost
                elif fraction.source_container_id.parent_rc_id.net_weight != 0.00:
                    fraction.production_cost = ((fraction.source_container_id.parent_rc_id.container_cost * fraction.fraction_weight)/(fraction.source_container_id.parent_rc_id.net_weight)) + fraction.labour_cost
                else:
                    fraction.production_cost = 0.00
            else:
                credit_note_obj = self.env['account.move'].search([('project_id', '=', fraction.project_id.id),('type', '=', 'in_refund')])
                dc_container_obj = self.env['project.container'].search([(('project_id', '=', fraction.project_id.id))])
                non_conformity_charges = 0.00
                if dc_container_obj:
                    for dc in dc_container_obj:
                        non_conformity_charges = dc.penalty_amount
                product_uom = 'weight'
                for line in fraction.project_id.origin.order_line:
                    if line.product_id.fraction_by_count:
                        product_uom = 'count'
                    else:
                        product_uom = 'weight'
                if product_uom == 'weight':
                    if fraction.fraction_by == 'weight':
                        quantity = 0.0
                        production_cost = 0.0
                        product_offer_price = 0.00
                        total_credit = 0.0
                        for line in fraction.project_id.origin.order_line:
                            quantity += line.product_qty

                        for line in fraction.project_id.origin.mask_po_line_ids:
                            if line.product_id == fraction.sub_product_id:
                                product_offer_price = line.price_unit
                            else:
                                product_offer_price = product_offer_price

                        for credit_note in credit_note_obj:
                            total_credit += credit_note.amount_total

                        fraction_offer_price = (fraction.fraction_weight/1000)*product_offer_price

                        if quantity != 0.00:
                            fraction_purchase_cost = ((fraction.fraction_weight/1000)/quantity)*fraction.project_id.extra_purchase_cost
                            fraction_unloading_cost = ((fraction.fraction_weight/1000)/quantity)*fraction.source_container_id.picking_id.unloading_charges
                            fraction_reception_cost = ((fraction.fraction_weight/1000)/quantity)*fraction.source_container_id.picking_id.reception_charges
                            fraction_credit = ((fraction.fraction_weight/1000)/quantity)*total_credit
                            fraction_non_conformity_charges = ((fraction.fraction_weight/1000))*non_conformity_charges

                            fraction.additional_purchase_cost_dup = ((fraction.fraction_weight/1000)/quantity)*fraction.project_id.extra_purchase_cost
                            fraction.unloading_cost_dup = ((fraction.fraction_weight/1000)/quantity)*fraction.source_container_id.picking_id.unloading_charges
                            fraction.reception_cost_dup = ((fraction.fraction_weight/1000)/quantity)*fraction.source_container_id.picking_id.reception_charges
                            fraction.tranport_cost_dup = ((fraction.fraction_weight/1000)/quantity)*fraction.project_id.confirmed_transport_cost
                            fraction.purchase_cost_dup = fraction_offer_price
                        else:
                            fraction_purchase_cost = 0.00
                            fraction_unloading_cost = 0.00
                            fraction_reception_cost = 0.00
                            fraction_credit = 0.00
                            fraction_non_conformity_charges = 0.00

                            fraction.additional_purchase_cost_dup = 0.00
                            fraction.unloading_cost_dup = 0.00
                            fraction.reception_cost_dup = 0.00
                            fraction.tranport_cost_dup = 0.00
                            fraction.purchase_cost_dup = 0.00

                        if fraction.is_vrac:
                            qty = 0.0
                            if fraction.sub_product_id.uom_id.name == 'Tonne':
                                qty = fraction.fraction_weight / 1000
                            else:
                                qty = fraction.fraction_weight
                            fraction.production_cost = fraction.company_id.vrac_cost * qty
                        else:
                            fraction.production_cost = (fraction_offer_price + fraction_purchase_cost + fraction_unloading_cost + fraction_reception_cost + fraction.labour_cost + fraction_non_conformity_charges) - fraction_credit
                    else:
                        quantity = 0.0
                        production_cost = 0.0
                        product_offer_price = 0.00
                        fraction_weight = 0.00
                        total_credit = 0.0
                        for line in fraction.project_id.origin.order_line:
                            quantity += line.product_qty

                        for line in fraction.project_id.origin.mask_po_line_ids:
                            if line.product_id == fraction.sub_product_id:
                                product_offer_price = line.price_subtotal
                                if line.product_uom.name == 'Tonne':
                                    fraction_weight = line.product_qty*1000
                                elif line.product_uom.name == 'Units' or line.product_uom.name == 'Unités':
                                    product_fraction_obj = self.env['project.fraction'].search([('project_id', '=', fraction.project_id.id),('sub_product_id', '=', fraction.sub_product_id.id)])
                                    if product_fraction_obj:
                                        for product_fraction in product_fraction_obj:
                                            fraction_weight += product_fraction.fraction_weight
                                    else:
                                        fraction_weight = fraction_weight
                                    recipient_obj = self.env['stock.container'].search([('project_id', '=', fraction.project_id.id),('content_type_id', '=', fraction.sub_product_id.id)])
                                    if recipient_obj:
                                        for rc in recipient_obj:
                                            fraction_weight += rc.net_weight
                                    else:
                                        fraction_weight = fraction_weight
                                else:
                                    fraction_weight = line.product_qty
                            else:
                                product_offer_price = product_offer_price

                        for credit_note in credit_note_obj:
                            total_credit += credit_note.amount_total
                        if fraction_weight != 0.00:
                            weight_per_piece = product_offer_price/fraction_weight
                        else:
                            weight_per_piece = 0.00

                        fraction_offer_price = (fraction.fraction_weight)*weight_per_piece

                        if quantity != 0.00:
                            fraction_purchase_cost = ((fraction.fraction_weight/1000)/quantity)*fraction.project_id.extra_purchase_cost
                            fraction_unloading_cost = ((fraction.fraction_weight/1000)/quantity)*fraction.source_container_id.picking_id.unloading_charges
                            fraction_reception_cost =((fraction.fraction_weight/1000)/quantity)*fraction.source_container_id.picking_id.reception_charges
                            fraction_credit = ((fraction.fraction_weight/1000)/quantity)*total_credit
                            fraction_non_conformity_charges = ((fraction.fraction_weight/1000))*non_conformity_charges

                            fraction.additional_purchase_cost_dup = ((fraction.fraction_weight/1000)/quantity)*fraction.project_id.extra_purchase_cost
                            fraction.unloading_cost_dup = ((fraction.fraction_weight/1000)/quantity)*fraction.source_container_id.picking_id.unloading_charges
                            fraction.reception_cost_dup = ((fraction.fraction_weight/1000)/quantity)*fraction.source_container_id.picking_id.reception_charges
                            fraction.tranport_cost_dup = ((fraction.fraction_weight/1000)/quantity)*fraction.project_id.confirmed_transport_cost
                            fraction.purchase_cost_dup = fraction_offer_price
                        else:
                            fraction_purchase_cost = 0.00
                            fraction_unloading_cost = 0.00
                            fraction_reception_cost = 0.00
                            fraction_credit = 0.00
                            fraction_non_conformity_charges = 0.00

                            fraction.additional_purchase_cost_dup = 0.00
                            fraction.unloading_cost_dup = 0.00
                            fraction.reception_cost_dup = 0.00
                            fraction.tranport_cost_dup = 0.00
                            fraction.purchase_cost_dup = 0.00

                        if fraction.is_vrac:
                            qty = 0.0
                            if fraction.sub_product_id.uom_id.name == 'Tonne':
                                qty = fraction_weight / 1000
                            else:
                                qty = fraction_weight
                            fraction.production_cost = fraction.company_id.vrac_cost * qty
                        else:
                            fraction.production_cost = (fraction_offer_price + fraction_purchase_cost + fraction_unloading_cost + fraction_reception_cost + fraction.labour_cost + fraction_non_conformity_charges) - fraction_credit
                else:
                    quantity = 0.0
                    production_cost = 0.0
                    product_offer_price = 0.00
                    total_credit = 0.0
                    for line in fraction.project_id.origin.order_line:
                        quantity += line.product_qty

                    for line in fraction.project_id.origin.mask_po_line_ids:
                        if line.product_id == fraction.sub_product_id:
                            product_offer_price = line.price_unit
                        else:
                                product_offer_price = product_offer_price

                    for credit_note in credit_note_obj:
                        total_credit += credit_note.amount_total

                    fraction_offer_price = (fraction.number_of_pieces)*product_offer_price

                    if quantity != 0.00:
                        fraction_purchase_cost = ((fraction.number_of_pieces)/quantity)*fraction.project_id.extra_purchase_cost
                        fraction_unloading_cost = ((fraction.number_of_pieces)/quantity)*fraction.source_container_id.picking_id.unloading_charges
                        fraction_reception_cost =((fraction.number_of_pieces)/quantity)*fraction.source_container_id.picking_id.reception_charges
                        fraction_credit = ((fraction.number_of_pieces)/quantity)*total_credit
                        fraction_non_conformity_charges = ((fraction.number_of_pieces))*non_conformity_charges

                        fraction.additional_purchase_cost_dup = ((fraction.number_of_pieces/1000)/quantity)*fraction.project_id.extra_purchase_cost
                        fraction.unloading_cost_dup = ((fraction.number_of_pieces/1000)/quantity)*fraction.source_container_id.picking_id.unloading_charges
                        fraction.reception_cost_dup = ((fraction.number_of_pieces/1000)/quantity)*fraction.source_container_id.picking_id.reception_charges
                        fraction.tranport_cost_dup = ((fraction.number_of_pieces/1000)/quantity)*fraction.project_id.confirmed_transport_cost
                        fraction.purchase_cost_dup = fraction_offer_price
                    else:
                        fraction_purchase_cost = 0.00
                        fraction_unloading_cost = 0.00
                        fraction_reception_cost = 0.00
                        fraction_credit = 0.00
                        fraction_non_conformity_charges = 0.00

                        fraction.additional_purchase_cost_dup = 0.00
                        fraction.unloading_cost_dup = 0.00
                        fraction.reception_cost_dup = 0.00
                        fraction.tranport_cost_dup = 0.00
                        fraction.purchase_cost_dup = 0.00

                    if fraction.is_vrac:
                        qty = fraction.number_of_pieces
                        fraction.production_cost = fraction.company_id.vrac_cost * qty
                    else:
                        fraction.production_cost = (fraction_offer_price + fraction_purchase_cost + fraction_unloading_cost + fraction_reception_cost + fraction.labour_cost + fraction_non_conformity_charges) - fraction_credit

    @api.model
    def create(self, vals):

        project_obj = self.env['project.entries'].browse(vals.get("project_id"))

        source_container_id = self.env['project.container'].browse(vals.get("source_container_id"))
        ir_sequence_id = False
        if source_container_id.state == 'close':
            raise UserError(_('Fraction can not be created, because the source container is closed!'))
        if source_container_id:
            ir_sequence_id = self.env['ir.sequence'].search([('code', '=', source_container_id.name)])
            if ir_sequence_id:
                vals['name'] = str(source_container_id.name) + '/' + str(self.env['ir.sequence'].next_by_code(str(source_container_id.name))) or '/'
        if not source_container_id and vals.get('is_vrac') == True:
            vals['name'] = str(self.env['internal.project'].browse(vals.get("internal_project_id")).name) + '/' + str(self.env['ir.sequence'].next_by_code('recipient.container.seq')) or '/'
            ir_sequence_id = True
        if not ir_sequence_id:
            sequence_id = self.env['ir.sequence'].create({'name': source_container_id.name, 'code': source_container_id.name, 'prefix': 'F', 'padding': 4, 'number_increment': 1, 'number_next_actual': 1})
            if sequence_id:
                vals['name'] = str(source_container_id.name) + '/' + str(self.env['ir.sequence'].next_by_code(str(source_container_id.name))) or '/'

        # if source_container_id.net_weight > 0.0 and source_container_id.net_weight == source_container_id.net_gross_weight:
        #     raise UserError(_('Fraction can not be created, Weight of the fraction is greater than Container weight!'))

        container_weight = source_container_id.net_gross_weight - source_container_id.net_weight      

        #container tolerance calcualtion
        tolerance_weight = source_container_id.net_gross_weight + (source_container_id.net_gross_weight * project_obj.company_id.tolerance_percentage/100)

        maximum_allowed_weight = tolerance_weight - source_container_id.net_weight

        if not vals.get('is_vrac') and vals.get('fraction_by') == 'weight' and source_container_id.net_gross_weight > 0.0:
            if maximum_allowed_weight < vals.get("fraction_weight"):
                raise UserError(_('Fractions weight close to container weight, You can create only %s kg fraction!') % maximum_allowed_weight)


        res = super(ProjectFractions, self).create(vals)
        if source_container_id:
            res.source_container_id.fr_count +=1


        # if vals.get('recipient_container_id'):
        #     stock_container = self.env['stock.container'].browse(vals.get('recipient_container_id'))
        #     if stock_container.fraction_line_ids:
        #         for line in stock_container.fraction_line_ids:
        #             if not stock_container.is_multi_product_container:
        #                 if line.fraction_id.sub_product_id.id != vals.get('sub_product_id'):
        #                     raise UserError(_('Please add the same type of sub materials to the recipient container!'))
        return res

    def write(self, values):

        #container tolerance calcualtion
        if values.get("fraction_weight"):
            tolerance_weight = self.source_container_id.net_gross_weight + (self.source_container_id.net_gross_weight * self.company_id.tolerance_percentage/100)

            maximum_allowed_weight = tolerance_weight - (self.source_container_id.net_weight - self.fraction_weight)

            if not self.is_vrac and self.fraction_by == 'weight' and self.source_container_id.net_gross_weight > 0.0:
                if abs(maximum_allowed_weight) < values.get("fraction_weight"):
                    raise UserError(_('Fractions weight close to container weight, You can create only %s kg fraction!') % abs(maximum_allowed_weight))

        res = super(ProjectFractions, self).write(values)

        # if values.get('recipient_container_id'):
        #     stock_container = self.env['stock.container'].browse(values.get('recipient_container_id'))
        #     if stock_container.fraction_line_ids:
        #         for line in stock_container.fraction_line_ids:
        #             if not stock_container.is_multi_product_container:
        #                 if line.fraction_id.sub_product_id.id != values.get('sub_product_id'):
        #                     raise UserError(_('Please add the same type of sub materials to the recipient container!'))
        return res


    def close_fraction(self):
        if self.state == 'new':
            if self.fraction_by == 'weight':
                if self.fraction_weight <= 0.0:
                    raise UserError(_('Please add fraction weight!'))
            else:
                if self.number_of_pieces <= 0:
                    raise UserError(_('Please number of pieces in fraction!'))


            if not self.recipient_container_id:
                raise UserError(_('Please select the Recipient Container!'))

            if self.recipient_container_id.max_weight > 0.0 and self.recipient_container_id.max_weight == self.recipient_container_id.net_weight:
                raise UserError(_('Recipient Container is full, Please select/create some other container!'))

            rc_weight = self.recipient_container_id.max_weight - self.recipient_container_id.net_weight
            if rc_weight < self.fraction_weight:
                raise UserError(_('Recipient Container is almost full it can accept only %s kg, Please adjust accordingly!') % rc_weight)

            fraction_vals = []
            fraction_line = {}
            fraction_line.update({
                'name': self.name,
                'weight': self.fraction_weight,
                'number_of_pieces': self.number_of_pieces,
                'fraction_id': self.id,
                })
            fraction_vals.append((0, 0, fraction_line))
            self.recipient_container_id.container_specific = self.fraction_by
            self.recipient_container_id.fraction_line_ids = fraction_vals

            quantity = 0.00
            if self.fraction_by == 'weight':
                if self.sub_product_id.uom_id.name == 'Tonne':
                    quantity = self.fraction_weight / 1000
                else:
                    quantity = self.fraction_weight
            else:
                quantity = self.number_of_pieces

            if self.second_process:
                stock_location = self.env["stock.location"].search([("is_stock_location", '=', True), ('company_id', '=', self.internal_project_id.company_id.id)], limit=1)
            else:
                stock_location = self.env["stock.location"].search([("is_stock_location", '=', True), ('company_id', '=', self.project_id.company_id.id)], limit=1)

            stock_vals = {
                'product_id': self.sub_product_id.id,
                'location_id': stock_location.id,
                'quantity': quantity,
            }
            
            self.env["stock.quant"].sudo().create(stock_vals)

            self.state = 'closed'

    def unlink(self):
        for line in self:
            if line.source_container_id.fr_count > 0:
                line.source_container_id.fr_count -= 1
            rc_line = self.env['fraction.line'].search([('fraction_id', '=', line.id)])
            if rc_line:
                rc_line.unlink()
        return super(ProjectFractions, self).unlink()

    @api.onchange('is_scrap')
    def onchange_is_scrap(self):
        if self.is_scrap:
            self.main_product_id = False
            self.sub_product_id = False