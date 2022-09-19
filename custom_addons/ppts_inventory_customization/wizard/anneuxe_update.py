from odoo import api, fields, models, _


class UpdateAnnexe(models.TransientModel):
    _name = "update.annexe.wizard"

    number_bsd = fields.Char(string="Numéro du bordereau de rattachement")
    company_id = fields.Many2one('res.company',string='Company')
    pickup_street = fields.Char()
    pickup_street2 = fields.Char()
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

    delivery_partner_id = fields.Many2one('res.partner',string='Destination Company')
    delivery_street = fields.Char()
    delivery_street2 = fields.Char()
    delivery_zip = fields.Char(change_default=True)
    delivery_city = fields.Char()
    delivery_phone = fields.Char("Tél")
    delivery_email = fields.Char("Mél")
    logistics_id = fields.Many2one('logistics.management')

    gross_weight_on_bridge = fields.Float('Gross weight on Bridge(Kg)')

    expected_delivery = fields.Date('Expected date of delivery')
    # first
    transporter1 = fields.Many2one('res.partner',string="Transporter Name")
    transporter1_street = fields.Char()
    transporter1_street2 = fields.Char()
    transporter1_zip = fields.Char(change_default=True)
    transporter1_city = fields.Char()
    transporter1_phone = fields.Char("Tél")
    transporter1_email = fields.Char("Mél")
    transport1_contact = fields.Many2one('res.partner',string="Transporter Contact")
    scheduled_date = fields.Date("Declaration")

    # second
    transporter2 = fields.Many2one('res.partner',string="Transporter Name2")
    transporter2_street = fields.Char()
    transporter2_street2 = fields.Char()
    transporter2_zip = fields.Char(change_default=True)
    transporter2_city = fields.Char()
    transporter2_phone = fields.Char("Tél")
    transporter2_email = fields.Char("Mél")
    transport2_contact = fields.Many2one('res.partner',string="Transporter Contact")
    second_carrier = fields.Date("Date of Transfer")

    # third
    transporter3 = fields.Many2one('res.partner',string="Transporter Name3")
    transporter3_street = fields.Char()
    transporter3_street2 = fields.Char()
    transporter3_zip = fields.Char(change_default=True)
    transporter3_city = fields.Char()
    transporter3_phone = fields.Char("Tél")
    transporter3_email = fields.Char("Mél")
    transport3_contact = fields.Many2one('res.partner',string="Transporter contact")
    third_carrier = fields.Date("Date of Transfer")

    client = fields.Many2one('res.partner',string="Client Name")
    client_street = fields.Char()
    client_street2 = fields.Char()
    client_zip = fields.Char(change_default=True)
    client_city = fields.Char()
    client_phone = fields.Char("Tél")
    client_email = fields.Char("Mél")
    client_contact = fields.Many2one('res.partner',string="Contact")

    contractor = fields.Many2one('res.partner',string="Contractor Name")
    contractor_street = fields.Char()
    contractor_street2 = fields.Char()
    contractor_zip = fields.Char(change_default=True)
    contractor_city = fields.Char()
    contractor_phone = fields.Char("Tél")
    contractor_email = fields.Char("Mél")
    contractor_contact = fields.Many2one('res.partner',string="Contact")

    buyer_treatment_code = fields.Selection([
        ('d9' , 'D9'),
        ('r4' , 'R4'),
        ('r5' , 'R5'),
        ('r8' , 'R8'),
    ],string="Recovery Operation")
    material_type = fields.Text('Usual Description of the waste')
    waste_code = fields.Char('Waste Identification Code')

    despatch_country = fields.Many2one('res.country',string="Export/dispatch")
    transit_country_1 = fields.Many2one('res.country',string="Transit country 1")
    transit_country_2 = fields.Many2one('res.country',string="Transit country 2")
    transit_country_3 = fields.Many2one('res.country',string="Transit country 3")
    destination_country = fields.Many2one('res.country',string="Import Destination")
    declaration_date = fields.Date("Declaration")
    reception_date = fields.Date("Date of reception")
    confirmed_quantity = fields.Float("Confirmed Quantity")
    is_transporter2 = fields.Boolean("Include Transporter2")
    is_transporter3 = fields.Boolean("Include Transporter3")

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.pickup_street = self.company_id.street
            self.pickup_street2 = self.company_id.street2
            self.pickup_zip = self.company_id.zip
            self.pickup_city = self.company_id.city
            self.pickup_state_id = self.company_id.state_id.id
            self.pickup_countries_id = self.company_id.country_id.id
            self.phone = self.company_id.phone
            self.email = self.company_id.email

    @api.onchange('delivery_partner_id')
    def onchange_delivery_partner_id(self):
        if self.delivery_partner_id:
            self.delivery_street = self.delivery_partner_id.street
            self.delivery_street2 = self.delivery_partner_id.street2
            self.delivery_zip = self.delivery_partner_id.zip
            self.delivery_city = self.delivery_partner_id.city
            self.delivery_phone = self.delivery_partner_id.phone
            self.delivery_email = self.delivery_partner_id.email

    @api.onchange('transporter1')
    def onchange_transporter1(self):
        if self.transporter1:
            self.transporter1_street = self.transporter1.street
            self.transporter1_street2 = self.transporter1.street2
            self.transporter1_zip = self.transporter1.zip
            self.transporter1_city = self.transporter1.city
            self.transporter1_phone = self.transporter1.phone
            self.transporter1_email = self.transporter1.email
            self.transporter1_contact = self.transporter1.id

    @api.onchange('transporter2')
    def onchange_transporter2(self):
        if self.transporter2:
            self.transporter2_street = self.transporter2.street
            self.transporter2_street2 = self.transporter2.street2
            self.transporter2_zip = self.transporter2.zip
            self.transporter2_city = self.transporter2.city
            self.transporter2_phone = self.transporter2.phone
            self.transporter2_email = self.transporter2.email
            self.transporter2_contact = self.transporter2.id

    @api.onchange('transporter3')
    def onchange_transporter3(self):
        if self.transporter3:
            self.transporter3_street = self.transporter3.street
            self.transporter3_street2 = self.transporter3.street2
            self.transporter3_zip = self.transporter3.zip
            self.transporter3_city = self.transporter3.city
            self.transporter3_phone = self.transporter3.phone
            self.transporter3_email = self.transporter3.email
            self.transporter3_contact = self.transporter3.id

    @api.onchange('client')
    def onchange_client(self):
        if self.client:
            self.client_street = self.client.street
            self.client_street2 = self.client.street2
            self.client_zip = self.client.zip
            self.client_city = self.client.city
            self.client_phone = self.client.phone
            self.client_email = self.client.email
            self.client_contact = self.client.id

    @api.onchange('contractor')
    def onchange_contractor(self):
        if self.contractor:
            self.contractor_street = self.contractor.street
            self.contractor_street2 = self.contractor.street2
            self.contractor_zip = self.contractor.zip
            self.contractor_city = self.contractor.city
            self.contractor_phone = self.contractor.phone
            self.contractor_email = self.contractor.email
            self.contractor_contact = self.contractor.id

    def update_annexe(self):
        if self.logistics_id:
            self.logistics_id.update({
                'number_bsd':self.number_bsd,
                'company_id':self.company_id.id,
                'pickup_street':self.company_id.street,
                'pickup_city':self.company_id.city,
                'pickup_zip':self.company_id.zip,
                'pickup_state_id':self.company_id.state_id.id,
                'pickup_countries_id':self.company_id.country_id.id,
                'delivery_partner_id':self.delivery_partner_id.id,
                'delivery_street':self.delivery_street,
                'delivery_zip':self.delivery_zip,
                'delivery_city':self.delivery_city,
                'gross_weight_on_bridge':self.gross_weight_on_bridge,
                'expected_delivery':self.expected_delivery,
                'expected_delivery':self.scheduled_date,
                'is_transporter2':self.is_transporter2,
                'transporter2':self.transporter2.id,
                'transporter2_street':self.transporter2_street,
                'transporter2_zip':self.transporter2_zip,
                'transporter2_city':self.transporter2_city,
                'transporter2_phone':self.transporter2_phone,
                'transporter2_email':self.transporter2_email,
                'transporter2_contact':self.transport2_contact.id,
                'second_carrier':self.second_carrier,
                'is_transporter3':self.is_transporter3,
                'transporter3':self.transporter3.id,
                'transporter3_street':self.transporter3_street,
                'transporter3_zip':self.transporter3_zip,
                'transporter3_city':self.transporter3_city,
                'transporter3_phone':self.transporter3_phone,
                'transporter3_email':self.transporter3_email,
                'transporter3_contact':self.transport3_contact.id,
                'third_carrier':self.third_carrier,
                'buyer_treatment_code':self.buyer_treatment_code,
                'material':self.material_type,
                'waste_code':self.waste_code,
                'despatch_country':self.despatch_country.id,
                'transit_country_1':self.transit_country_1.id,
                'transit_country_2':self.transit_country_2.id,
                'transit_country_3':self.transit_country_3.id,
                'destination_country': self.destination_country,
                'declaration_date':self.declaration_date,
                'reception_date':self.reception_date,
                'confirmed_quantity':self.confirmed_quantity,
          })