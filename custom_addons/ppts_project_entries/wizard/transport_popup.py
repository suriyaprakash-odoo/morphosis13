from odoo import fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError

class TransportPopup(models.TransientModel):
    _name = 'transport.popup'
    _description = 'Transport Popup'

    pickup_partner_id = fields.Many2one('res.partner',string="Pickup Point")

    collection_date_type = fields.Selection([
        ('specific', 'Specific Date'),
        ('between', 'In between'),
        ('as_soon_as_possible', 'As soon as possible')
    ], string='Pickup Date Type')

    gross_weight = fields.Float("Gross Weight")
    waste_code = fields.Char("Waste Code")
    material = fields.Char("Material")
    container_count = fields.Integer("Container Count")
    dimension = fields.Char("Dimension")

    lorry_type = fields.Selection([
        ('container', 'container'),
        ('curtainside', 'Curtain-side'),
        ('semi_trailer', 'Semi-Trailer'),
        ('rigid_body_truck', 'Rigid Body Truck'),
        ('moving_floor', 'Moving Floor')
    ], string='Type of Lorry')

    pickup_date = fields.Date("Pickup Date")
    pickup_earliest_date = fields.Date("Earliest Date")
    pickup_latest_date = fields.Date('Latest Date')

    is_full_load = fields.Boolean('Full Load?')
    is_tail_lift = fields.Boolean('Tail-Lift')
    hayons = fields.Selection([('hayons', 'Hayons'), ('hayons_t', 'Hayons + transpalette'),
                               ('hayons_te', 'Hayons + transpalette electrique')])

    note = fields.Text("Note")

    # grid_rotation = fields.Char('rotation de grille')

    def send_transport_notificaton(self):
        project_id = self.env["project.entries"].browse(self.env.context.get('active_id'))

        for rec in project_id:
            carton_line_list = [(0, 0, {
                'name': record.name,
                'cost': record.cost
            }) for record in rec.carton_ids]

        containers = []
        transport_type = ''
        if project_id.send_containers:
            transport_type = 'drop_off'
            if project_id.project_container_ids:
                for ct in project_id.project_container_ids:
                    containers.append((0, 0, {
                        'product_id': ct.product_id.id,
                        'quantity': ct.quantity,
                    }))
            else:
                raise UserError('Please add some containers to send')

        if self.container_count:
            count_type = 'specified'
        else:
            count_type = 'not_specified'

        vals = {
            'pickup_partner_id': self.pickup_partner_id.id,
            'delivery_partner_id': project_id.company_id.partner_id.id,
            'pickup_country_id': project_id.partner_id.state_id.id,
            'delivery_country_id': project_id.company_id.partner_id.state_id.id,
            'company_id': project_id.company_id.id,
            'origin': project_id.id,
            'container_count': count_type,

            'lorry_type': self.lorry_type,
            'is_tail_lift': project_id.is_tail_lift,
            'morning_opening_hours_start': project_id.morning_opening_hours_start,
            'morning_opening_hours_end': project_id.morning_opening_hours_end,
            'evening_opening_hours_start': project_id.evening_opening_hours_start,
            'evening_opening_hours_end': project_id.evening_opening_hours_end,
            'pickup_date_type': self.collection_date_type,
            'pickup_date': self.pickup_date,
            'is_full_load': project_id.is_full_load,
            'gross_weight': self.gross_weight,
            'carton_ids': carton_line_list,
            'pickup_street': project_id.partner_id.street,
            'pickup_street2': project_id.partner_id.street2,
            'pickup_zip': project_id.partner_id.zip,
            'pickup_state_id': project_id.partner_id.state_id.id,
            'pickup_countries_id': project_id.partner_id.country_id.id,
            'delivery_street': project_id.company_id.partner_id.street,
            'delivery_street2': project_id.company_id.partner_id.street2,
            'delivery_zip': project_id.company_id.partner_id.zip,
            'delivery_state_id': project_id.company_id.partner_id.state_id.id,
            'delivery_countries_id': project_id.company_id.partner_id.country_id.id,
            'logistics_for': 'purchase',
            'status': 'new',
            'send_containers': project_id.send_containers,
            'container_line_ids': containers,
            'transport_type': transport_type,

            'pickup_earliest_date': self.pickup_earliest_date,
            'pickup_latest_date': self.pickup_latest_date,
            'waste_code':self.waste_code,
            'material':self.material,
            'dimension':self.dimension,
            'no_of_container': self.container_count,
            'hayons': self.hayons,
            'grid_rotation': project_id.partner_id.grid_rotation,
        }

        self.env["logistics.management"].create(vals)

        template = self.env.ref('ppts_project_entries.email_template_send_notification')

        ctx = {
                'pickup_partner_id':self.pickup_partner_id.name if self.pickup_partner_id else '',
                'project': project_id.name,
                'pickup_type': dict(self._fields['collection_date_type'].selection).get(self.collection_date_type),
                'gross_weight':self.gross_weight,
                'partner': project_id.partner_id.name,
                'company': project_id.company_id.name,
                'waste_code': self.waste_code or '',
                'material':self.material,
                'container_count': self.container_count,
                'dimension':self.dimension or '',
                'type_lorry': dict(self._fields['lorry_type'].selection).get(self.lorry_type),
                'pickup_date': self.pickup_date,
                'note':self.note or ''
            }

        template.with_context(ctx).sudo().send_mail(project_id.id, force_send=True)
        
        project_id.origin.button_confirm()


        # try:
        #     compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        # except ValueError:
        #     compose_form_id = False
        # ctx = dict(self.env.context or {})
        #
        # ctx.update({
        #     'default_model': 'project.entries',
        #     'active_model': 'project.entries',
        #     'active_id': self.env.context.get('active_id'),
        #     'default_res_id': self.env.context.get('active_id'),
        #     'default_use_template': bool(template_id),
        #     'default_template_id': template_id,
        #     'default_composition_mode': 'comment',
        #     'custom_layout': "mail.mail_notification_paynow",
        #     'default_attachment_ids': [],
        #     'model_description': 'Allocate Logistics',
        #     'force_email': True,
        #     'mark_allocate_logistics_as_sent': True
        # })
        #
        # return {
        #     'name': 'Compose Email',
        #     'type': 'ir.actions.act_window',
        #     'view_mode': 'form',
        #     'res_model': 'mail.compose.message',
        #     'views': [(compose_form_id, 'form')],
        #     'view_id': compose_form_id,
        #     'target': 'new',
        #     'context': ctx,
        # }
