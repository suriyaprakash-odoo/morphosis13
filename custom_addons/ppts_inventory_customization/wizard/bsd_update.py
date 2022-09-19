from odoo import api, fields, models, _



class UpdateBSD(models.TransientModel):
    _name = "update.bsd.wizard"

    logistics_id = fields.Many2one('logistics.management')
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
    adr_line = fields.One2many("adr.line.wiz","bsd_line","ADR Line")
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

    def update_bsd(self):
        if self.logistics_id:
            # adr_lst=[]
            for loop in self.adr_line:
                if not loop.adrline_id:
                    adr_line_obj = self.env['adr.line'].create({
                    'tunnel_code_id' : loop.tunnel_code_id.id,
                    'adr_class_id':loop.adr_class_id.id,
                    'adr_pickup_type_id': loop.adr_pickup_type_id.id,
                    'hazard_type_id' :loop.hazard_type_id.id,
                    'un_code':loop.un_code.id,
                    'logistics_id':self.logistics_id.id
                    })
                else:
                    loop.adrline_id.update(
                        {
                            'tunnel_code_id' : loop.tunnel_code_id.id,
                            'adr_class_id':loop.adr_class_id.id,
                            'adr_pickup_type_id': loop.adr_pickup_type_id.id,
                            'hazard_type_id' :loop.hazard_type_id.id,
                            'un_code':loop.un_code.id,
                        }
                    )

            self.logistics_id.update({
                'number_bsd':self.number_bsd,
                'pickup_partner_id':self.pickup_partner_id.id,
                'company_id':self.company_id.id,
                'pickup_street':self.pickup_street,
                'pickup_city':self.pickup_city,
                'pickup_zip':self.pickup_zip,
                'pickup_state_id':self.pickup_state_id.id,
                'pickup_countries_id':self.pickup_countries_id.id,
                'delivery_partner_id':self.delivery_partner_id.id,
                'delivery_street':self.delivery_street,
                'delivery_zip':self.delivery_zip,
                'delivery_city':self.delivery_city,
                'delivery_state_id':self.delivery_state_id.id,
                'delivery_countries_id':self.delivery_countries_id.id,
                'partner_id':self.logistics_contact.id,
                'pretreatment_code':self.pretreatment_code,
                'waste_code':self.waste_code,
                'waste_form':self.waste_form,
                'is_adr':self.is_adr,
                'packing_type':self.packing_type,
                'container_count':self.container_count,
                'gross_weight_on_bridge':self.gross_weight_on_bridge,
                'partner_id':self.transporter.id,
                'pickup_latest_date':self.reciption_date,
                'expected_delivery':self.expected_delivery,
                'delivery_countries_id':self.r_state_id.id,
                'buy_weight_confirmed':self.buy_weight_confirmed,
                'buyer_reception_date':self.buyer_reception_date,
                'buyer_accept_lot':self.buyer_accept_lot,
                'buyer_reject_reason':self.buyer_reject_reason,
                'buyer_treatment_date':self.buyer_treatment_date,
                'buyer_treatment_code':self.buyer_treatment_code
            })

class ADRLineWiz(models.TransientModel):
    _name = "adr.line.wiz"

    un_code = fields.Many2one('un.code', string='UN Code')
    adr_class_id = fields.Many2one('adr.class', string='ADR Class')
    adr_pickup_type_id = fields.Many2one('adr.pickup.type', string='ADR Package Type')
    hazard_type_id = fields.Many2one('hazard.number', string='Hazard Number')
    tunnel_code_id = fields.Many2one('tunnel.code',string='Tunnel Code')
    logistics_id = fields.Many2one('logistics.management', string='Logistics Management Reference')

    bsd_line = fields.Many2one(comodel_name="update.bsd.wizard",string="BSD")
    adrline_id = fields.Many2one(comodel_name="adr.line")