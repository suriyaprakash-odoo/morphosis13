from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

class LogisticsManagement(models.Model):
    _name = "logistics.management"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Logistics Management"

    name = fields.Char('Name' , default='New')
    partner_id = fields.Many2one('res.partner',string='Logistics',domain="[('is_transporter', '=', True)]")
    company_id = fields.Many2one('res.company',string='Company', required=1)
    user_id = fields.Many2one(
        'res.users', string='Purchase Representative', index=True, tracking=True,
        default=lambda self: self.env.user, check_company=True)
    origin = fields.Many2one('project.entries',string='Project Entry')
    sales_origin = fields.Many2one('sale.order',string='Sale Order')
    pickup_partner_id = fields.Many2one('res.partner',string='Pickup Point')
    pickup_partner_location_id = fields.Many2one('res.partner', domain="[('parent_id' , '=?' , pickup_partner_id)]",string='Pickup Location')
    delivery_partner_location_id = fields.Many2one('res.partner', domain="[('parent_id' , '=?' , delivery_partner_id)]",string='Delivery Location')
    pickup_street = fields.Char()
    pickup_street2 = fields.Char()
    pickup_zip = fields.Char(change_default=True)
    pickup_city = fields.Char()
    pickup_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', pickup_countries_id)]")
    pickup_countries_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    pickup_country_id = fields.Many2one('res.country.state',string='Department of Origin')
    delivery_partner_id = fields.Many2one('res.partner',string='Delivery Point')
    delivery_street = fields.Char()
    delivery_street2 = fields.Char()
    delivery_zip = fields.Char(change_default=True)
    delivery_city = fields.Char()
    delivery_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', delivery_countries_id)]")
    delivery_countries_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    delivery_country_id = fields.Many2one('res.country.state',string='Department of Destination')
    pickup_date_type = fields.Selection([
        ('specific', 'Specific Date'),
        ('between', 'In between'),
        ('as_soon_as_possible', 'As soon as possible')
        ],string='Pickup date type')
    pickup_date = fields.Date('Date of Pickup')
    pickup_earliest_date = fields.Date('Earliest Date')
    pickup_latest_date = fields.Date('Latest Date')
    expected_delivery = fields.Date('Expected date of delivery')
    expected_delivery_start_time = fields.Float('Time Duration')
    expected_delivery_end_time = fields.Float('Time Duration')
    transport_type = fields.Selection([
        ('collect' , 'Collection'),
        ('delivery' , 'Delivery'),
        ('crosstrade' , 'Cross-Trade')
        ],string='Type of Journey')
    tranport_mode = fields.Selection([
        ('direct' , 'Direct'),
        ('route' , 'Route Groupage'),
        ('air' , 'Air Flight'),
        # ('sea' , 'Sea Flight'),
        ('lcl' , 'Maritime Groupage(LCL)'),
        ('fcl' , 'Maritime Groupage(FCL)')
        ],string='Transport Mode',default='direct')
    container_type = fields.Selection([
        ('20' , '20ft'),
        ('40' , '40ft'),
        ('hc' , '40ft HC'),
        ('ot' , '40ft OT')
        ],string='Container Load')
    loading_port_id = fields.Many2one('res.sea.ports',string='Port of Loading')
    loading_port_code = fields.Char(string='Code')
    unloading_port_id = fields.Many2one('res.sea.ports',string='Port of Unloading')
    unloading_port_code = fields.Char(string='Code')
    is_full_load = fields.Boolean('Full Load?')
    gross_weight = fields.Float('Gross weight(Kg)', required=1)
    # weight_uom_id = fields.Many2one('uom.uom','Weight Unit', required=1)
    no_of_container = fields.Integer('Quantity of Container')
    linear_meter = fields.Selection([
        ('1' , '1'),
        ('2' , '2'),
        ('3' , '3'),
        ('4' , '4'),
        ('5' , '5'),
        ('6' , '6'),
        ('7' , '7'),
        ('8' , '8'),
        ('9' , '9'),
        ('10' , '10'),
        ('11' , '11'),
        ('12' , '12'),
        ('13' , '13')
        ],string="Linear Meter")
    transporter_id = fields.Char('ID of transporter')
    lorry_registration = fields.Char('Registration of Lorry')
    lorry_type = fields.Selection([
        ('container' , 'container'),
        ('curtainside' , 'Curtain-side'),
        ('semi_trailer' , 'Semi-Trailer'),
        ('rigid_body_truck' , 'Rigid Body Truck'),
        ('moving_floor' , 'Moving Floor')
        ],string='Type of Lorry')
    is_tail_lift = fields.Boolean('Tail-Lift')
    notes = fields.Text('Instruction and Notes')
    client_feedback_score = fields.Selection([
        ('0' , '0'),
        ('1' , '1'),
        ('2' , '2'),
        ('3' , '3'),
        ('4' , '4'),
        ('5' , '5')
        ],string='Client Feedback Score')
    transport_cost = fields.Monetary('Price for Transport', currency_field='currency_id')
    incoterms_id = fields.Many2one('account.incoterms',string='Incoterms')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    container_count = fields.Selection([
        ('specified' , 'Specified'),
        ('not_specified' , 'Not Specified')
        ], string = 'Container Count')
    logistics_for = fields.Selection([
        ('sale' , 'Sales'),
        ('purchase' , 'Purchase')
        ],string='Logistics for?')
    active = fields.Boolean('Active',default=True)

    is_adr = fields.Boolean('Is ADR Required')

    adr_num = fields.Char('ADR Number')
    tunnel_code_id = fields.Many2one('tunnel.code',string='Tunnel Code')
    adr_class_id = fields.Many2one('adr.class',string='Classes')
    adr_pickup_type_id = fields.Many2one('adr.pickup.type',string='Package Type')
    hazard_type_id = fields.Many2one('hazard.number',string='Hazard Type')
    un_code = fields.Many2one('un.code', string='UN Code')

    adr_number = fields.Selection([
        ('fuel_cells','3166 - Fuel Cells'),
        ('li_metal_battery','3090 - Lithium Metal Batteries'),
        ('li_cells','3480 - Lithium Cells'),
        ('li_battery_equiped','3091 - Lithium Batteries in Equipment'),
        ('ni_metal_hydride','3496 - Nickel Metal Hydride')
        ],string="UN List Number")
    adr_class = fields.Selection([
        ('explosives','Explosives'),
        ('glasses','Gases'),
        ('flammable_liquid','Flammable Liquids'),
        ('flammable_solid','Flammable Solids'),
        ('oxidizer','Oxidizers'),
        ('toxic_infactious','Toxic & Infectious'),
        ('radioactive','Radioactive'),
        ('corrosive','Corrosives'),
        ('miscellaneous_dangerous,','Miscellaneous Dangerous Goods'),
        ('iithium_ion','Lithium Ion Batteries')
        ],string="Classes")
    adr_packing_group = fields.Selection([
        ('high_danger','I - High Danger'),
        ('medium_danger','II - Medium Danger'),
        ('low_danger','III - Low Danger')
        ],string="Package Type")

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    reciption_date = fields.Date('Date of Reciption')
    entry_gross_weight = fields.Float('Gross weight at entry(Kg)')
    entry_weight_uom_id = fields.Many2one('uom.uom','Weight Unit at entry')
    licence_plate = fields.Char('Registraion of container')
    tare_of_lorry = fields.Float('Tare of lorry')
    loaded_lorry_weight = fields.Float('Net weight of load with container(Kg)')
    actual_container = fields.Integer('Actual numer of containers')
    is_conforms_with_deliver_note = fields.Boolean('Conforms with delivery note')
    bsdannex = fields.Selection([
        ('bsd' , 'BSD'),
        ('annux7' , 'Annexe7')
        ],string='BSD/Annexe7')
    waste_in_container = fields.Char('Standard waste codes of each container')
    delivery_note = fields.Binary('Delivery note of Supplier')
    is_non_conformity = fields.Boolean('Non-Conformity Notice')

    shipping_date = fields.Date('Shipping Date')
    gross_weight_on_bridge = fields.Float('Gross weight on Bridge(Kg)')
    gross_weight_on_bridge_uom_id = fields.Many2one('uom.uom','Weight Unit at Bridge')
    delivery_tare_of_lorry = fields.Float('Tare of lorry')
    date_deadline = fields.Date('Deadline for filing customs papers')
    load_net_weight = fields.Float('Net weight of load(Kg)')
    delivery_licence_plate = fields.Char('Registraion of container')
    customs_seal_number = fields.Char('Customs Seal Number')
    delivery_documents = fields.Binary('Documents')
    waste_code = fields.Char('Waste Code',default="16 02 16")
    customs_classification_code = fields.Char('Customs Classification Code')
    containers_to_ship = fields.Many2one(comodel_name='stock.picking',string='Containers to Ship')
    weight_to_ship = fields.Float('Weight to Ship(Kg)')
    weight_to_ship_uom_id = fields.Many2one('uom.uom',string='Weight to ship UOM')
    volume_to_ship = fields.Selection([
        ('20' , '20ft'),
        ('40' , '40ft'),
        ('hc' , '40ft HC'),
        ('ot' , '40ft OT')
        ],string='Volume to Ship')

    status = fields.Selection([
        ('new' , 'New'),
        ('request' , 'RFQ Sent'),
        ('approved' , 'Approved'),
        ('delivered' , 'Delivered'),
        ('rejected' , 'Rejected')
        ],string='Status',default='new')

    carton_ids = fields.One2many('carton.logistics.line','carton_id',string="Carton lines")

    notes = fields.Text('Notes')

    purchase_order_id = fields.Many2one('purchase.order',string="Purchase order ref")
    
    opening_hours_start = fields.Char('Opening Hours Start')
    opening_hours_end = fields.Char('Opening Hours End')
    morning_opening_hours_start = fields.Char('Morning Opening Hours Start')
    morning_opening_hours_end = fields.Char('Morning Opening Hours End')
    evening_opening_hours_start = fields.Char('Evening Opening Hours Start')
    evening_opening_hours_end = fields.Char('Evening Opening Hours End')

    success_msg = fields.Char("Messgae",default="Shipment Created")

    bsd_next_seq = fields.Integer('Next BSD Sequence', default='01')
    annexe_next_seq = fields.Integer('Next Annexe7 Sequence', default='01')
    current_bsd_sequence = fields.Char('Current BSD Sequence')
    current_annexe_sequence = fields.Char('Current Annexe7 Sequence')

    transport_documents_line_ids = fields.One2many('transport.document','transport_documents_line_id', string="Transport Documents Ref")
    is_3rd_party = fields.Boolean("Is 3rd Party")
    adr_line = fields.One2many("adr.line","logistics_id",string="ADR Line")
    vendor_ref = fields.Char("Vendor Reference")
    buyer_ref = fields.Char("Buyer Reference")

    stock_picking_id = fields.Many2one(comodel_name="stock.picking",string="Shipment",compute="_compute_stock_picking")

    stock_picking_weight = fields.Float(string="Shipment Weight(Kg)",compute="_compute_stock_picking")

    material = fields.Text(string="Material")
    dimension = fields.Char(string="Colisage")
    # bsd
    number_bsd = fields.Char(string="Numéro du bordereau de rattachement/Annexe7")
    pretreatment_code = fields.Selection([
        ('d9' , 'D9'),
        ('r4' , 'R4'),
        ('r5' , 'R5'),
        ('r8' , 'R8'),
    ],string="Opération d'élimination/valorisation prévue")
    waste_form = fields.Selection([('solide','Solide'),('liquide','Liquide'),('gaseux','Gaseux')],string="Consistance")
    packing_type = fields.Selection([('list of benne','List of benne'),('citerne','Citerne'),('big bag','Big bag'),('palette','Palette'),('grv','GRV'),('fut','fût'),('mixte','Mixte')],string="Conditionnement")
    buy_weight_confirmed = fields.Integer("Quantité réellé présentée")
    buyer_reception_date = fields.Date("Date de présentation")
    buyer_accept_lot = fields.Boolean("Lot Accepté")
    buyer_reject_reason = fields.Text("Motif de refus")
    buyer_treatment_date = fields.Date("Date de traitement")
    buyer_treatment_code = fields.Selection([
        ('d9' , 'D9'),
        ('r4' , 'R4'),
        ('r5' , 'R5'),
        ('r8' , 'R8'),
    ],string="Code D/R")
    # annexe
    second_carrier = fields.Date("Date of Transfer")
    third_carrier = fields.Date("Date of Transfer")
    despatch_country = fields.Many2one('res.country',string="Export/dispatch")
    transit_country_1 = fields.Many2one('res.country',string="Transit country 1")
    transit_country_2 = fields.Many2one('res.country',string="Transit country 2")
    transit_country_3 = fields.Many2one('res.country',string="Transit country 3")
    destination_country = fields.Many2one('res.country',string="Import Destination")
    declaration_date = fields.Date("Declaration")
    reception_date = fields.Date("Date of reception")
    confirmed_quantity = fields.Float("Confirmed Quantity")

    is_transporter2 = fields.Boolean("Include Transporter2")
    transporter2 = fields.Many2one('res.partner',string="Transporter 2")
    transporter2_street = fields.Char()
    transporter2_zip = fields.Char()
    transporter2_city = fields.Char()
    transporter2_phone = fields.Char()
    transporter2_email = fields.Char()
    transporter2_contact = fields.Many2one('res.partner',string="Transporter Contact")

    is_transporter3 = fields.Boolean("Include Transporter3")
    transporter3 = fields.Many2one('res.partner',string="Transporter 3")
    transporter3_street = fields.Char()
    transporter3_zip = fields.Char()
    transporter3_city = fields.Char()
    transporter3_phone = fields.Char()
    transporter3_email = fields.Char()
    transporter3_contact = fields.Many2one('res.partner',string="Transporter Contact")
    # client = fields.Many2one('res.partner',string="Client")
    # client_street = fields.Char()
    # client_zip = fields.Char()
    # client_city = fields.Char()
    # client_phone = fields.Char()
    # client_email = fields.Char()
    # cleint_contact = fields.Many2one('res.partner')

    adr_packing_group = fields.Selection([
        ('high_danger', 'I - High Danger'),
        ('medium_danger', 'II - Medium Danger'),
        ('low_danger', 'III - Low Danger')
    ], string="Package Type")

    hayons = fields.Selection([('hayons','Hayons'),('hayons_t','Hayons + transpalette'),('hayons_te','Hayons + transpalette electrique')])

    grid_rotation = fields.Char('rotation de grille')


    @api.onchange('pickup_partner_id','delivery_partner_id')
    def onchange_pickup_delivery_location_id(self):
        if self.pickup_partner_id and self.logistics_for == "purchase":
            self.morning_opening_hours_start = self.pickup_partner_id.morning_opening_hours_start
            self.morning_opening_hours_end = self.pickup_partner_id.morning_opening_hours_end
            self.evening_opening_hours_start = self.pickup_partner_id.evening_opening_hours_start
            self.evening_opening_hours_end = self.pickup_partner_id.evening_opening_hours_end
        elif self.delivery_partner_id and self.logistics_for == "sale":
            self.morning_opening_hours_start = self.delivery_partner_id.morning_opening_hours_start
            self.morning_opening_hours_end = self.delivery_partner_id.morning_opening_hours_end
            self.evening_opening_hours_start = self.delivery_partner_id.evening_opening_hours_start
            self.evening_opening_hours_end = self.delivery_partner_id.evening_opening_hours_end
        # else:
        #     self.morning_opening_hours_start = False
        #     self.morning_opening_hours_end = False
        #     self.evening_opening_hours_start = False
        #     self.evening_opening_hours_end = False


    def get_term_condition(self):
        term = """<p style='color:red;text-align:center;font-weight:bold;'>*Attention transport sous attestation de transport de déchets DGX et NON DGX*<br/>
        DGX<br/>
        *Le chauffeur doit l'avoir impérativement dans son camion*<br/>
        *Reaffrètement interdit*</p>
        """
        return term

    term = fields.Html(string="Terms and Conditions", default=get_term_condition)

    bsd_annexe_line_ids = fields.One2many('bsdannexe.product.line', 'bsd_annexe_line_id', string='Product Line Ref')

    def _compute_stock_picking(self):
        for logistic in self:
            if logistic.logistics_for == "purchase":
                get_picking = self.env['stock.picking'].search([('project_entry_id','=',logistic.origin.id),('origin','=',logistic.origin.origin.name)],limit=1)
                if get_picking:
                    logistic.stock_picking_id = get_picking.id
                    logistic.stock_picking_weight = get_picking.weight_at_entry
                else:
                    logistic.stock_picking_id = False
                    logistic.stock_picking_weight = 0

            elif logistic.logistics_for == "sale":
                get_picking = self.env['stock.picking'].search([('origin','=',logistic.sales_origin.name)],limit=1)
                if get_picking:
                    logistic.stock_picking_id = get_picking.id
                    logistic.stock_picking_weight = get_picking.sale_logistics_weight_at_exit
                else:
                    logistic.stock_picking_id = False
                    logistic.stock_picking_weight = 0
            else:
                logistic.stock_picking_id = False

    @api.onchange('loading_port_id')
    def onchange_loading_port_id(self):
        if self.loading_port_id:
            self.loading_port_code = self.loading_port_id.code

    @api.onchange('unloading_port_id')
    def onchange_unloading_port_id(self):
        if self.unloading_port_id:
            self.unloading_port_code = self.unloading_port_id.code

    @api.onchange('pickup_partner_id')
    def onchange_pickup_partner_id(self):
        if self.pickup_partner_id:
            if self.pickup_partner_id.short_code:
                short_code = self.pickup_partner_id.short_code + '/'
            else:
                short_code = ''
            if self.pickup_partner_id.ref:
                ref = self.pickup_partner_id.ref + '/'
            else:
                ref = ''
            self.vendor_ref = ref + short_code + str(self.pickup_partner_id.lot_sequence_number)

    # @api.model
    # def create(self, vals):
    #     if vals.get('logistics') == 'purchase':
    @api.onchange('transporter2')
    def onchange_transporter2(self):
        if self.transporter2:
            self.transporter2_street = self.transporter2.street
            self.transporter2_zip = self.transporter2.zip
            self.transporter2_city = self.transporter2.city
            self.transporter2_phone = self.transporter2.phone
            self.transporter2_email = self.transporter2.email

    @api.onchange('transporter3')
    def onchange_transporter3(self):
        if self.transporter3:
            self.transporter3_street = self.transporter3.street
            self.transporter3_zip = self.transporter3.zip
            self.transporter3_city = self.transporter3.city
            self.transporter3_phone = self.transporter3.phone
            self.transporter3_email = self.transporter3.email

    @api.model
    def create(self, vals):
        res = super(LogisticsManagement, self).create(vals)
        if res.is_adr and not res.adr_line:
            raise UserError("Please add some ADR lines!")
        return res

    def write(self, values):
        res = super(LogisticsManagement, self).write(values)
        if self.is_adr and not self.adr_line:
            raise UserError("Please add some ADR lines!")
        return res

    def name_get(self):
        result = []
        for record in self:
            if record.vendor_ref:
                ref = ' -' + record.vendor_ref
            else:
                ref = ''
            if record.pickup_partner_id:
                name = record.name + ' [' + str(record.pickup_partner_id.name) + ref + ']'
                result.append((record.id, name))
            else:
                result.append((record.id, record.name))
        return result

    @api.onchange('pickup_partner_location_id')
    def onchange_pickup_address(self):
        if self.pickup_partner_location_id:
            self.pickup_street = self.pickup_partner_location_id.street
            self.pickup_street2 = self.pickup_partner_location_id.street2
            self.pickup_zip = self.pickup_partner_location_id.zip
            self.pickup_city = self.pickup_partner_location_id.city
            self.pickup_state_id = self.pickup_partner_location_id.state_id
            self.pickup_countries_id = self.pickup_partner_location_id.country_id
        else:
            self.pickup_street = self.pickup_partner_id.street
            self.pickup_street2 = self.pickup_partner_id.street2
            self.pickup_zip = self.pickup_partner_id.zip
            self.pickup_city = self.pickup_partner_id.city
            self.pickup_state_id = self.pickup_partner_id.state_id
            self.pickup_countries_id = self.pickup_partner_id.country_id

            
    @api.onchange('delivery_partner_location_id')
    def onchange_delivery_address(self):
        if self.delivery_partner_location_id:
            self.delivery_street = self.delivery_partner_location_id.street
            self.delivery_street2 = self.delivery_partner_location_id.street2
            self.delivery_zip = self.delivery_partner_location_id.zip
            self.delivery_city = self.delivery_partner_location_id.city
            self.delivery_state_id = self.delivery_partner_location_id.state_id
            self.delivery_countries_id = self.delivery_partner_location_id.country_id
        else:
            self.delivery_street = self.delivery_partner_id.street
            self.delivery_street2 = self.delivery_partner_id.street2
            self.delivery_zip = self.delivery_partner_id.zip
            self.delivery_city = self.delivery_partner_id.city
            self.delivery_state_id = self.delivery_partner_id.state_id
            self.delivery_countries_id = self.delivery_partner_id.country_id
              
    def action_view_project_entry(self):

      return{
          'name': _('Project Entry'),
          'type':'ir.actions.act_window',
          'view_type':'form',
          'view_mode':'tree,form',
          'res_model':'project.entries',
          'res_id':self.origin.id,
          'views_id':False,
          'views':[(self.env.ref('ppts_project_entries.project_entries_form_view').id or False, 'form')],
          }
              
    def action_view_transport_po(self):

      return{
          'name': _('Purchase Order'),
          'type':'ir.actions.act_window',
          'view_type':'form',
          'view_mode':'tree,form',
          'res_model':'purchase.order',
          'res_id':self.purchase_order_id.id,
          'views_id':False,
          'views':[(self.env.ref('purchase.purchase_order_form').id, 'form')],
          }
              
    def action_view_shipment(self):
        if self.logistics_for == 'purchase':
            shipment_id = self.env['stock.picking'].search([('project_entry_id' , '=' , self.origin.id)])
        else:
            shipment_id = self.env['stock.picking'].search([('origin' , '=' , self.sales_origin.name)])

        return{
          'name': _('Shipment'),
          'type':'ir.actions.act_window',
          'view_type':'form',
          'view_mode':'tree,form',
          'res_model':'stock.picking',
          'res_id':shipment_id.id,
          'views_id':False,
          'views':[(self.env.ref('stock.view_picking_form').id, 'form')],
          }


    def action_send_transport_rfq(self):
        '''
        This function opens a window to compose an email, with the edit logistics request template message loaded by default
        '''
        if self.partner_id.email:
            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('ppts_logistics', 'email_template_send_transport_request')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            ctx = dict(self.env.context or {})

            ctx.update({
                'default_model': 'logistics.management',
                'active_model': 'logistics.management',
                'active_id': self.ids[0],
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'custom_layout': "mail.mail_notification_paynow",
                'default_attachment_ids':[],
                'model_description' : 'Request for Quotation',
                'force_email': True,
                'mark_logistics_as_sent': True
            })

            print(ctx)

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
        else:
            raise ValidationError(_('Please Email ID for logistics in partner'))
        
    
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_logistics_as_sent'):
            self.filtered(lambda o: o.status == 'new').write({'status': 'request'})
        return super(LogisticsManagement, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)


    def action_approve_request(self):

        ctx = dict(self.env.context or {})

        ctx.update({
                    'active_id' : self.ids[0],
                    'partner_id' : self.partner_id.id,
                    'default_add_cost_existing_po': self.origin.add_cost_existing_po,
                })

        view_id = self.env.ref('ppts_logistics.view_create_transport_rfq').id
        return{
                'name': ('Create Transport PO'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'transport.rfq',
                'views': [(view_id, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx
                }

  
    def print_bsd_report(self):
        bsd_sequence = ''
        if self.logistics_for == 'sale':
            bsd_sequence = str(self.sales_origin.name) + '/BSD/0' + str(self.bsd_next_seq)
            self.current_bsd_sequence = bsd_sequence
            self.bsd_next_seq += 1
        else:
            bsd_sequence = str(self.origin.name) + '/BSD/0' + str(self.bsd_next_seq)
            self.current_bsd_sequence = bsd_sequence
            self.bsd_next_seq += 1

        return self.env.ref('ppts_logistics.report_bsd').report_action(self)
    
    def print_annux_report(self):
        annexe_sequence = ''
        if self.logistics_for == 'sale':
            annexe_sequence = str(self.sales_origin.name) + '/Annexe7/0' + str(self.annexe_next_seq)
            self.current_annexe_sequence = annexe_sequence
            self.annexe_next_seq += 1
        else:
            annexe_sequence = str(self.origin.name) + '/Annexe7/0' + str(self.annexe_next_seq)
            self.current_annexe_sequence = annexe_sequence
            self.annexe_next_seq += 1

        return self.env.ref('ppts_logistics.report_annux').report_action(self)

    def action_reject_request(self):

        self.status = 'rejected'

class TransportDocuments(models.Model):
    _name = 'transport.document'
    _rec_name = 'transport_documents'

    transport_documents = fields.Binary('Transport Documents')
    transport_documents_line_id = fields.Many2one('logistics.management', string="Logistics Management Ref")


class ResSeaPorts(models.Model):
    _name = 'res.sea.ports'

    name = fields.Char('Name', required=1)
    code = fields.Char('Code', required=1)
    state_id = fields.Many2one('res.country.state',string='State')
    country_id = fields.Many2one('res.country',string='Country', required=1)


    
class CartonLine(models.Model):
    _name = "carton.logistics.line"

    name = fields.Char("Carton Number")
    cost = fields.Float("Cost")
    carton_id = fields.Many2one('logistics.management', string='Logistics Management Reference')


class TunnelCode(models.Model):
    _name = 'tunnel.code'

    name = fields.Char('Tunnel Code')

class AdrClass(models.Model):
    _name = 'adr.class'
    _rec_name = 'code'

    code = fields.Char('Code')
    lable = fields.Char('Class Name')

class AdrPickupType(models.Model):
    _name = 'adr.pickup.type'
    _rec_name = 'code'

    code = fields.Char('Class Code')
    class_type = fields.Char('Class Type')

class HazardNumber(models.Model):
    _name = 'hazard.number'
    _rec_name = 'code'

    code = fields.Char('Hazard Code')
    hazard_name = fields.Char('Hazard Name')

class UNCode(models.Model):
    _name = 'un.code'
    _rec_name = 'code'

    code = fields.Char('UN Code')

class ADRLine(models.Model):
    _name = "adr.line"

    un_code = fields.Many2one('un.code', string='UN Code')
    adr_class_id = fields.Many2one('adr.class', string='ADR Class')
    adr_pickup_type_id = fields.Many2one('adr.pickup.type', string='ADR Package Type')
    hazard_type_id = fields.Many2one('hazard.number', string='Hazard Number')
    tunnel_code_id = fields.Many2one('tunnel.code',string='Tunnel Code')
    logistics_id = fields.Many2one('logistics.management', string='Logistics Management Reference')


class BsdAnnexeProductLine(models.Model):
    _name = "bsdannexe.product.line"

    bsd_annexe_line_id = fields.Many2one('logistics.management')
    product_id = fields.Many2one('product.product', 'Product')
    name = fields.Char('Description')
    product_qty = fields.Float('Quantity')
    product_uom = fields.Many2one('uom.uom', 'UoM')
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    price_subtotal = fields.Float(string='Subtotal')
    price_total = fields.Float(string='Total')
    logistics_id = fields.Many2one('logistics.management', string='Logistics Management Reference')
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
    number_bsd = fields.Char(string="Numéro du bordereau de rattachement",required=1)
    pickup_partner_id = fields.Many2one('res.partner',string='Emetteur du bordereau')
    company_id = fields.Many2one('res.company',string='Company', required=1)
    pickup_street = fields.Char()
    pickup_zip = fields.Char(change_default=True)
    pickup_city = fields.Char()
    pickup_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', pickup_countries_id)]")
    pickup_countries_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    phone = fields.Char("Tél")
    email = fields.Char("Mél")
    contact_person_in = fields.Many2one('res.partner',string='Personne à contacter (for incoming material)')
    contact_person_out = fields.Selection([
        ('cyril' , 'Cyril Boutin'),
        ('blais' , 'Gaëtan Blais'),
        ('kadia' , 'Kadia Deh'),
    ],string='Personne à contacter (Outgoing material)')
    sale_logistics_exit_date_time=fields.Date('')

    delivery_partner_id = fields.Many2one('res.partner',string='Destination Company')
    delivery_street = fields.Char()
    delivery_street2 = fields.Char()
    delivery_zip = fields.Char(change_default=True)
    delivery_city = fields.Char()
    delivery_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', delivery_countries_id)]")
    delivery_countries_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    delivery_phone = fields.Char("Tél")
    delivery_email = fields.Char("Mél")

    logistics_contact = fields.Many2one('res.partner',string="Personne à contacter")
    pretreatment_code = fields.Selection([
        ('d9' , 'D9'),
        ('r4' , 'R4'),
        ('r5' , 'R5'),
        ('r8' , 'R8'),
    ],string="Opération d'élimination/valorisation prévue")

    waste_code = fields.Char('Waste Code')
    waste_form = fields.Selection([('solide','Solide'),('liquide','Liquide'),('gaseux','Gaseux')],string="Consistance")
    product_id = fields.Many2one('product.product',string="Dénomination usuel")

    is_adr = fields.Boolean('Is ADR Required')
    adr_line = fields.One2many("adr.line.wizard","bsd_line","ADR Line")
    adr_num = fields.Char('ADR Number')
    tunnel_code_id = fields.Many2one('tunnel.code',string='Tunnel Code')
    adr_class_id = fields.Many2one('adr.class',string='Classes')
    adr_pickup_type_id = fields.Many2one('adr.pickup.type',string='Package Type')
    hazard_type_id = fields.Many2one('hazard.number',string='Hazard Type')
    un_code = fields.Many2one('un.code', string='UN Code')

    packing_type = fields.Selection([('list of benne','List of benne'),('citerne','Citerne'),('big bag','Big bag'),('palette','Palette'),('grv','GRV'),('fut','fût'),('mixte','Mixte')],string="Conditionnement")
    container_count = fields.Selection([
        ('specified' , 'Specified'),
        ('not_specified' , 'Not Specified')
    ], string = 'Nombre de colis')
    gross_weight_on_bridge = fields.Float('Gross weight on Bridge(Kg)')
    gross_weight_on_bridge_uom_id = fields.Many2one('uom.uom','Weight Unit at Bridge')

    transporter = fields.Many2one('res.partner',string="Transporter name")
    transporter_street = fields.Char()
    transporter_street2 = fields.Char()
    transporter_zip = fields.Char(change_default=True)
    transporter_city = fields.Char()
    transporter_phone = fields.Char("Tél")
    transporter_email = fields.Char("Mél")
    transport_contact = fields.Many2one('res.partner',string="NOM")

    recipt = fields.Many2one
    reciption_date = fields.Date('Date of Reciption')
    expected_delivery = fields.Date('Expected date of delivery')
    r_state_id = fields.Many2one("res.country.state", string='Département', ondelete='restrict')

    subcontractor = fields.Many2one('res.partner',string="Destinataire")
    subcontractor_street = fields.Char()
    subcontractor_street2 = fields.Char()
    subcontractor_zip = fields.Char(change_default=True)
    subcontractor_city = fields.Char()
    subcontractor_phone = fields.Char("Tél")
    subcontractor_email = fields.Char("Mél")
    subcontractor_contact = fields.Many2one('res.partner',string="Transporter Contact")

    buy_weight_confirmed = fields.Integer("Quantité réellé présentée")
    buyer_reception_date = fields.Date("Date de présentation")
    buyer_accept_lot = fields.Boolean("Lot Accepté")
    buyer_reject_reason = fields.Text("Motif de refus")
    buyer_treatment_date = fields.Date("Date de traitement")
    buyer_treatment_code = fields.Selection([
        ('d9' , 'D9'),
        ('r4' , 'R4'),
        ('r5' , 'R5'),
        ('r8' , 'R8'),
    ],string="Code D/R")

    @api.onchange('pickup_partner_id')
    def onchange_pickup_partner_id(self):
        if self.pickup_partner_id:
            self.pickup_street = self.pickup_partner_id.street
            self.pickup_zip = self.pickup_partner_id.zip
            self.pickup_city = self.pickup_partner_id.city
            self.pickup_state_id = self.pickup_partner_id.state_id.id
            self.pickup_countries_id = self.pickup_partner_id.country_id.id
            self.phone = self.pickup_partner_id.phone
            self.email = self.pickup_partner_id.email

    @api.onchange('delivery_partner_id')
    def onchange_delivery_partner_id(self):
        if self.delivery_partner_id:
            self.delivery_street = self.delivery_partner_id.street
            self.delivery_zip = self.delivery_partner_id.zip
            self.delivery_city = self.delivery_partner_id.city
            self.delivery_state_id = self.delivery_partner_id.state_id.id
            self.delivery_countries_id = self.delivery_partner_id.country_id.id
            self.delivery_phone = self.delivery_partner_id.phone
            self.delivery_email = self.delivery_partner_id.email

    @api.onchange('transporter')
    def onchange_transporter(self):
        if self.transporter:
            self.transporter_street = self.transporter.street
            self.transporter_zip = self.transporter.zip
            self.transporter_city = self.transporter.city
            self.transporter_phone = self.transporter.phone
            self.transporter_email = self.transporter.email
            self.transport_contact = self.transporter.id

    @api.onchange('subcontractor')
    def onchange_subcontractor(self):
        if self.subcontractor:
            self.subcontractor_street = self.subcontractor.street
            self.subcontractor_zip = self.subcontractor.zip
            self.subcontractor_city = self.subcontractor.city
            self.subcontractor_phone = self.subcontractor.phone
            self.subcontractor_email = self.subcontractor.email
            self.subcontractor_contact = self.subcontractor.id

class ADRLineWizard(models.TransientModel):
    _name = "adr.line.wizard"

    un_code = fields.Many2one('un.code', string='UN Code')
    adr_class_id = fields.Many2one('adr.class', string='ADR Class')
    adr_pickup_type_id = fields.Many2one('adr.pickup.type', string='ADR Package Type')
    hazard_type_id = fields.Many2one('hazard.number', string='Hazard Number')
    tunnel_code_id = fields.Many2one('tunnel.code',string='Tunnel Code')
    logistics_id = fields.Many2one('logistics.management', string='Logistics Management Reference')

    bsd_line = fields.Many2one(comodel_name="bsdannexe.product.line",string="BSD")
    adrline_id = fields.Many2one(comodel_name="adr.line")