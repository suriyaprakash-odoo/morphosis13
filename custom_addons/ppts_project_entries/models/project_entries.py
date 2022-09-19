from odoo import fields, models, api, _
from datetime import datetime
from werkzeug.urls import url_encode
from odoo.exceptions import AccessError, UserError, ValidationError
import xlwt
import os
import base64
from odoo import tools
import math

ADDONS_PATH = tools.config['addons_path'].split(",")[-1]


class ProjectEntries(models.Model):
    _name = 'project.entries'
    _inherit = ['mail.thread']
    _description = 'Project Entries'

    name = fields.Char('Name', default='New', track_visibility='onchange')
    origin = fields.Many2one('purchase.order', 'Source Document', required=1, track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', 'Vendor', required=1, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=1, track_visibility='onchange')
    partner_ref = fields.Char('Vendor Reference')
    user_id = fields.Many2one('res.users', 'Project sales manager', track_visibility='onchange')
    project_origin = fields.Many2one('res.country.state', 'Collection point for project', track_visibility='onchange')
    pickup_location_id = fields.Many2one('res.partner', string='Pickup Location') #domain="['|',('parent_id' , '=?' , partner_id),('unknown_location','=',True)]"
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    is_transport = fields.Boolean('Transported by us?', track_visibility='onchange')
    transporter_id = fields.Many2one('res.partner', 'Unique Identifier of transporter', track_visibility='onchange')
    project_type = fields.Selection([
        ('fixed_price', 'Fixed Price'),
        ('variable_price', 'Variable Price'),
        ('reuse', 'Re-use'),
        ('refine', 'Refining'),
        # ('transfer', 'Dropship'),
        # ('cross_dock', 'Cross Dock'),
        # ('dismantle_sort', 'Dismantling'),
        # ('reuse', 'Re-use'),
        # ('sorting', 'Sorting'),
        # ('refine', 'Refining'),
    ], string='Project Type', track_visibility='onchange')
    container_waste_type = fields.Selection([
        ('mixed', 'Mixed'),
        ('single', 'Monotype')
    ], 'Type of Waste in container', track_visibility='onchange')
    pricing_type = fields.Selection([
      ('fixed' , 'Fixed Price'),
      ('variable' , 'Variable Price')
      ], string="Pricing", default='fixed')
    waste_code = fields.Char('Waste Code')
    is_fifteen_days = fields.Boolean("Is 15 days notice?")
    fifteen_days_date = fields.Date("15 days treatment date")
    is_client_request_sorted = fields.Boolean('Client request sorted with report')
    is_offer_subject_to_analysis = fields.Boolean('Offer subject to analysis')
    forcased_transport_cost = fields.Monetary('Transport cost', currency_field='currency_id')
    confirmed_transport_cost = fields.Monetary('Transport cost', currency_field='currency_id')
    offer_expiry_date = fields.Date('Offer Expiry Date')
    quoted_price = fields.Monetary('Quoted Buying price', currency_field='currency_id', track_visibility='onchange')
    calculated_bying_price = fields.Monetary('Calculated Buying Price', currency_field='currency_id', compute='_compute_buying_price', track_visibility='onchange')
    target_price = fields.Monetary('Target Buying Price', currency_field='currency_id', track_visibility='onchange')
    conditional_offer = fields.Float('Conditional Offer')
    standard_tc = fields.Selection([
        ('france', 'France'),
        ('europian', 'Europian Union'),
        ('international_route', 'International Routes'),
        ('international_air', 'International Air'),
        ('international_sea', 'International Sea')
    ], string='Standard Terms & Conditions', )
    is_offer_accept = fields.Boolean('Offer Accepted')
    is_offer_reject = fields.Boolean('Reject Offer')
    reject_reason = fields.Char('Reason Offer Rejected')
    # logistics_request = fields.Binary('Logistics request')
    export_license = fields.Binary('Export License')
    project_entry_ids = fields.One2many('project.entries.line', 'project_entry_id', string='Project entries line')

    status = fields.Selection([
        ('quote', 'Quote'),
        ('in_transit', 'In Transit'),
        ('reception', 'Reception'),
        ('wip', 'Production'),
        ('srt', 'Sorted/Treated'),
        ('finished', 'Closed'),
        ('reject', 'Rejected'),
    ], string='Status', default='quote', track_visibility='onchange')

    transport_request_count = fields.Integer('Transport Requests', compute='compute_transport_request_count')
    fraction_count = fields.Integer(compute='_compute_fraction_data', string="Number of Quotations")
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    total_production_cost = fields.Monetary('Production Cost', currency_field='currency_id', compute='_compute_total_production_cost', track_visibility='onchange')
    forecast_production_cost = fields.Monetary('Production Cost', currency_field='currency_id', compute='_compute_forecast_production_cost')
    process_type_cost = fields.Monetary('Process Cost', currency_field='currency_id', compute='_compute_process_type_cost')
    labour_cost = fields.Monetary('Labour Cost', currency_field='currency_id', compute="_compute_labour_cost")
    initial_offer_price = fields.Monetary('Initial Offer Price', currency_field='currency_id')

    is_internal_project = fields.Boolean('Is Internal Project?')
    is_demand_sent = fields.Boolean('Is Logistics demand sent?')

    is_registered_package = fields.Boolean("Is Registered package collection?")
    collection_type = fields.Selection([
        ('labels', 'Labels Only'),
        ('boxes', 'Boxes Only'),
        ('labels_boxes', 'Labels and Boxes')
    ], string='Collection Type')
    no_of_boxes = fields.Integer("Number of Boxes")

    carton_ids = fields.One2many('carton.line', 'carton_id', string="Carton lines")

    notes = fields.Text("Notes")
    transport_rfq_count = fields.Integer('RFQ Count', compute='compute_transport_rfq_count', default=0)
    # computed_no_of_container = fields.Integer('No of containers duplicate', compute="_compute_total_containers")

    lorry_type = fields.Selection([
        ('container', 'container'),
        ('curtainside', 'Curtain-side'),
        ('semi_trailer', 'Semi-Trailer'),
        ('rigid_body_truck', 'Rigid Body Truck'),
        ('moving_floor', 'Moving Floor')
    ], string='Type of Lorry')
    is_full_load = fields.Boolean('Full Load?')
    is_tail_lift = fields.Boolean('Tail-Lift')
    hayons = fields.Selection([('hayons', 'Hayons'), ('hayons_t', 'Hayons + transpalette'),
                               ('hayons_te', 'Hayons + transpalette electrique')])

    no_of_container = fields.Integer(string='Number of containers', compute='_get_total_container')
    # no_of_container_duplicate = fields.Integer(string='Number of containers', related='no_of_container')
    opening_hours_start = fields.Char('Opening Hours Start')
    opening_hours_end = fields.Char('Opening Hours End')
    morning_opening_hours_start = fields.Char('Morning Opening Hours Start')
    morning_opening_hours_end = fields.Char('Morning Opening Hours End')
    evening_opening_hours_start = fields.Char('Evening Opening Hours Start')
    evening_opening_hours_end = fields.Char('Evening Opening Hours End')
    collection_date_type = fields.Selection([
        ('specific', 'Specific Date'),
        ('between', 'In between'),
        ('as_soon_as_possible', 'As soon as possible')
    ], string='Collection Date Type')
    estimated_collection_date = fields.Date('Collection Date')
    collection_date_from = fields.Date('From')
    collection_date_to = fields.Date('To')

    is_ecologic = fields.Boolean('Is Ecologic')
    command = fields.Char('Commande', size=9)
    order = fields.Char('Ordre', size=8)
    num_demande = fields.Char('Num Demande')
    ordre_de_traitement = fields.Char('Ordre de Traitement')

    silver_cost_ids = fields.One2many('silver.refining.cost', 'silver_cost_id', string="Silver Refining cost line")
    gold_cost_ids = fields.One2many('gold.refining.cost', 'gold_cost_id', string="Gold Refining cost line")
    palladium_cost_ids = fields.One2many('palladium.refining.cost', 'palladium_cost_id', string="Palladium Refining cost line")
    platinum_cost_ids = fields.One2many('platinum.refining.cost', 'platinum_cost_id', string="Platinum Refining cost line")
    copper_cost_ids = fields.One2many('copper.refining.cost', 'copper_cost_id', string="Copper Refining cost line")

    potential_sales_price = fields.Monetary('Potential Revenue', currency_field='currency_id', compute='_compute_potential_sale_price', track_visibility='onchange')

    margin_class = fields.Selection([
        ('class_a', 'Class A'),
        ('class_b', 'Class B'),
        ('class_c', 'Class C')
    ], string="Margin Class")

    purchase_ids = fields.One2many("project.purchase.orders","project_id", string="Purchase Orders")
    extra_purchase_cost = fields.Monetary(compute='_compute_extra_purchase', currency_field='currency_id', string="Additional Purchase")
    estimated_extra_purchase_cost = fields.Monetary('Additional Purchase', currency_field='currency_id')
    active = fields.Boolean("Active",default=True)

    account_ids = fields.One2many("project.account.move","project_id", string="Account ID Ref")

    rhodium_cost_ids = fields.One2many('rhodium.refining.cost', 'rhodium_cost_id', string="Rhodium Refining cost line")
    ruthenium_cost_ids = fields.One2many('ruthenium.refining.cost', 'ruthenium_cost_id', string="Ruthenium Refining cost line")
    iridium_cost_ids = fields.One2many('iridium.refining.cost', 'iridium_cost_id', string="Iridium Refining cost line")

    silver = fields.Boolean("Silver")
    gold = fields.Boolean("Gold")
    palladium = fields.Boolean("Palladium")
    platinum = fields.Boolean("Platinum")
    copper = fields.Boolean("Copper")
    rhodium = fields.Boolean("Rhodium")
    ruthenium = fields.Boolean("Ruthenium")
    iridium = fields.Boolean("iridium")

    account_payment_ids = fields.One2many(related='origin.account_payment_ids', string="Pay Purchase Advanced")
    document_ids = fields.One2many("project.documents", 'project_id', string="Project Documents")

    value_of_lot = fields.Monetary('Value of Lot', currency_field = 'currency_id', compute = '_compute_lot_value')
    actual_sale_cost = fields.Monetary('Revenue', currency_field = 'currency_id')
    forecast_profit = fields.Monetary('Profit', currency_field = 'currency_id', compute = '_compute_forecast_profit')
    calculated_profit = fields.Monetary('Calculated Profit', currency_field = 'currency_id', compute = '_compute_calculated_profit')
    calculated_profit_percentage = fields.Float('Calculated Profit(%)', compute='_compute_calculated_profit_percentage')
    actual_profit = fields.Monetary('Final Profit', currency_field = 'currency_id', compute = '_compute_actual_profit')
    production_cost_with_offer = fields.Monetary('Production Cost with Offer', currency_field = 'currency_id', compute='compute_production_cost_with_offer')
    actual_date = fields.Date("Actual Collection Date")

    date_demand = fields.Date("Date de demande")
    date_reception = fields.Date("Date Réception Données")
    send_containers = fields.Boolean("Send Containers?")
    project_container_ids = fields.One2many("project.container.line","project_id", string="Container Details")

    add_cost_existing_po = fields.Boolean(string="Include Transport in PO?",default=False)
    add_additional_sale_po = fields.Boolean(string="Include Additional Sale in PO?",default=False)

    sample_line_ids = fields.One2many('project.refining.sample', 'sample_line_id', string='Refining Samples')

    total_quantity = fields.Float(string="Total Quantity (Kg)", compute="_compute_total_quantity")
    total_offer_price = fields.Monetary(string="Total Offer Price", compute="_compute_total_offer_price")

    creation_date = fields.Date('Create Date', default=fields.Datetime.now)

    include_logistics = fields.Boolean('Does not Include Logistics')

    expected_delivery = fields.Date('Expected date of delivery', compute='_compute_expected_delivery')

    # grid_rotation = fields.Char('rotation de grille')


    def _compute_expected_delivery(self):
        transports = self.env["logistics.management"].sudo().search([('origin', '=', self.id),('status','!=','rejected')], limit=1)

        if transports:
            self.expected_delivery = transports.expected_delivery
        else:
            self.expected_delivery = False
        


    def confirm_project(self):
        self.origin.button_confirm()
        self.status = 'reception'

    def _compute_total_quantity(self):
        total_weight = 0
        for line in self.project_entry_ids:
            if line.product_id.uom_id.uom_type == 'bigger':
                total_weight += line.product_qty * line.product_id.uom_id.factor_inv
            elif line.product_id.uom_id.uom_type == 'smaller':
                total_weight += line.product_qty / line.product_id.uom_id.factor
            else:
                total_weight += line.product_qty
            
        self.total_quantity = total_weight
    
    def _compute_total_offer_price(self):
        total_price = 0
        for line in self.project_entry_ids:
            total_price += line.offer_price
        self.total_offer_price = total_price

    def create_container_action(self):
        ctx = dict()
        ctx.update({
            'default_project_id': self.id,
        })

        if self.project_type=="reuse":
            ctx.update({
            'default_project_id': self.id,
            # 'default_action_type':'re-use',
        })


        form_id = self.env.ref('ppts_inventory_customization.create_container_wizard_form').id

        return {
            'name': _('Create Containers'),
            'type': 'ir.actions.act_window',
            'res_model': 'create.container.wizard',
            'view_mode': 'form',
            'res_model': 'create.container.wizard',
            'view_id': form_id,
            'context': ctx,
            'target':'new',
        }

    @api.onchange('send_containers')
    def onchange_send_containers(self):
        if self.send_containers:
            self.is_transport = True
        else:
            self.is_transport = False

    def close_project(self):
        self.status = 'finished'

    def compute_production_cost_with_offer(self):
        for project in self:
            shipments = self.env["stock.picking"].search([('project_entry_id', '=', project.id)],limit=1)
            project.update({
                    'production_cost_with_offer' : project.total_production_cost + project.quoted_price + shipments.reception_charges
                })

    def _compute_calculated_profit(self):
        for project in self:
            if math.ceil(project.potential_sales_price) != 0 or math.ceil(project.calculated_service_profit) != 0 or math.ceil(project.metal_profit) != 0:
                if math.ceil(project.total_production_cost) != 0:
                    project.update({
                            'calculated_profit' : (project.potential_sales_price + project.calculated_service_profit + project.metal_profit) - project.total_production_cost - project.quoted_price
                        })
                else:
                    project.update({
                            'calculated_profit' : 0.0
                        })
            else:
                project.update({
                        'calculated_profit' : 0.0
                    })

    def _compute_calculated_profit_percentage(self):
        for project in self:
            if project.potential_sales_price != 0:
                project.update({
                        'calculated_profit_percentage' : (project.calculated_profit/project.potential_sales_price) * 100
                    })
            else:
                project.update({
                        'calculated_profit_percentage' : 0.0
                    })


    def _compute_actual_profit(self):
        for project in self:
            if project.actual_sale_cost != 0:
                if project.total_production_cost != 0:
                    project.update({
                            'actual_profit' : project.actual_sale_cost - project.total_production_cost - project.quoted_price
                        })
                else:
                    project.update({
                            'actual_profit' : 0.0
                        })
            else:
                project.update({
                        'actual_profit' : 0.0
                    })


    def _compute_forecast_profit(self):
        for project in self:
            if project.origin:
                if project.origin.opportunity_id:
                    additional_costs = project.forcased_transport_cost + project.estimated_extra_purchase_cost
                    project.update({
                            'forecast_profit' : project.origin.opportunity_id.cash_margin - additional_costs
                        })
                else:
                    project.update({
                            'forecast_profit' : 0.0
                        })
            else:
                project.update({
                    'forecast_profit' : 0.0
                })

    def _compute_forecast_production_cost(self):
        for project in self:
            project.update({
                    'forecast_production_cost' : project.forcased_transport_cost + project.process_type_cost
                })

    def _compute_lot_value(self):
        for project in self:
            if project.origin:
                if project.origin.opportunity_id:
                    value_of_lot = 0.0
                    for line in project.origin.opportunity_id.product_lines:
                        value_of_lot += line.quantity * line.price_per_ton
                    project.update({
                            'value_of_lot' : value_of_lot
                        })
                else:
                    project.update({
                            'value_of_lot' : 0.0
                        })
            else:
                project.update({
                        'value_of_lot' : 0.0
                    })

    def _compute_process_type_cost(self):
        for project in self:
            if project.origin:
                if project.origin.opportunity_id:
                    processing_cost = 0.0
                    for line in project.origin.opportunity_id.product_lines:
                        for process in line.process_type:
                            processing_cost += process.estimated_production_cost
                    project.update({
                            'process_type_cost' : processing_cost
                        })
                else:
                    project.update({
                        'process_type_cost' : 0.00
                    })
            else:
                project.update({
                    'process_type_cost' : processing_cost
                })

    def _compute_labour_cost(self):
        for project in self:
            shipments = self.env["stock.picking"].search([('project_entry_id', '=', project.id)],limit=1)
            labour_cost = 0.0
            if shipments:
                for shipment in shipments:
                    print('--',shipment.unloading_charges,'--')
                    if shipment:
                        containers = self.env["project.container"].search([('picking_id', '=', shipment.id)])
                        recipient_container_obj = self.env['stock.container'].search([('project_id', '=', project.id),('picking_id', '=', shipment.id)])
                        if containers:
                            for container in containers:
                                fractions = self.env["project.fraction"].search([('source_container_id', '=', container.id)])
                                if fractions:
                                    for fraction in fractions:
                                        labour_cost += fraction.labour_cost
                                    project.update({
                                        'labour_cost': labour_cost + shipment.unloading_charges
                                    })
                                else:
                                    project.update({
                                        'labour_cost': labour_cost + shipment.unloading_charges
                                    })
                        else:
                            project.update({
                                'labour_cost': labour_cost + shipment.unloading_charges
                            })
                        if recipient_container_obj:
                            for rc in recipient_container_obj:
                                labour_cost += (rc.forecast_sale_price - rc.container_cost)
                            project.update({
                                'labour_cost' : labour_cost + shipment.unloading_charges
                            })
                        else:
                            project.update({
                                'labour_cost' : labour_cost + shipment.unloading_charges
                            })
                    else:
                        project.update({
                            'labour_cost': labour_cost + shipment.unloading_charges
                        })
            else:
                project.update({
                    'labour_cost': labour_cost
                })

    def additional_purchase_order(self):
        ctx = dict()
        ctx.update({
            'default_project_entry_id': self.id,
            'default_is_internal_purchase':True,
            'default_partner_id':self.partner_id.id
        })
        return {
            'name': _('Purchase Order'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree, form',
            'res_model': 'purchase.order',
            'views_id': False,
            'views': [(self.env.ref('purchase.purchase_order_form').id, 'form')],
            'context': ctx
        }

    def action_create_credit_note(self):
        ctx = dict()
        ctx.update({
                'default_invoice_origin': self.origin.name,
                'default_project_id': self.id,
                'default_type': 'in_refund',
                'default_partner_id': self.partner_id.id,
            })

        return {
            'name': _('Vendor Credit Note'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree, form',
            'res_model': 'account.move',
            'views_id': False, 
            'views': [(self.env.ref('account.view_move_form').id, 'form')],
            'context': ctx
        }

    @api.depends('purchase_ids.untaxed_amount')
    def _compute_extra_purchase(self):
        for project_entry in self:
            total = 0
            if project_entry.is_registered_package:
                if project_entry.purchase_ids:
                    for purchase in project_entry.purchase_ids:
                        total += purchase.untaxed_amount
                total += project_entry.confirmed_transport_cost
            else:
                if project_entry.purchase_ids:
                    for purchase in project_entry.purchase_ids:
                        total += purchase.untaxed_amount
            project_entry.update({
                'extra_purchase_cost': total,
            })


    @api.depends('project_entry_ids')
    def _get_total_container(self):
        for project_entry in self:
            total_container = 0
            for project in project_entry.project_entry_ids:
                total_container += project.container_count
            # logistics_obj = self.env['logistics.management'].search([('origin' , '=' , project_entry.id)])
            # if logistics_obj:
            #     for logistics in logistics_obj:
            #         logistics.no_of_container = total_container
            # else:
            #     pass
        project_entry.update({
            'no_of_container': total_container,
        })

    def _compute_potential_sale_price(self):
        for project in self:
            if project.status == 'srt' or project.status == 'wip' or project.status == 'finished':
                container_obj = self.env['project.container'].search([('project_id', '=', project.id)])
                sales_cost = 0.0
                if container_obj:
                    # sales_cost = 0.00
                    for container in container_obj:
                        fraction_obj = self.env['project.fraction'].search([('source_container_id', '=', container.id)])
                        if fraction_obj:
                            for fraction in fraction_obj:
                                fraction_cost = 0

                                for pe_line in project.project_entry_ids:
                                    if pe_line.product_id == fraction.sub_product_id:
                                        product_price = pe_line.price_unit
                                    else:
                                        product_price = fraction.sub_product_id.lst_price if project.is_ecologic else fraction.sub_product_id.lst_price

                                if fraction.fraction_by == 'weight':
                                    if fraction.sub_product_id.uom_id.name == 'Tonne':
                                        fraction_cost = (fraction.fraction_weight/1000) * product_price
                                    else:
                                        fraction_cost = fraction.fraction_weight * product_price
                                else:
                                    fraction_cost = fraction.number_of_pieces * product_price
                                sales_cost += fraction_cost
                        else:
                            project.update({
                                'potential_sales_price': project.potential_sales_price
                            })
                    if sales_cost != 0:
                        project.update({
                            'potential_sales_price': sales_cost
                        })
                    else:
                        project.update({
                            'potential_sales_price': 0.00
                        })
                else:
                    project.update({
                        'potential_sales_price': project.potential_sales_price
                    })
                recipient_container_obj = self.env['stock.container'].search([('project_id', '=', project.id)])
                if recipient_container_obj:

                    for container in recipient_container_obj:
                        for pe_line in project.project_entry_ids:
                            if pe_line.product_id == container.content_type_id:
                                product_price = pe_line.price_unit
                            else:
                                product_price = container.content_type_id.lst_price if project.is_ecologic else container.content_type_id.lst_price

                        if container.container_specific == 'weight':
                            if container.content_type_id.uom_id.name == 'Tonne':
                                sales_cost += (container.net_weight_dup/1000) * product_price
                            else:
                                sales_cost += container.net_weight_dup * product_price
                        else:
                            sales_cost += container.total_number_of_pieces_dup * product_price

                    if sales_cost != 0.0:
                        project.update({
                            'potential_sales_price' : sales_cost
                        })
                    else:
                        project.update({
                            'potential_sales_price' : project.potential_sales_price
                        })
                else:
                    project.update({
                        'potential_sales_price' : project.potential_sales_price
                    })
            else:
                project.update({
                    'potential_sales_price': 0.00
                })

    def name_get(self):
        result = []
        for record in self:
            if record.partner_id.company_type == 'company':
                name = record.name + ' [' + record.partner_id.name + ']'
                result.append((record.id, name))
            elif record.partner_id.company_type == 'person' and record.partner_id.parent_id:
                name = record.name + ' [' + record.partner_id.parent_id.name + ']'
                result.append((record.id, name))
            else:
                name = record.name
                result.append((record.id, name))
        return result

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.street = self.partner_id.street
            self.street2 = self.partner_id.street2
            self.city = self.partner_id.city
            self.state_id = self.partner_id.state_id
            self.zip = self.partner_id.zip
            self.country_id = self.partner_id.country_id
           
            # self.is_tail_lift = self.partner_id.is_tail_lift
            # self.hayons = self.partner_id.hayons
            # self.grid_rotation = self.partner_id.grid_rotation
        
    
    @api.onchange('pickup_location_id')
    def onchange_pickup_location_id(self):
        if self.pickup_location_id:
            self.morning_opening_hours_start = self.pickup_location_id.morning_opening_hours_start
            self.morning_opening_hours_end = self.pickup_location_id.morning_opening_hours_end
            self.evening_opening_hours_start = self.pickup_location_id.evening_opening_hours_start
            self.evening_opening_hours_end = self.pickup_location_id.evening_opening_hours_end

            self.is_tail_lift = self.pickup_location_id.is_tail_lift
            self.hayons = self.pickup_location_id.hayons
            # self.grid_rotation = self.pickup_location_id.grid_rotation
        
        elif self.partner_id:
            self.morning_opening_hours_start = self.partner_id.morning_opening_hours_start
            self.morning_opening_hours_end = self.partner_id.morning_opening_hours_end
            self.evening_opening_hours_start = self.partner_id.evening_opening_hours_start
            self.evening_opening_hours_end = self.partner_id.evening_opening_hours_end

            self.is_tail_lift = self.partner_id.is_tail_lift
            self.hayons = self.partner_id.hayons
            # self.grid_rotation = self.partner_id.grid_rotation
        

    # @api.depends('project_entry_ids')
    # def _compute_total_containers(self):
    #     for rec in self:
    #         for line in rec.project_entry_ids:
    #             if line.container_count != 0:
    #                 rec.computed_no_of_container += line.container_count
    #             else:
    #                 rec.computed_no_of_container = rec.computed_no_of_container

    # @api.onchange('computed_no_of_container')
    # def onchange_computed_no_of_container(self):
    #     if self.computed_no_of_container != 0.00:
    #         self.no_of_container = self.computed_no_of_container

    def _compute_total_production_cost(self):
        for project in self:
            if project.project_type == 'refine':
                mo_id = self.env["mrp.production"].search([('project_id', '=', self.id),('state', '=', 'done')],limit=1)
                if mo_id:
                    project.update({
                        'total_production_cost': project.extra_purchase_cost + mo_id.production_total
                    })
                else:
                    project.update({
                        'total_production_cost': project.extra_purchase_cost
                    })
            else:
                project.update({
                    'total_production_cost': project.extra_purchase_cost + project.labour_cost
                })
            # shipments = self.env["stock.picking"].search([('project_entry_id', '=', project.id)])
            # production_cost = 0.0
            # if shipments:
            #     for shipment in shipments:
            #         if shipment:
            #             containers = self.env["project.container"].search([('picking_id', '=', shipment.id)])
            #             if containers:
            #                 for container in containers:
            #                     fractions = self.env["project.fraction"].search([('source_container_id', '=', container.id)])
            #                     if fractions:
            #                         for fraction in fractions:
            #                             production_cost += fraction.production_cost
            #                             project.update({
            #                                 'total_production_cost': production_cost + project.extra_purchase_cost
            #                             })
            #                     else:
            #                         project.update({
            #                             'total_production_cost': production_cost + project.extra_purchase_cost
            #                         })
            #             else:
            #                 project.update({
            #                     'total_production_cost': production_cost + project.extra_purchase_cost
            #                 })
            #         else:
            #             project.update({
            #                 'total_production_cost': production_cost + project.extra_purchase_cost
            #             })
            # else:
            #     project.update({
            #         'total_production_cost': production_cost + project.extra_purchase_cost
            #     })

    def _compute_buying_price(self):
        for project in self:

            if project.total_production_cost != 0:
                for line in project.project_entry_ids:

                    product_price = line.product_id.ecologic_price if project.is_ecologic else line.product_id.lst_price

                    if project.margin_class == 'class_a':
                        project.calculated_bying_price += (((product_price * line.product_qty) * (1 - (project.company_id.sale_margin_a / 100))) -  project.total_production_cost)
                    elif project.margin_class == 'class_b':
                        project.calculated_bying_price += (((product_price * line.product_qty) * (1 - (project.company_id.sale_margin_b / 100))) -  project.total_production_cost)
                    else:
                        project.calculated_bying_price += (((product_price * line.product_qty) * (1 - (project.company_id.sale_margin_c / 100))) -  project.total_production_cost)
            else:
                project.calculated_bying_price = 0.00

    def compute_transport_request_count(self):
        transport_obj = self.env['logistics.management'].search([('origin', '=', self.id)])

        self.transport_request_count = len(transport_obj)

    def compute_transport_rfq_count(self):
        for rec in self:
            transport_rfq_obj = self.env['purchase.order'].search([('origin', '=', rec.origin.name)])
            if transport_rfq_obj:
                rec.transport_rfq_count = len(transport_rfq_obj)
            else:
                rec.transport_rfq_count = 0

    def action_alert_logistics(self):
        '''
        This function opens a window to compose an email, with the demand for logistics template message loaded by default
        '''
        if self.partner_ref == False:
            raise ValidationError(_('Vendor is not Created'))
        # elif self.lorry_type == False:
        #     raise ValidationError(_('Lorry Type is not Created'))
        elif self.pickup_location_id == False:
            raise ValidationError(_('PickUp Location is not Created'))
        elif self.total_quantity == False:
            raise  ValidationError(_('Total Quantity is not Created'))
        # elif self.morning_opening_hours_start == False:
        #     raise ValidationError(_('Morning Opening Hours is not Created'))
        # elif self.morning_opening_hours_end == False:
        #     raise ValidationError(_('Morning Ending Hour is not Created'))
        # elif self.evening_opening_hours_start == False:
        #     raise ValidationError(_('Evening Opening Hours is not Created'))
        # elif self.evening_opening_hours_end == False:
        #     raise ValidationError(_('Evening Ending Hour is not Created'))
        else:
            self.ensure_one()


        ctx = dict(self.env.context or {})
        ctx.update({
            'default_pickup_partner_id': self.pickup_location_id.id,
            'default_container_count': self.no_of_container,
            'default_collection_date_type':self.collection_date_type,
            'default_lorry_type': self.lorry_type,
            'default_pickup_date': self.estimated_collection_date,
            'default_pickup_earliest_date': self.collection_date_from,
            'default_pickup_latest_date': self.collection_date_to,
            'default_gross_weight': self.total_quantity,
            'default_is_full_load': self.is_full_load,
            'default_is_tail_lift': self.is_tail_lift,
            'default_hayons': self.hayons,
            'default_grid_rotation': self.partner_id.grid_rotation,
        })

        return {
            'name': _('Transport Notification'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'transport.popup',
            'target': 'new',
            'context':ctx,
        }

    def generate_sorting_report(self):

        containers_obj = self.env['project.container'].search([('project_id', '=', self.id)])

        list = []
        workbook = xlwt.Workbook()

        sheet = workbook.add_sheet('Fraction Sorting Report', cell_overwrite_ok=True)
        sheet.show_grid = False
        sheet.col(1).width = 256 * 25
        sheet.col(2).width = 256 * 25
        sheet.col(3).width = 256 * 25
        sheet.col(4).width = 256 * 25
        sheet.col(5).width = 256 * 25
        sheet.col(6).width = 256 * 25
        sheet.col(7).width = 256 * 25

        style01 = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color gray40,bottom_color gray40,right_color gray40,left_color gray40,left thin,right thin,top thin,bottom thin;')
        style02 = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color gray40,bottom_color gray40,right_color gray40,left_color gray40,left thin,right thin,top thin,bottom thin;')
        style03 = xlwt.easyxf('font: name Times New Roman,color-index black,bold on,italic on; border:top_color gray40,bottom_color gray40,right_color gray40,left_color gray40,left thin,right thin,top thin,bottom thin;')
        style04 = xlwt.easyxf('font: name Times New Roman,color-index green ; border:top_color gray40,bottom_color gray40,right_color gray40,left_color gray40,left thin,right thin,top thin,bottom thin;')

        total_weight = 0.00
        weight_uom_id = ''
        for line in self.project_entry_ids:
            if line.product_uom.name == 'Tonne':
                total_weight += (line.product_qty * 1000)
            else:
                total_weight += line.product_qty
            weight_uom_id = line.product_uom.name

        gross_weight = str(total_weight) + ' Kg'

        sorted_qty = 0.00

        sheet.write(0, 0, 'Référence du Projet', style01)
        sheet.write(0, 1, self.name, style01)
        sheet.write(1, 0, 'Client', style01)
        sheet.write(1, 1, self.partner_id.name, style01)
        sheet.write(2, 0, 'Poids Net', style01)
        sheet.write(2, 1, gross_weight, style01)

        n = 4
        n += 0

        sheet.write(n, 0, 'Référence de la Fraction', style01)
        sheet.write(n, 1, 'Matière', style01)
        sheet.write(n, 2, 'Sous-Matières', style01)
        # sheet.write(n, 3, 'Gross Weight', style01)
        # sheet.write(n, 4, 'Tare Weight', style01)
        # sheet.write(n, 5, 'Extra Tare Weight', style01)
        sheet.write(n, 3, 'Poids Net', style01)
        sheet.write(n, 4, 'Coût de production', style01)

        n += 2

        for container in containers_obj:
            fraction_obj = self.env['project.fraction'].search([('source_container_id', '=', container.id)])
            container_production_cost = 0.0
            for fractions in fraction_obj:
                container_production_cost += fractions.production_cost
            sheet.write(n - 1, 0, container.name or '', style03)
            sheet.write(n - 1, 1, container.main_product_id.name or '', style03)

            if container.sub_product_id and container.sub_product_id.product_template_attribute_value_ids:
                sheet.write(n - 1, 2, container.sub_product_id.name+' ('+(container.sub_product_id.product_template_attribute_value_ids.name)+')', style03)
            elif container.sub_product_id:
                sheet.write(n - 1, 2, container.sub_product_id.name, style03)
            elif container.sub_product_id.product_template_attribute_value_ids:
                sheet.write(n - 1, 2, container.sub_product_id.product_template_attribute_value_ids.name, style03)
            else:
                sheet.write(n - 1, 2, '', style03)

            # sheet.write(n - 1, 2, container.sub_product_id.name+' ('+(container.sub_product_id.product_template_attribute_value_ids.name)+')', style03)

            # sheet.write(n - 1, 3, container.gross_weight or '', style02)
            # sheet.write(n - 1, 4, container.container_type_id.tare_weight or '', style02)
            # sheet.write(n - 1, 5, container.extra_tare or '', style02)
            sheet.write(n - 1, 3, container.net_gross_weight or '', style03)
            sheet.write(n - 1, 4, container.container_cost or '', style03)
            n += 1

            # fraction_obj = self.env['project.fraction'].search([('source_container_id' , '=' , container.id)])
            if fraction_obj:
                for fraction in fraction_obj:
                    sorted_qty += fraction.fraction_weight
                    sheet.write(n - 1, 0, fraction.name or '', style02)
                    sheet.write(n - 1, 1, fraction.main_product_id.name or '', style02)

                    if fraction.sub_product_id and fraction.sub_product_id.product_template_attribute_value_ids:
                        sheet.write(n - 1, 2, fraction.sub_product_id.name+' ('+(fraction.sub_product_id.product_template_attribute_value_ids.name)+')', style02)
                    elif fraction.sub_product_id:
                        sheet.write(n - 1, 2, fraction.sub_product_id.name, style02)
                    elif fraction.sub_product_id.product_template_attribute_value_ids:
                        sheet.write(n - 1, 2, fraction.sub_product_id.product_template_attribute_value_ids.name, style02)
                    else:
                        sheet.write(n - 1, 2, '', style02)

                    # sheet.write(n - 1, 2, fraction.sub_product_id.name+' ('+(fraction.sub_product_id.product_template_attribute_value_ids.name)+')' or '', style02)

                    # sheet.write(n - 1, 3, fraction.container_weight or '', style02)
                    # sheet.write(n - 1, 4, fraction.recipient_container_id.tare_weight or '', style02)
                    # sheet.write(n - 1, 5, fraction.source_container_id.extra_tare or '', style02)
                    sheet.write(n - 1, 3, fraction.fraction_weight or '', style02)
                    sheet.write(n - 1, 4, fraction.fraction_production_cost or '', style02)
                    n += 1
            else:
                sorted_qty += container.net_gross_weight

        stock_containers = self.env['stock.container'].search([('project_id', '=', self.id)])
        for st_container in stock_containers:
            sorted_qty += st_container.net_weight
            sheet.write(n - 1, 0, st_container.name or '', style04)
            sheet.write(n - 1, 1, st_container.content_type_id.name or '', style04)

            if st_container.content_type_id and st_container.content_type_id.product_template_attribute_value_ids:
                sheet.write(n - 1, 2, st_container.content_type_id.name+' ('+(st_container.content_type_id.product_template_attribute_value_ids.name)+')', style04)
            elif st_container.content_type_id:
                sheet.write(n - 1, 2, st_container.content_type_id.name, style04)
            elif st_container.content_type_id.product_template_attribute_value_ids:
                sheet.write(n - 1, 2, st_container.content_type_id.product_template_attribute_value_ids.name, style04)
            else:
                sheet.write(n - 1, 2, '', style02)

            # sheet.write(n - 1, 2, st_container.content_type_id.name+'('+st_container.content_type_id.product_template_attribute_value_ids.name+')' or '', style04)
            sheet.write(n - 1, 3, st_container.net_weight or '', style04)
            sheet.write(n - 1, 4, st_container.estimated_container_cost or '', style04)
            n += 1

        sheet.write(n, 2, 'Poids trié en totalee', style01)
        sheet.write(n, 3, sorted_qty, style01)

        filename = ('/tmp/Fraction Report.xls')
        # filename = os.path.join(ADDONS_PATH, 'Fraction Report.xls')

        workbook.save(filename)
        fraction_view = open(filename, 'rb')
        file_data = fraction_view.read()
        out = base64.encodestring(file_data)
        attach_value = {
            'fraction_char': 'Fraction Report.xls',
            'fraction_xml': out,
        }

        act_id = self.env['fraction.sort.report'].create(attach_value)
        fraction_view.close()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fraction.sort.report',
            'res_id': act_id.id,
            'target': 'new',
        }

    def fixed_purchase_report(self):
        list = []
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Fixed Purchase Report', cell_overwrite_ok=True)
        sheet.show_grid = False
        sheet.col(1).width = 256 * 25
        sheet.col(2).width = 256 * 25
        sheet.col(3).width = 256 * 25
        sheet.col(4).width = 256 * 25
        sheet.col(5).width = 256 * 25

        style01 = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color gray40,bottom_color gray40,right_color gray40,left_color gray40,left thin,right thin,top thin,bottom thin;')
        style02 = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color gray40,bottom_color gray40,right_color gray40,left_color gray40,left thin,right thin,top thin,bottom thin;')
        total_weight = 0.00
        weight_uom_id = ''
        for line in self.origin.order_line:
            if line.product_uom.name == 'Tonne':
                total_weight += (line.product_qty * 1000)
            else:
                total_weight += line.product_qty
            weight_uom_id = line.product_uom.name

        gross_weight = str(total_weight) + ' ' + str(weight_uom_id)

        sheet.write(0, 0, 'Référence', style01)
        sheet.write(0, 1, self.name, style01)
        sheet.write(1, 0, 'Client', style01)
        sheet.write(1, 1, self.partner_id.name, style01)
        sheet.write(2, 0, 'Poids Brut du Lot', style01)
        sheet.write(2, 1, gross_weight, style01)

        n = 4
        n += 0

        sheet.write(n, 0, 'Matière', style01)
        sheet.write(n, 1, 'Sous-Matière', style01)
        sheet.write(n, 2, 'Quantité', style01)
        sheet.write(n, 3, 'Unité de mesure', style01)
        sheet.write(n, 4, 'Prix offert Unitaire ', style01)
        sheet.write(n, 5, 'Prix Offert', style01)

        n += 2
        product_line_list = []
        for product_line in self.origin.order_line:
            sheet.write(n - 1, 0, product_line.product_id.name or '', style02)
            sheet.write(n - 1, 1, product_line.product_id.product_template_attribute_value_ids.name or '', style02)
            sheet.write(n - 1, 2, product_line.product_qty or '', style02)
            sheet.write(n - 1, 3, product_line.product_uom.name or '', style02)
            sheet.write(n - 1, 4, product_line.price_unit or '', style02)
            sheet.write(n - 1, 5, product_line.price_subtotal or '', style02)
            n += 1

        filename = ('/tmp/Fixed Purchase Report.xls')
        # filename = os.path.join(ADDONS_PATH, 'Fixed Purchase Report.xls')
        workbook.save(filename)
        fixed_purchase_report_view = open(filename, 'rb')
        file_data = fixed_purchase_report_view.read()
        out = base64.encodestring(file_data)
        attach_value = {'fixed_purchase_report_char': 'Fixed Purchase Report.xls', 'fixed_purchase_report_xml': out}

        act_id = self.env['fixed.purchase.report'].create(attach_value)
        fixed_purchase_report_view.close()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fixed.purchase.report',
            'res_id': act_id.id,
            'target': 'new',
        }

    def _get_share_url(self, redirect=False, signup_partner=False, pid=None):
        """
        Build the url of the record  that will be sent by mail and adds additional parameters such as
        access_token to bypass the recipient's rights,
        signup_partner to allows the user to create easily an account,
        hash token to allow the user to be authenticated in the chatter of the record portal view, if applicable
        :param redirect : Send the redirect url instead of the direct portal share url
        :param signup_partner: allows the user to create an account with pre-filled fields.
        :param pid: = partner_id - when given, a hash is generated to allow the user to be authenticated
            in the portal chatter, if any in the target page,
            if the user is redirected to the portal instead of the backend.
        :return: the url of the record with access parameters, if any.
        """
        self.ensure_one()
        params = {
            'model': self._name,
            'res_id': self.id,
        }
        if hasattr(self, 'access_token'):
            params['access_token'] = self._portal_ensure_token()
        if pid:
            params['pid'] = pid
            params['hash'] = self._sign_token(pid)
        if signup_partner and hasattr(self, 'partner_id') and self.partner_id:
            params.update(self.partner_id.signup_get_auth_param()[self.partner_id.id])

        return '%s?%s' % ('/mail/view' if redirect else self.access_url, url_encode(params))

        # @api.returns('mail.message', lambda value: value.id)

    # def message_post(self, **kwargs):
    #     if self.env.context.get('mark_allocate_logistics_as_sent'):
    #         if not kwargs['partner_ids']:
    #             raise UserError('Please add the recipients')
    #         else:
    #             if self.env.context.get('mark_allocate_logistics_as_sent'):
    #                 self.filtered(lambda o: o.status == 'quote').write({'is_demand_sent': True})
    #             return super(ProjectEntries, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    def send_notification(self):
        if self.is_registered_package:
            if not self.carton_ids:
                raise ValidationError('Enter Chronopost barcode')
            else:
                template_id = self.env.ref('ppts_project_entries.email_template_send_notification').id
                mail_template = self.env['mail.template'].browse(template_id)
        else:
            template_id = self.env.ref('ppts_project_entries.email_template_send_notification').id
            mail_template = self.env['mail.template'].browse(template_id)

        if mail_template:
            if self.is_registered_package:
                self.status = 'reception'
            else:
                self.status = 'in_transit'
                mail_template.send_mail(self.id, force_send=True)
            self.origin.button_confirm()

            # get stock

            stock_picking = self.env['stock.picking'].sudo().search([('origin','=',self.origin.name)])

            for picking in stock_picking:
                if not self.is_transport:
                    picking.logistics_updated = True

    def action_create_transport_request(self):
        ctx = dict()

        for rec in self:
            carton_line_list = [(0, 0, {
                'name': record.name,
                'cost': record.cost
            }) for record in rec.carton_ids]


        containers=[]
        transport_type = ''
        if self.send_containers:
            transport_type = 'drop_off'
            if self.project_container_ids:
                for ct in self.project_container_ids:
                    containers.append((0, 0, {
                        'product_id': ct.product_id.id,
                        'quantity': ct.quantity,
                    }))
            else:
                raise UserError(_('Please add some containers to send'))


        total_weight = 0.00
        weight_uom_id = 0
        for line in self.project_entry_ids:
            # if line.product_uom.name == 'Tonne':
            #     total_weight += (line.product_qty * 1000)
            # else:
            #     total_weight += line.product_qty
            
            if line.product_id.uom_id.uom_type == 'bigger':
                total_weight += line.product_qty * line.product_id.uom_id.factor_inv
            elif line.product_id.uom_id.uom_type == 'smaller':
                total_weight += line.product_qty / line.product_id.uom_id.factor
            else:
                total_weight += line.product_qty
                        
            weight_uom_id = line.product_uom.id

        ctx = ({
            'default_pickup_partner_id': self.partner_id.id,
            'default_delivery_partner_id': self.company_id.partner_id.id,
            'default_pickup_country_id': self.partner_id.state_id.id,
            'default_delivery_country_id': self.company_id.partner_id.state_id.id,
            'default_company_id': self.company_id.id,
            'default_origin': self.id,
            'default_no_of_container': round(self.no_of_container),
            'default_lorry_type': self.lorry_type,
            'default_is_tail_lift': self.is_tail_lift,
            'default_morning_opening_hours_start': self.morning_opening_hours_start,
            'default_morning_opening_hours_end': self.morning_opening_hours_end,
            'default_evening_opening_hours_start': self.evening_opening_hours_start,
            'default_evening_opening_hours_end': self.evening_opening_hours_end,
            'default_pickup_date_type': self.collection_date_type,
            'default_pickup_date': self.estimated_collection_date,
            'default_pickup_earliest_date': self.collection_date_from,
            'default_pickup_latest_date': self.collection_date_to,
            'default_is_full_load': self.is_full_load,
            'default_gross_weight': total_weight,
            'default_weight_uom_id': weight_uom_id,
            'default_carton_ids': carton_line_list,
            'default_pickup_street': self.street,
            'default_pickup_street2': self.street2,
            'default_pickup_zip': self.zip,
            'default_carton_pickup_city': self.city,
            'default_state_id': self.state_id,
            'default_pickup_countries_id': self.country_id,
            'default_logistics_for': 'purchase',
            'default_status': 'new',
            'default_send_containers': self.send_containers,
            'default_container_line_ids': containers,
            'default_transport_type': transport_type,
            'default_hayons': self.hayons,
            'default_grid_rotation': self.partner_id.grid_rotation,

        })

        form_id = self.env.ref('ppts_logistics.logistics_management_form_view').id

        return {
            'name': _('Transport Request'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'logistics.management',
            'views_id': False,
            'views': [(form_id or False, 'form')],
            'target': 'current',
            'context': ctx,
        }

    def action_view_transport_request(self):

        return {
            'name': _('Transport Request'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'logistics.management',
            'domain': [('origin', '=', self[0].id)],
            'views_id': False,
            'views': [(self.env.ref('ppts_logistics.logistics_management_tree_view').id or False, 'tree'),
                      (self.env.ref('ppts_logistics.logistics_management_form_view').id or False, 'form')],
        }

    def action_view_purchase_order(self):

        return {
            'name': _('Purchase Order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': self[0].origin.id,
            'views_id': False,
            'views': [(self.env.ref('purchase.purchase_order_form').id, 'form')],
        }

    def action_view_transport_po(self):

        transport_po_obj = self.env['purchase.order'].search([('origin', '=', self.origin.name)])

        return {
            'name': _('Purchase Order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': transport_po_obj.id,
            'views_id': False,
            'views': [(self.env.ref('purchase.purchase_order_form').id, 'form')],
        }

    @api.model
    def create(self, vals):
        if not vals.get('margin_class'):
            raise UserError(_('Please add margin class!'))
        if not vals.get('pickup_location_id'):
            raise UserError(_('Please add pickup point location!'))

        if vals.get('name', 'New') == 'New':
            if vals.get('project_type') == 'fixed_price':
                vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.pf') or '/'
            elif vals.get('project_type') == 'variable_price':
                vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.pv') or '/'
            elif vals.get('project_type') == 'reuse':
                vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.pr') or '/'
            elif vals.get('project_type') == 'refine':
                vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.pa') or '/'
            # if vals.get('project_type') == 'sorting':
            #     vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.pe') or '/'
            # elif vals.get('project_type') == 'reuse':
            #     vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.pr') or '/'
            # elif vals.get('project_type') == 'transfer':
            #     vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.cd') or '/'
            # elif vals.get('project_type') == 'refine':
            #     vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.pa') or '/'
            # elif vals.get('project_type') == 'cross_dock':
            #     vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.cd') or '/'
            # elif vals.get('project_type') == 'dismantle_sort':
            #     vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.ds') or '/'

        if vals.get('origin'):
            project_obj = self.env['project.entries'].search([('origin', '=', int(vals.get('origin')))])
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('project.entries.pe') or '/'

        if project_obj:
            raise UserError(_('Project entry is already created for the same purchase request'))
        else:
            res = super(ProjectEntries, self).create(vals)

            # if res.partner_id.short_code:
            #     res.partner_ref = str(res.partner_id.short_code)+'/0'+str(res.partner_id.lot_sequence_number)
            # else:
            #     res.partner_ref = 'Lot/0'+str(res.partner_id.lot_sequence_number)

            # res.partner_id.lot_sequence_number += 1

            # for line in res.project_entry_ids:
            #     if not line.account_analytic_id:
            #         raise Warning("Analytic account not selected in lines.")

            res.origin.is_project = True

            return res

    # def write(self, vals):
    #     res = super(ProjectEntries, self).write(vals)
    #     if self.project_entry_ids:
    #         po_product_line_list = []
    #         crm_product_line_list = []
    #         for record in self.project_entry_ids:
    #             po_product_line_list.append((0, 0, {
    #                 'product_id': record.product_id.id,
    #                 'name': record.name or '',
    #                 'product_qty': record.product_qty,
    #                 'product_uom': record.product_uom.id,
    #                 'price_unit': record.offer_price if not record.is_malus else record.malus_demand,
    #                 'date_planned': datetime.now()
    #             }))
    #             crm_product_line_list.append((0, 0, {
    #                 'product_id': record.product_id.id,
    #                 'description': record.name or '',
    #                 'quantity': record.product_qty,
    #                 'uom_id': record.product_uom.id,
    #                 'price_per_ton': record.price_unit,
    #                 'is_malus': record.is_malus,
    #                 'price': record.price,
    #                 'offer_price': record.offer_price,
    #                 'return_price': record.malus,
    #                 'charge_malus': record.charge_malus,
    #                 'malus_demand': record.malus_demand,
    #                 'expexted_margin_percentage': record.expexted_margin_percentage,
    #                 'computed_margin_percentage': record.computed_margin_percentage
    #             }))
    #         if self.origin:
    #             self.origin.order_line = po_product_line_list
    #         if self.origin.opportunity_id:
    #             self.origin.opportunity_id.product_lines = crm_product_line_list
    #             self.origin.opportunity_id.margin_class = self.margin_class
    #             self.origin.opportunity_id.estimated_transport_cost = self.forcased_transport_cost

    #     return res

    def unlink(self):

        self.origin.is_project = False

        return super(ProjectEntries, self).unlink()

    def plan_third_party_arrival(self):
        transports = self.env["logistics.management"].search([('origin', '=', self.id)], limit=1)
        if transports:
            vals = ({'default_project_id': self.id,
                     'default_note': 'Transport request is already created for this project! You can delete the existing request or you can update the date of the existing request.',
                     'default_exist': True, 'default_transport_id': transports.name, 'default_planned_date': transports.expected_delivery})
        else:
            vals = ({'default_project_id': self.id})

        return {
            'name': "Third Party Arrival Plan",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'third.party.arrival',
            'target': 'new',
            'context': vals,
        }

    def update_actual_sales_cost_cron(self):
        shipment_obj = self.env['stock.picking'].search([('picking_type_code', '=', 'outgoing'),('state', '=', 'done')])
        
        for rec in shipment_obj:
            sale_obj = self.env['sale.order'].search([('name', '=', rec.origin)])
            if sale_obj:
                for so_line in sale_obj.order_line:
                    if so_line.container_id:
                        container_cost = so_line.price_subtotal/int(len(so_line.container_id))
                        for container in so_line.container_id:
                            if not container.is_sales_cost_updated == True:
                                if container.cross_dock != True:
                                    if container.fraction_line_ids:
                                        fraction_cost = container_cost / len(container.fraction_line_ids)
                                        for fraction_line in container.fraction_line_ids:
                                            fraction_line.fraction_id.project_id.actual_sale_cost += fraction_cost
                                else:
                                    container.project_id.actual_sale_cost += container_cost
                                container.is_sales_cost_updated = True

    
    @api.onchange('carton_ids')
    def update_transport_cost(self):
        transport_cost = 0.0
        for line in self.carton_ids:
            if line.sur_charges:
                transport_cost += line.cost + (line.cost * (line.sur_charges/100))
            else:
                transport_cost += line.cost
        if self.is_registered_package:
            if transport_cost != 0.0:
                self.confirmed_transport_cost = transport_cost




class ProjectEntriesLine(models.Model):
    _name = 'project.entries.line'
    _description = 'Product'

    @api.model
    def default_get(self, fields_name):
        res = super(ProjectEntriesLine, self).default_get(fields_name)
        if self._context.get('margin_class'):
            res.update({'margin_class': self._context.get('margin_class')})

        return res

    product_id = fields.Many2one('product.product', 'Product')
    name = fields.Char('Description')
    product_qty = fields.Float('Quantity')
    product_uom = fields.Many2one('uom.uom', 'UoM')
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    price_subtotal = fields.Float(string='Subtotal')
    price_total = fields.Float(string='Total')
    project_entry_id = fields.Many2one('project.entries', string='Project entries Reference')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    margin_class = fields.Selection([
        ('class_a', 'Class A'),
        ('class_b', 'Class B'),
        ('class_c', 'Class C')
    ], string="Margin Class")
    price = fields.Monetary(string='Target Sale/Purchase Price', currency_field='currency_id', compute='_compute_target_price')
    offer_price = fields.Monetary(string='Offer Price', currency_field='currency_id')
    price_unit = fields.Monetary(string='Price per UdM', currency_field='currency_id')
    expexted_margin_percentage = fields.Integer('Company Margin(%)', compute='_compute_estimated_margin', store=True)
    computed_margin_percentage = fields.Integer('Offer Margin(%)')
    malus = fields.Monetary('Malus', currency_field='currency_id')
    charge_malus = fields.Monetary('Charge Malus', currency_field='currency_id')
    malus_demand = fields.Monetary('Malus Demandé', currency_field='currency_id')
    is_malus = fields.Boolean('Is Malus')
    is_service = fields.Boolean("Is Service")
    estimated_service_cost = fields.Float("Estimated Service Cost")

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.onchange('product_id')
    def onchange_product(self):
        self.name = self.product_id.name
        self.price_unit = self.product_id.ecologic_price if self.project_entry_id.is_ecologic else self.product_id.lst_price
        self.product_uom = self.product_id.uom_id.id
        self.malus = self.product_id.malus
        self.charge_malus = self.product_id.charge_malus
        # if self.product_qty != 0:
        #     if self.product_id.lst_price != 0:
        #         if not self.is_malus:
        #             if self.margin_class == 'class_a':
        #                 self.price = ((self.product_id.lst_price) * (1 - (self.project_entry_id.company_id.sale_margin_a / 100)))
        #             if self.margin_class == 'class_b':
        #                 self.price = ((self.product_id.lst_price) * (1 - (self.project_entry_id.company_id.sale_margin_b / 100)))
        #             if self.margin_class == 'class_c':
        #                 self.price = ((self.product_id.lst_price) * (1 - (self.project_entry_id.company_id.sale_margin_c / 100)))
        #     else:
        #         raise UserError('Please update the public price of the product')
        # else:
        #     self.price = 0.0

    @api.depends('product_qty', 'product_id')
    def _compute_target_price(self):
        for rec in self:

            product_price = rec.product_id.ecologic_price if rec.project_entry_id.is_ecologic else rec.product_id.lst_price

            if rec.product_qty != 0:
                if math.ceil(product_price) != 0:
                    if not rec.is_malus:
                        if rec.project_entry_id.is_ecologic:
                            rec.price = product_price
                        else:
                            if rec.margin_class == 'class_a':
                                rec.price = ((product_price) * (1 - (rec.project_entry_id.company_id.sale_margin_a / 100)))
                            elif rec.margin_class == 'class_b':
                                rec.price = ((product_price) * (1 - (rec.project_entry_id.company_id.sale_margin_b / 100)))
                            else:
                                rec.price = ((product_price) * (1 - (rec.project_entry_id.company_id.sale_margin_c / 100)))
                    else:
                        rec.price = 0.0
                else:
                    raise UserError('Please update the public price of the product')
            else:
                rec.price = 0.0

    @api.onchange('offer_price', 'price')
    def onchange_offer_margin(self):
        if not self.is_malus:

            product_price = self.product_id.ecologic_price if self.project_entry_id.is_ecologic else self.product_id.lst_price

            if self.offer_price != 0 and self.product_qty:
                if math.ceil(product_price) != 0:
                    if self.project_entry_id.is_ecologic:
                        self.computed_margin_percentage = ((self.product_id.lst_price - self.offer_price)/self.product_id.ecologic_price) * 100
                    else:
                        self.computed_margin_percentage = ((((product_price - self.offer_price)) / product_price) * 100)
                else:
                    raise UserError('Please update the public/ecologic price of the product')

    @api.depends('margin_class')
    def _compute_estimated_margin(self):
        expexted_margin_percentage = 0
        for rec in self:
            if rec.margin_class == 'class_a':
                rec.expexted_margin_percentage = rec.project_entry_id.company_id.sale_margin_a
            elif rec.margin_class == 'class_b':
                rec.expexted_margin_percentage = rec.project_entry_id.company_id.sale_margin_b
            else:
                rec.expexted_margin_percentage = rec.project_entry_id.company_id.sale_margin_c

    # @api.onchange('price_unit','product_qty')
    # def onchange_price_subtotal(self):
    #     self.price_subtotal = self.product_qty * self.price_unit


class CartonLine(models.Model):
    _name = "carton.line"

    name = fields.Char("Carton Number")
    cost = fields.Float("Cost")
    sur_charges = fields.Float("Sur Charges(%)")
    carton_id = fields.Many2one('project.entries', string='Project entries Reference')


class SilverRefiningCost(models.Model):
    _name = "silver.refining.cost"

    silver_cost_id = fields.Many2one('project.entries', string="Silver Refining cost line Ref")
    analysis_for_certification = fields.Float('Analyse CAP (g) pas obligatoire',digits=(16, 3))
    reference_sample_analysis = fields.Float('Analyse Echantillon de Référence (g)',digits=(16, 3))
    actual_result = fields.Float('Résultats après traitement (g)',digits=(16, 3))
    dedection_percentage = fields.Float('Pourcentage restitution', compute='_commission_percentage')
    buy_price_discount = fields.Float('Pourcentage remise contre prix LME', compute='_lme_percentage')
    remaining_metal = fields.Float('Solde en compte client', compute="_compute_remaining_metal",digits=(16, 3))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    lbma_price = fields.Monetary('Prix LBMA/LME par kg', currency_field='currency_id')
    offer_buying_price = fields.Monetary('Offre de Rachat', currency_field='currency_id', compute="_compute_buying_price")
    treatment_cost = fields.Monetary('Frais de préstation', currency_field='currency_id')
    final_purchase_price = fields.Monetary('Offre actuelle', currency_field='currency_id', compute="_compute_final_purchase_price")
    price_per_gram = fields.Float("rix LBMA/LME par g", compute='_compute_gram_price')
    waste_nature = fields.Char("Nature du déchet")
    project_id = fields.Many2one("project.entries", string="Project ID")
    minimum_levy = fields.Float("Minimum Levy(g)")
    return_percentage = fields.Float('Pourcentage restitution')
    lme_price_discount = fields.Float('Pourcentage remise contre prix LME')
    price_date = fields.Date("Date of Price")
    price_source = fields.Selection([('lme_morning','LME Morning'),('lme_evening','LME Evening'),('spot','Spot'),('lmba_morning','LBMA Morning'),('lbma_Evening','LBMA Evening')]
                                    ,string="Source of Price")
    sample_ct_id = fields.Many2one("project.container", string="Sample CT")
    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_2 = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_3 = fields.Many2one('project.refining.sample', string='Refining Sample')

    is_analysis_for_certification = fields.Boolean()
    is_reference_sample_analysis = fields.Boolean()
    is_actual_result = fields.Boolean()

    @api.onchange('analysis_for_certification')
    def onchange_analysis_for_certification(self):
        if self.analysis_for_certification:
            self.is_analysis_for_certification = True

    @api.onchange('reference_sample_analysis')
    def onchange_reference_sample_analysis(self):
        if self.reference_sample_analysis:
            self.is_reference_sample_analysis = True

    @api.onchange('actual_result')
    def onchange_actual_result(self):
        if self.actual_result:
            self.is_actual_result = True

    @api.depends('lme_price_discount')
    def _lme_percentage(self):
        for rec in self:
            buy_price_discount = 0.0
            if rec.lme_price_discount:
                buy_price_discount = 100 - rec.lme_price_discount
            rec.update({
                'buy_price_discount': buy_price_discount
            })

    @api.depends('return_percentage')
    def _commission_percentage(self):
        for rec in self:
            deduction_percentage = 0.0
            if rec.return_percentage:
                deduction_percentage =  100 - rec.return_percentage
            rec.update({
                'dedection_percentage': deduction_percentage
            })


    @api.depends('lbma_price')
    def _compute_gram_price(self):
        for rec in self:
            gram_price = rec.lbma_price / 1000
            rec.update({
                'price_per_gram': gram_price
            })

    @api.depends('actual_result', 'dedection_percentage','minimum_levy')
    def _compute_remaining_metal(self):
        for rec in self:
            remaining_metal = 0.00
            if rec.minimum_levy and  rec.minimum_levy > (rec.actual_result * (rec.dedection_percentage/100)):
                deduction = rec.minimum_levy
            else:
                deduction = rec.actual_result * (rec.dedection_percentage/100)
            if rec.actual_result:
                remaining_metal = rec.actual_result - deduction
            rec.update({
                'remaining_metal': remaining_metal
            })

    @api.depends('price_per_gram', 'remaining_metal', 'buy_price_discount')
    def _compute_buying_price(self):
        for rec in self:
            offer_buying_price = 0.00
            offer_buying_price = rec.price_per_gram * rec.remaining_metal * (1 - (rec.buy_price_discount / 100))
            rec.update({
                'offer_buying_price': offer_buying_price
            })

    @api.depends('offer_buying_price', 'treatment_cost')
    def _compute_final_purchase_price(self):
        for rec in self:
            final_purchase_price = 0.00
            final_purchase_price = rec.offer_buying_price - rec.treatment_cost
            rec.update({
                'final_purchase_price': final_purchase_price
            })


class GoldRefiningCost(models.Model):
    _name = "gold.refining.cost"

    gold_cost_id = fields.Many2one('project.entries', string="Gold Refining cost line Ref")
    analysis_for_certification = fields.Float('Analyse CAP (g) pas obligatoire', digits=(16, 3))
    reference_sample_analysis = fields.Float('Analyse Echantillon de Référence (g)', digits=(16, 3))
    actual_result = fields.Float('Résultats après traitement (g)', digits=(16, 3))
    dedection_percentage = fields.Float('Pourcentage restitution', compute='_commission_percentage')
    buy_price_discount = fields.Float('Pourcentage remise contre prix LME',compute='_lme_percentage')
    remaining_metal = fields.Float('Solde en compte client', compute="_compute_remaining_metal", digits=(16, 3))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    lbma_price = fields.Monetary('Prix LBMA/LME par kg', currency_field='currency_id')
    offer_buying_price = fields.Monetary('Offre de Rachat', currency_field='currency_id', compute="_compute_buying_price")
    treatment_cost = fields.Monetary('Frais de préstation', currency_field='currency_id')
    final_purchase_price = fields.Monetary('Offre actuelle', currency_field='currency_id', compute="_compute_final_purchase_price")
    price_per_gram = fields.Float("rix LBMA/LME par g", compute='_compute_gram_price')
    waste_nature = fields.Char("Nature du déchet")
    project_id = fields.Many2one("project.entries", string="Project ID")
    minimum_levy = fields.Float("Minimum Levy(g)")
    return_percentage = fields.Float('Pourcentage restitution')
    lme_price_discount = fields.Float('Pourcentage remise contre prix LME')
    price_date = fields.Date("Date of Price")
    price_source = fields.Selection([('lme_morning', 'LME Morning'), ('lme_evening', 'LME Evening'), ('spot', 'Spot'), ('lmba_morning', 'LBMA Morning'), ('lbma_evening', 'LBMA Evening')]
                                    , string="Source of Price")
    sample_ct_id = fields.Many2one("project.container", string="Sample CT", domain="[('state','in',('new','confirmed','inprogress','planned'))]" )
    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_2 = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_3 = fields.Many2one('project.refining.sample', string='Refining Sample')

    is_analysis_for_certification = fields.Boolean()
    is_reference_sample_analysis = fields.Boolean()
    is_actual_result = fields.Boolean()

    @api.onchange('analysis_for_certification')
    def onchange_analysis_for_certification(self):
        if self.analysis_for_certification:
            self.is_analysis_for_certification = True

    @api.onchange('reference_sample_analysis')
    def onchange_reference_sample_analysis(self):
        if self.reference_sample_analysis:
            self.is_reference_sample_analysis = True

    @api.onchange('actual_result')
    def onchange_actual_result(self):
        if self.actual_result:
            self.is_actual_result = True

    @api.depends('lme_price_discount')
    def _lme_percentage(self):
        for rec in self:
            buy_price_discount = 0.0
            if rec.lme_price_discount:
                buy_price_discount = 100 - rec.lme_price_discount
            rec.update({
                'buy_price_discount': buy_price_discount
            })
    @api.depends('return_percentage')
    def _commission_percentage(self):
        for rec in self:
            deduction_percentage = 0.0
            if rec.return_percentage:
                deduction_percentage = 100 - rec.return_percentage
            rec.update({
                'dedection_percentage': deduction_percentage
            })

    @api.depends('lbma_price')
    def _compute_gram_price(self):
        for rec in self:
            gram_price = rec.lbma_price / 1000
            rec.update({
                'price_per_gram': gram_price
            })

    @api.depends('actual_result', 'dedection_percentage', 'minimum_levy')
    def _compute_remaining_metal(self):
        for rec in self:
            remaining_metal = 0.00
            print(rec.actual_result * (rec.dedection_percentage / 100), "+++++++++++++++++++++++")
            if rec.minimum_levy and rec.minimum_levy > (rec.actual_result * (rec.dedection_percentage / 100)):
                deduction = rec.minimum_levy
            else:
                deduction = rec.actual_result * (rec.dedection_percentage / 100)
            if rec.actual_result:
                remaining_metal = rec.actual_result - deduction
            rec.update({
                'remaining_metal': remaining_metal
            })

    @api.depends('price_per_gram', 'remaining_metal', 'buy_price_discount')
    def _compute_buying_price(self):
        for rec in self:
            offer_buying_price = 0.00
            offer_buying_price = rec.price_per_gram * rec.remaining_metal * (1 - (rec.buy_price_discount / 100))
            rec.update({
                'offer_buying_price': offer_buying_price
            })

    @api.depends('offer_buying_price', 'treatment_cost')
    def _compute_final_purchase_price(self):
        for rec in self:
            final_purchase_price = 0.00
            final_purchase_price = rec.offer_buying_price - rec.treatment_cost
            rec.update({
                'final_purchase_price': final_purchase_price
            })


class PalladiumRefiningCost(models.Model):
    _name = "palladium.refining.cost"

    palladium_cost_id = fields.Many2one('project.entries', string="Palladium Refining cost line Ref")
    analysis_for_certification = fields.Float('Analyse CAP (g) pas obligatoire', digits=(16, 3))
    reference_sample_analysis = fields.Float('Analyse Echantillon de Référence (g)', digits=(16, 3))
    actual_result = fields.Float('Résultats après traitement (g)', digits=(16, 3))
    dedection_percentage = fields.Float('Pourcentage restitution', compute='_commission_percentage')
    buy_price_discount = fields.Float('Pourcentage remise contre prix LME',compute='_lme_percentage')
    remaining_metal = fields.Float('Solde en compte client', compute="_compute_remaining_metal", digits=(16, 3))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    lbma_price = fields.Monetary('Prix LBMA/LME par kg', currency_field='currency_id')
    offer_buying_price = fields.Monetary('Offre de Rachat', currency_field='currency_id', compute="_compute_buying_price")
    treatment_cost = fields.Monetary('Frais de préstation', currency_field='currency_id')
    final_purchase_price = fields.Monetary('Offre actuelle', currency_field='currency_id', compute="_compute_final_purchase_price")
    price_per_gram = fields.Float("rix LBMA/LME par g", compute='_compute_gram_price')
    waste_nature = fields.Char("Nature du déchet")
    project_id = fields.Many2one("project.entries", string="Project ID")
    minimum_levy = fields.Float("Minimum Levy(g)")
    return_percentage = fields.Float('Pourcentage restitution')
    lme_price_discount = fields.Float('Pourcentage remise contre prix LME')
    price_date = fields.Date("Date of Price")
    price_source = fields.Selection([('lme_morning', 'LME Morning'), ('lme_evening', 'LME Evening'), ('spot', 'Spot'), ('lmba_morning', 'LBMA Morning'), ('lbma_evening', 'LBMA Evening')]
                                    , string="Source of Price")
    sample_ct_id = fields.Many2one("project.container", string="Sample CT", domain="[('state','in',('new','confirmed','inprogress','planned'))]" )
    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_2 = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_3 = fields.Many2one('project.refining.sample', string='Refining Sample')

    is_analysis_for_certification = fields.Boolean()
    is_reference_sample_analysis = fields.Boolean()
    is_actual_result = fields.Boolean()

    @api.onchange('analysis_for_certification')
    def onchange_analysis_for_certification(self):
        if self.analysis_for_certification:
            self.is_analysis_for_certification = True

    @api.onchange('reference_sample_analysis')
    def onchange_reference_sample_analysis(self):
        if self.reference_sample_analysis:
            self.is_reference_sample_analysis = True

    @api.onchange('actual_result')
    def onchange_actual_result(self):
        if self.actual_result:
            self.is_actual_result = True

    @api.depends('lme_price_discount')
    def _lme_percentage(self):
        for rec in self:
            buy_price_discount = 0.0
            if rec.lme_price_discount:
                buy_price_discount = 100 - rec.lme_price_discount
            rec.update({
                'buy_price_discount': buy_price_discount
            })
    @api.depends('return_percentage')
    def _commission_percentage(self):
        for rec in self:
            deduction_percentage = 0.0
            if rec.return_percentage:
                deduction_percentage = 100 - rec.return_percentage
            rec.update({
                'dedection_percentage': deduction_percentage
            })

    @api.depends('lbma_price')
    def _compute_gram_price(self):
        for rec in self:
            gram_price = rec.lbma_price / 1000
            rec.update({
                'price_per_gram': gram_price
            })

    @api.depends('actual_result', 'dedection_percentage', 'minimum_levy')
    def _compute_remaining_metal(self):
        for rec in self:
            remaining_metal = 0.00
            print(rec.actual_result * (rec.dedection_percentage / 100), "+++++++++++++++++++++++")
            if rec.minimum_levy and rec.minimum_levy > (rec.actual_result * (rec.dedection_percentage / 100)):
                deduction = rec.minimum_levy
            else:
                deduction = rec.actual_result * (rec.dedection_percentage / 100)
            if rec.actual_result:
                remaining_metal = rec.actual_result - deduction
            rec.update({
                'remaining_metal': remaining_metal
            })

    @api.depends('price_per_gram', 'remaining_metal', 'buy_price_discount')
    def _compute_buying_price(self):
        for rec in self:
            offer_buying_price = 0.00
            offer_buying_price = rec.price_per_gram * rec.remaining_metal * (1 - (rec.buy_price_discount / 100))
            rec.update({
                'offer_buying_price': offer_buying_price
            })

    @api.depends('offer_buying_price', 'treatment_cost')
    def _compute_final_purchase_price(self):
        for rec in self:
            final_purchase_price = 0.00
            final_purchase_price = rec.offer_buying_price - rec.treatment_cost
            rec.update({
                'final_purchase_price': final_purchase_price
            })


class PlatinumRefiningCost(models.Model):
    _name = "platinum.refining.cost"

    platinum_cost_id = fields.Many2one('project.entries', string="Platinum Refining cost line Ref")
    analysis_for_certification = fields.Float('Analyse CAP (g) pas obligatoire', digits=(16, 3))
    reference_sample_analysis = fields.Float('Analyse Echantillon de Référence (g)', digits=(16, 3))
    actual_result = fields.Float('Résultats après traitement (g)', digits=(16, 3))
    dedection_percentage = fields.Float('Pourcentage restitution', compute='_commission_percentage')
    buy_price_discount = fields.Float('Pourcentage remise contre prix LME',compute='_lme_percentage')
    remaining_metal = fields.Float('Solde en compte client', compute="_compute_remaining_metal", digits=(16, 3))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    lbma_price = fields.Monetary('Prix LBMA/LME par kg', currency_field='currency_id')
    offer_buying_price = fields.Monetary('Offre de Rachat', currency_field='currency_id', compute="_compute_buying_price")
    treatment_cost = fields.Monetary('Frais de préstation', currency_field='currency_id')
    final_purchase_price = fields.Monetary('Offre actuelle', currency_field='currency_id', compute="_compute_final_purchase_price")
    price_per_gram = fields.Float("rix LBMA/LME par g", compute='_compute_gram_price')
    waste_nature = fields.Char("Nature du déchet")
    project_id = fields.Many2one("project.entries", string="Project ID")
    minimum_levy = fields.Float("Minimum Levy(g)")
    return_percentage = fields.Float('Pourcentage restitution')
    lme_price_discount = fields.Float('Pourcentage remise contre prix LME')
    price_date = fields.Date("Date of Price")
    price_source = fields.Selection([('lme_morning', 'LME Morning'), ('lme_evening', 'LME Evening'), ('spot', 'Spot'), ('lmba_morning', 'LBMA Morning'), ('lbma_evening', 'LBMA Evening')]
                                    , string="Source of Price")
    sample_ct_id = fields.Many2one("project.container", string="Sample CT", domain="[('state','in',('new','confirmed','inprogress','planned'))]" )
    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_2 = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_3 = fields.Many2one('project.refining.sample', string='Refining Sample')

    is_analysis_for_certification = fields.Boolean()
    is_reference_sample_analysis = fields.Boolean()
    is_actual_result = fields.Boolean()

    @api.onchange('analysis_for_certification')
    def onchange_analysis_for_certification(self):
        if self.analysis_for_certification:
            self.is_analysis_for_certification = True

    @api.onchange('reference_sample_analysis')
    def onchange_reference_sample_analysis(self):
        if self.reference_sample_analysis:
            self.is_reference_sample_analysis = True

    @api.onchange('actual_result')
    def onchange_actual_result(self):
        if self.actual_result:
            self.is_actual_result = True

    @api.depends('lme_price_discount')
    def _lme_percentage(self):
        for rec in self:
            buy_price_discount = 0.0
            if rec.lme_price_discount:
                buy_price_discount = 100 - rec.lme_price_discount
            rec.update({
                'buy_price_discount': buy_price_discount
            })
    @api.depends('return_percentage')
    def _commission_percentage(self):
        for rec in self:
            deduction_percentage = 0.0
            if rec.return_percentage:
                deduction_percentage = 100 - rec.return_percentage
            rec.update({
                'dedection_percentage': deduction_percentage
            })

    @api.depends('lbma_price')
    def _compute_gram_price(self):
        for rec in self:
            gram_price = rec.lbma_price / 1000
            rec.update({
                'price_per_gram': gram_price
            })

    @api.depends('actual_result', 'dedection_percentage', 'minimum_levy')
    def _compute_remaining_metal(self):
        for rec in self:
            remaining_metal = 0.00
            print(rec.actual_result * (rec.dedection_percentage / 100), "+++++++++++++++++++++++")
            if rec.minimum_levy and rec.minimum_levy > (rec.actual_result * (rec.dedection_percentage / 100)):
                deduction = rec.minimum_levy
            else:
                deduction = rec.actual_result * (rec.dedection_percentage / 100)
            if rec.actual_result:
                remaining_metal = rec.actual_result - deduction
            rec.update({
                'remaining_metal': remaining_metal
            })

    @api.depends('price_per_gram', 'remaining_metal', 'buy_price_discount')
    def _compute_buying_price(self):
        for rec in self:
            offer_buying_price = 0.00
            offer_buying_price = rec.price_per_gram * rec.remaining_metal * (1 - (rec.buy_price_discount / 100))
            rec.update({
                'offer_buying_price': offer_buying_price
            })

    @api.depends('offer_buying_price', 'treatment_cost')
    def _compute_final_purchase_price(self):
        for rec in self:
            final_purchase_price = 0.00
            final_purchase_price = rec.offer_buying_price - rec.treatment_cost
            rec.update({
                'final_purchase_price': final_purchase_price
            })


class CopperRefiningCost(models.Model):
    _name = "copper.refining.cost"

    copper_cost_id = fields.Many2one('project.entries', string="Copper Refining cost line Ref")
    analysis_for_certification = fields.Float('Analyse CAP (g) pas obligatoire', digits=(16, 3))
    reference_sample_analysis = fields.Float('Analyse Echantillon de Référence (g)', digits=(16, 3))
    actual_result = fields.Float('Résultats après traitement (g)', digits=(16, 3))
    dedection_percentage = fields.Float('Pourcentage restitution', compute='_commission_percentage')
    buy_price_discount = fields.Float('Pourcentage remise contre prix LME',compute='_lme_percentage')
    remaining_metal = fields.Float('Solde en compte client', compute="_compute_remaining_metal", digits=(16, 3))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    lbma_price = fields.Monetary('Prix LBMA/LME par kg', currency_field='currency_id')
    offer_buying_price = fields.Monetary('Offre de Rachat', currency_field='currency_id', compute="_compute_buying_price")
    treatment_cost = fields.Monetary('Frais de préstation', currency_field='currency_id')
    final_purchase_price = fields.Monetary('Offre actuelle', currency_field='currency_id', compute="_compute_final_purchase_price")
    price_per_gram = fields.Float("rix LBMA/LME par g", compute='_compute_gram_price')
    waste_nature = fields.Char("Nature du déchet")
    project_id = fields.Many2one("project.entries", string="Project ID")
    minimum_levy = fields.Float("Minimum Levy(g)")
    return_percentage = fields.Float('Pourcentage restitution')
    lme_price_discount = fields.Float('Pourcentage remise contre prix LME')
    price_date = fields.Date("Date of Price")
    price_source = fields.Selection([('lme_morning', 'LME Morning'), ('lme_evening', 'LME Evening'), ('spot', 'Spot'), ('lmba_morning', 'LBMA Morning'), ('lbma_evening', 'LBMA Evening')]
                                    , string="Source of Price")
    sample_ct_id = fields.Many2one("project.container", string="Sample CT", domain="[('state','in',('new','confirmed','inprogress','planned'))]" )
    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_2 = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_3 = fields.Many2one('project.refining.sample', string='Refining Sample')

    is_analysis_for_certification = fields.Boolean()
    is_reference_sample_analysis = fields.Boolean()
    is_actual_result = fields.Boolean()

    @api.onchange('analysis_for_certification')
    def onchange_analysis_for_certification(self):
        if self.analysis_for_certification:
            self.is_analysis_for_certification = True

    @api.onchange('reference_sample_analysis')
    def onchange_reference_sample_analysis(self):
        if self.reference_sample_analysis:
            self.is_reference_sample_analysis = True

    @api.onchange('actual_result')
    def onchange_actual_result(self):
        if self.actual_result:
            self.is_actual_result = True

    @api.depends('lme_price_discount')
    def _lme_percentage(self):
        for rec in self:
            buy_price_discount = 0.0
            if rec.lme_price_discount:
                buy_price_discount = 100 - rec.lme_price_discount
            rec.update({
                'buy_price_discount': buy_price_discount
            })
    @api.depends('return_percentage')
    def _commission_percentage(self):
        for rec in self:
            deduction_percentage = 0.0
            if rec.return_percentage:
                deduction_percentage = 100 - rec.return_percentage
            rec.update({
                'dedection_percentage': deduction_percentage
            })

    @api.depends('lbma_price')
    def _compute_gram_price(self):
        for rec in self:
            gram_price = rec.lbma_price / 1000
            rec.update({
                'price_per_gram': gram_price
            })

    @api.depends('actual_result', 'dedection_percentage', 'minimum_levy')
    def _compute_remaining_metal(self):
        for rec in self:
            remaining_metal = 0.00
            print(rec.actual_result * (rec.dedection_percentage / 100), "+++++++++++++++++++++++")
            if rec.minimum_levy and rec.minimum_levy > (rec.actual_result * (rec.dedection_percentage / 100)):
                deduction = rec.minimum_levy
            else:
                deduction = rec.actual_result * (rec.dedection_percentage / 100)
            if rec.actual_result:
                remaining_metal = rec.actual_result - deduction
            rec.update({
                'remaining_metal': remaining_metal
            })

    @api.depends('price_per_gram', 'remaining_metal', 'buy_price_discount')
    def _compute_buying_price(self):
        for rec in self:
            offer_buying_price = 0.00
            offer_buying_price = rec.price_per_gram * rec.remaining_metal * (1 - (rec.buy_price_discount / 100))
            rec.update({
                'offer_buying_price': offer_buying_price
            })

    @api.depends('offer_buying_price', 'treatment_cost')
    def _compute_final_purchase_price(self):
        for rec in self:
            final_purchase_price = 0.00
            final_purchase_price = rec.offer_buying_price - rec.treatment_cost
            rec.update({
                'final_purchase_price': final_purchase_price
            })


class RhodiumRefiningCost(models.Model):
    _name = "rhodium.refining.cost"

    rhodium_cost_id = fields.Many2one('project.entries', string="Rhodium Refining cost line Ref")
    analysis_for_certification = fields.Float('Analyse CAP (g) pas obligatoire', digits=(16, 3))
    reference_sample_analysis = fields.Float('Analyse Echantillon de Référence (g)', digits=(16, 3))
    actual_result = fields.Float('Résultats après traitement (g)', digits=(16, 3))
    dedection_percentage = fields.Float('Pourcentage restitution', compute='_commission_percentage')
    buy_price_discount = fields.Float('Pourcentage remise contre prix LME',compute='_lme_percentage')
    remaining_metal = fields.Float('Solde en compte client', compute="_compute_remaining_metal", digits=(16, 3))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    lbma_price = fields.Monetary('Prix LBMA/LME par kg', currency_field='currency_id')
    offer_buying_price = fields.Monetary('Offre de Rachat', currency_field='currency_id', compute="_compute_buying_price")
    treatment_cost = fields.Monetary('Frais de préstation', currency_field='currency_id')
    final_purchase_price = fields.Monetary('Offre actuelle', currency_field='currency_id', compute="_compute_final_purchase_price")
    price_per_gram = fields.Float("rix LBMA/LME par g", compute='_compute_gram_price')
    waste_nature = fields.Char("Nature du déchet")
    project_id = fields.Many2one("project.entries", string="Project ID")
    minimum_levy = fields.Float("Minimum Levy(g)")
    return_percentage = fields.Float('Pourcentage restitution')
    lme_price_discount = fields.Float('Pourcentage remise contre prix LME')
    price_date = fields.Date("Date of Price")
    price_source = fields.Selection([('lme_morning', 'LME Morning'), ('lme_evening', 'LME Evening'), ('spot', 'Spot'), ('lmba_morning', 'LBMA Morning'), ('lbma_evening', 'LBMA Evening')]
                                    , string="Source of Price")
    sample_ct_id = fields.Many2one("project.container", string="Sample CT", domain="[('state','in',('new','confirmed','inprogress','planned'))]" )
    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_2 = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_3 = fields.Many2one('project.refining.sample', string='Refining Sample')

    is_analysis_for_certification = fields.Boolean()
    is_reference_sample_analysis = fields.Boolean()
    is_actual_result = fields.Boolean()

    @api.onchange('analysis_for_certification')
    def onchange_analysis_for_certification(self):
        if self.analysis_for_certification:
            self.is_analysis_for_certification = True

    @api.onchange('reference_sample_analysis')
    def onchange_reference_sample_analysis(self):
        if self.reference_sample_analysis:
            self.is_reference_sample_analysis = True

    @api.onchange('actual_result')
    def onchange_actual_result(self):
        if self.actual_result:
            self.is_actual_result = True

    @api.depends('lme_price_discount')
    def _lme_percentage(self):
        for rec in self:
            buy_price_discount = 0.0
            if rec.lme_price_discount:
                buy_price_discount = 100 - rec.lme_price_discount
            rec.update({
                'buy_price_discount': buy_price_discount
            })
    @api.depends('return_percentage')
    def _commission_percentage(self):
        for rec in self:
            deduction_percentage = 0.0
            if rec.return_percentage:
                deduction_percentage = 100 - rec.return_percentage
            rec.update({
                'dedection_percentage': deduction_percentage
            })

    @api.depends('lbma_price')
    def _compute_gram_price(self):
        for rec in self:
            gram_price = rec.lbma_price / 1000
            rec.update({
                'price_per_gram': gram_price
            })

    @api.depends('actual_result', 'dedection_percentage', 'minimum_levy')
    def _compute_remaining_metal(self):
        for rec in self:
            remaining_metal = 0.00
            print(rec.actual_result * (rec.dedection_percentage / 100), "+++++++++++++++++++++++")
            if rec.minimum_levy and rec.minimum_levy > (rec.actual_result * (rec.dedection_percentage / 100)):
                deduction = rec.minimum_levy
            else:
                deduction = rec.actual_result * (rec.dedection_percentage / 100)
            if rec.actual_result:
                remaining_metal = rec.actual_result - deduction
            rec.update({
                'remaining_metal': remaining_metal
            })

    @api.depends('price_per_gram', 'remaining_metal', 'buy_price_discount')
    def _compute_buying_price(self):
        for rec in self:
            offer_buying_price = 0.00
            offer_buying_price = rec.price_per_gram * rec.remaining_metal * (1 - (rec.buy_price_discount / 100))
            rec.update({
                'offer_buying_price': offer_buying_price
            })

    @api.depends('offer_buying_price', 'treatment_cost')
    def _compute_final_purchase_price(self):
        for rec in self:
            final_purchase_price = 0.00
            final_purchase_price = rec.offer_buying_price - rec.treatment_cost
            rec.update({
                'final_purchase_price': final_purchase_price
            })


class RutheniumRefiningCost(models.Model):
    _name = "ruthenium.refining.cost"

    ruthenium_cost_id = fields.Many2one('project.entries', string="Ruthenium Refining cost line Ref")
    analysis_for_certification = fields.Float('Analyse CAP (g) pas obligatoire', digits=(16, 3))
    reference_sample_analysis = fields.Float('Analyse Echantillon de Référence (g)', digits=(16, 3))
    actual_result = fields.Float('Résultats après traitement (g)', digits=(16, 3))
    dedection_percentage = fields.Float('Pourcentage restitution')
    buy_price_discount = fields.Float('Pourcentage remise contre prix LME',compute='_lme_percentage')
    remaining_metal = fields.Float('Solde en compte client', compute="_compute_remaining_metal", digits=(16, 3))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    lbma_price = fields.Monetary('Prix LBMA/LME par kg', currency_field='currency_id')
    offer_buying_price = fields.Monetary('Offre de Rachat', currency_field='currency_id', compute="_compute_buying_price")
    treatment_cost = fields.Monetary('Frais de préstation', currency_field='currency_id')
    final_purchase_price = fields.Monetary('Offre actuelle', currency_field='currency_id', compute="_compute_final_purchase_price")
    price_per_gram = fields.Float("rix LBMA/LME par g", compute='_compute_gram_price')
    waste_nature = fields.Char("Nature du déchet")
    project_id = fields.Many2one("project.entries", string="Project ID")
    minimum_levy = fields.Float("Minimum Levy(g)")
    return_percentage = fields.Float('Pourcentage restitution')
    lme_price_discount = fields.Float('Pourcentage remise contre prix LME')
    price_date = fields.Date("Date of Price")
    price_source = fields.Selection([('lme_morning', 'LME Morning'), ('lme_evening', 'LME Evening'), ('spot', 'Spot'), ('lmba_morning', 'LBMA Morning'), ('lbma_evening', 'LBMA Evening')]
                                    , string="Source of Price")
    sample_ct_id = fields.Many2one("project.container", string="Sample CT", domain="[('state','in',('new','confirmed','inprogress','planned'))]" )
    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_2 = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_3 = fields.Many2one('project.refining.sample', string='Refining Sample')

    is_analysis_for_certification = fields.Boolean()
    is_reference_sample_analysis = fields.Boolean()
    is_actual_result = fields.Boolean()

    @api.onchange('analysis_for_certification')
    def onchange_analysis_for_certification(self):
        if self.analysis_for_certification:
            self.is_analysis_for_certification = True

    @api.onchange('reference_sample_analysis')
    def onchange_reference_sample_analysis(self):
        if self.reference_sample_analysis:
            self.is_reference_sample_analysis = True

    @api.onchange('actual_result')
    def onchange_actual_result(self):
        if self.actual_result:
            self.is_actual_result = True

    @api.depends('lme_price_discount')
    def _lme_percentage(self):
        for rec in self:
            buy_price_discount = 0.0
            if rec.lme_price_discount:
                buy_price_discount = 100 - rec.lme_price_discount
            rec.update({
                'buy_price_discount': buy_price_discount
            })
    @api.depends('return_percentage')
    def _commission_percentage(self):
        for rec in self:
            deduction_percentage = 0.0
            if rec.return_percentage:
                deduction_percentage = 100 - rec.return_percentage
            rec.update({
                'dedection_percentage': deduction_percentage
            })

    @api.depends('lbma_price')
    def _compute_gram_price(self):
        for rec in self:
            gram_price = rec.lbma_price / 1000
            rec.update({
                'price_per_gram': gram_price
            })

    @api.depends('actual_result', 'dedection_percentage', 'minimum_levy')
    def _compute_remaining_metal(self):
        for rec in self:
            remaining_metal = 0.00
            print(rec.actual_result * (rec.dedection_percentage / 100), "+++++++++++++++++++++++")
            if rec.minimum_levy and rec.minimum_levy > (rec.actual_result * (rec.dedection_percentage / 100)):
                deduction = rec.minimum_levy
            else:
                deduction = rec.actual_result * (rec.dedection_percentage / 100)
            if rec.actual_result:
                remaining_metal = rec.actual_result - deduction
            rec.update({
                'remaining_metal': remaining_metal
            })
    @api.depends('price_per_gram', 'remaining_metal', 'buy_price_discount')
    def _compute_buying_price(self):
        for rec in self:
            offer_buying_price = 0.00
            offer_buying_price = rec.price_per_gram * rec.remaining_metal * (1 - (rec.buy_price_discount / 100))
            rec.update({
                'offer_buying_price': offer_buying_price
            })

    @api.depends('offer_buying_price', 'treatment_cost')
    def _compute_final_purchase_price(self):
        for rec in self:
            final_purchase_price = 0.00
            final_purchase_price = rec.offer_buying_price - rec.treatment_cost
            rec.update({
                'final_purchase_price': final_purchase_price
            })

class IridiumRefiningCost(models.Model):
    _name = "iridium.refining.cost"

    iridium_cost_id = fields.Many2one('project.entries', string="Iridium Refining cost line Ref")
    analysis_for_certification = fields.Float('Analyse CAP (g) pas obligatoire', digits=(16, 3))
    reference_sample_analysis = fields.Float('Analyse Echantillon de Référence (g)', digits=(16, 3))
    actual_result = fields.Float('Résultats après traitement (g)', digits=(16, 3))
    dedection_percentage = fields.Float('Pourcentage restitution')
    buy_price_discount = fields.Float('Pourcentage remise contre prix LME',compute='_lme_percentage')
    remaining_metal = fields.Float('Solde en compte client', compute="_compute_remaining_metal", digits=(16, 3))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    lbma_price = fields.Monetary('Prix LBMA/LME par kg', currency_field='currency_id')
    offer_buying_price = fields.Monetary('Offre de Rachat', currency_field='currency_id', compute="_compute_buying_price")
    treatment_cost = fields.Monetary('Frais de préstation', currency_field='currency_id')
    final_purchase_price = fields.Monetary('Offre actuelle', currency_field='currency_id', compute="_compute_final_purchase_price")
    price_per_gram = fields.Float("rix LBMA/LME par g", compute='_compute_gram_price')
    waste_nature = fields.Char("Nature du déchet")
    project_id = fields.Many2one("project.entries", string="Project ID")
    minimum_levy = fields.Float("Minimum Levy(g)")
    return_percentage = fields.Float('Pourcentage restitution')
    lme_price_discount = fields.Float('Pourcentage remise contre prix LME')
    price_date = fields.Date("Date of Price")
    price_source = fields.Selection([('lme_morning', 'LME Morning'), ('lme_evening', 'LME Evening'), ('spot', 'Spot'), ('lmba_morning', 'LBMA Morning'), ('lbma_evening', 'LBMA Evening')]
                                    , string="Source of Price")
    sample_ct_id = fields.Many2one("project.container", string="Sample CT", domain="[('state','in',('new','confirmed','inprogress','planned'))]" )
    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_2 = fields.Many2one('project.refining.sample', string='Refining Sample')
    refining_sample_id_3 = fields.Many2one('project.refining.sample', string='Refining Sample')

    is_analysis_for_certification = fields.Boolean()
    is_reference_sample_analysis = fields.Boolean()
    is_actual_result = fields.Boolean()

    @api.onchange('analysis_for_certification')
    def onchange_analysis_for_certification(self):
        if self.analysis_for_certification:
            self.is_analysis_for_certification = True

    @api.onchange('reference_sample_analysis')
    def onchange_reference_sample_analysis(self):
        if self.reference_sample_analysis:
            self.is_reference_sample_analysis = True

    @api.onchange('actual_result')
    def onchange_actual_result(self):
        if self.actual_result:
            self.is_actual_result = True

    @api.depends('lme_price_discount')
    def _lme_percentage(self):
        for rec in self:
            buy_price_discount = 0.0
            if rec.lme_price_discount:
                buy_price_discount = 100 - rec.lme_price_discount
            rec.update({
                'buy_price_discount': buy_price_discount
            })
    @api.depends('return_percentage')
    def _commission_percentage(self):
        for rec in self:
            deduction_percentage = 0.0
            if rec.return_percentage:
                deduction_percentage = 100 - rec.return_percentage
            rec.update({
                'dedection_percentage': deduction_percentage
            })

    @api.depends('lbma_price')
    def _compute_gram_price(self):
        for rec in self:
            gram_price = rec.lbma_price / 1000
            rec.update({
                'price_per_gram': gram_price
            })

    @api.depends('actual_result', 'dedection_percentage', 'minimum_levy')
    def _compute_remaining_metal(self):
        for rec in self:
            remaining_metal = 0.00
            print(rec.actual_result * (rec.dedection_percentage / 100), "+++++++++++++++++++++++")
            if rec.minimum_levy and rec.minimum_levy > (rec.actual_result * (rec.dedection_percentage / 100)):
                deduction = rec.minimum_levy
            else:
                deduction = rec.actual_result * (rec.dedection_percentage / 100)
            if rec.actual_result:
                remaining_metal = rec.actual_result - deduction
            rec.update({
                'remaining_metal': remaining_metal
            })

    @api.depends('price_per_gram', 'remaining_metal', 'buy_price_discount')
    def _compute_buying_price(self):
        for rec in self:
            offer_buying_price = 0.00
            offer_buying_price = rec.price_per_gram * rec.remaining_metal * (1 - (rec.buy_price_discount / 100))
            rec.update({
                'offer_buying_price': offer_buying_price
            })

    @api.depends('offer_buying_price', 'treatment_cost')
    def _compute_final_purchase_price(self):
        for rec in self:
            final_purchase_price = 0.00
            final_purchase_price = rec.offer_buying_price - rec.treatment_cost
            rec.update({
                'final_purchase_price': final_purchase_price
            })
class ExcelWizard(models.TransientModel):
    _name = "fraction.sort.report"

    fraction_xml = fields.Binary("Download Excel Report")
    fraction_char = fields.Char("Excel File")


class FixedPurchaseExcelWizard(models.TransientModel):
    _name = "fixed.purchase.report"

    fixed_purchase_report_xml = fields.Binary("Download Excel Report")
    fixed_purchase_report_char = fields.Char("Excel File")

class PurchaseOrders(models.Model):
    _name = "project.purchase.orders"

    @api.model
    def default_get(self, fields_name):
        res = super(PurchaseOrders, self).default_get(fields_name)
        if self._context.get('project_entry_id_int'):
            res.update({'project_entry_id_int': self._context.get('project_entry_id_int')})
        if self._context.get('client_id_int'):
            res.update({'client_id_int': self._context.get('client_id_int')})
        return res

    purchase_id = fields.Many2one("purchase.order",string="Purchase Order", required=True)
    untaxed_amount = fields.Float("Untaxed Amount")
    amount = fields.Float("Amount", required=True)
    project_id = fields.Many2one("project.entries",string="Project ID")
    project_entry_id_int = fields.Integer('Project Entries ID')
    client_id_int = fields.Integer('Clinet ID')
    description = fields.Char("Description")

    @api.onchange('purchase_id')
    def onchange_purchase_id(self):
        if self.purchase_id:
            self.amount = self.purchase_id.amount_total
            self.untaxed_amount = self.purchase_id.amount_untaxed


class ProjectAccountMove(models.Model):
    _name = "project.account.move"

    @api.model
    def default_get(self, fields_name):
        res = super(ProjectAccountMove, self).default_get(fields_name)
        return res

    account_id = fields.Many2one("account.move",string="Vendor Bill", required=True)
    untaxed_amount = fields.Float("Untaxed Amount")
    amount = fields.Float("Amount", required=True)
    amount_residual = fields.Float("Amount Due")
    project_id = fields.Many2one('project.entries',string="Project ID")
    project_entry_id_int = fields.Integer('Project Entries ID')
    client_id_int = fields.Integer('Clinet ID')
    description = fields.Char("Description")

    @api.onchange('account_id')
    def onchange_account_id(self):
        if self.account_id:
            self.amount = self.account_id.amount_total
            self.untaxed_amount = self.account_id.amount_untaxed
            self.amount_residual = self.account_id.amount_residual


class ProjectDocs(models.Model):
    _name = 'project.documents'

    name = fields.Char("Description")
    project_doc = fields.Binary("Document")
    file_char = fields.Char("File Name")
    project_id = fields.Many2one("project.entries",string="Project ID")


class ProjectContainers(models.Model):
    _name = 'project.container.line'

    product_id = fields.Many2one("product.product", string="Container", domain="[('product_tmpl_id.reuse_container','=',True)]")
    quantity = fields.Float("Quantity")
    project_id = fields.Many2one("project.entries", string="Project ID")


class ProjectRefiningSample(models.Model):
    _name = 'project.refining.sample'

    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Many2one('stock.production.lot', string='Lot/Serial Number', domain="[('product_id','=',product_id)]")
    quantity = fields.Float('Quantity(kg)', digits=(12,4))
    expected_result = fields.Float('Expected Result', digits=(12,4))
    actual_result = fields.Float('Actual Result(%)', digits=(12,4))
    sample_line_id = fields.Many2one("project.entries", string="Project Entries Ref")
