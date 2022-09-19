from odoo import fields, models, api, _

class Meeting(models.Model):
    _inherit = 'calendar.event'
    _description = "Calendar Event"

    logistics_partner_id = fields.Many2one('res.partner','Logistics')
    logistics_pickup_partner_id = fields.Many2one('res.partner','Pickup point')
    logistics_delivery_partner_id = fields.Many2one('res.partner','Delivery Point')
    pickup_state_id = fields.Many2one('res.country.state','Pickup State')
    delivery_state_id = fields.Many2one('res.country.state','Delivery State')
    gross_weight = fields.Float('Gross Weight(Kg)')
    pickup_date_type = fields.Selection([
        ('specific', 'Specific Date'),
        ('between', 'In between'),
        ('as_soon_as_possible', 'As soon as possible')
        ],string='Pickup date type')
    pickup_date = fields.Date('Date of Pickup')
    pickup_earliest_date = fields.Date('Earliest Date')
    pickup_latest_date = fields.Date('Latest Date')
    expected_delivery = fields.Date('Expected Delivery')
    project_id = fields.Many2one('project.entries')
    main_product_id = fields.Many2one("product.template", string="Primary Type")
    sub_product_id = fields.Many2one("product.product", string="Secondary Type", domain="[('product_tmpl_id','=',main_product_id)]")
    action_type = fields.Selection([('internal', 'Internal'),
                                    ('external', 'External')], string="Action Type")
                                    # ('cross_dock','Cross Dock'),
                                    # ('dismantling', 'Dismantling'),
                                    # ('re-use', 'Re-use'),
                                    # ('sorting', 'Sorting'),
                                    # ('repack', 'Repackaging'),
                                    # ('refining', 'Refining'),
                                    # ('loose', 'Vrac')], string="Action Type")
    external_action_type = fields.Selection([('sorting', 'Sorting'),
                                             ('refining', 'Refining')], string="Client Action Type")
    supervisor_id = fields.Many2one("hr.employee", string="Supervisor", tracking=True, domain="[('is_supervisor','=', True)]")
    worker_ids = fields.Many2many('hr.employee', string="Assigned Workers", domain="[('is_worker','=', True)]")
    operator_ids = fields.Many2many("hr.employee",'hr_employee_operators_cal_rel', 'worker_id', string="Assigned Workers", tracking=True, domain="[('is_worker','=', True)]")
    status = fields.Selection([('new', 'New'), ('confirmed', 'Confirmed'),('planned','Planned'), ('in_progress', 'Production'), ('non_conformity', 'Non Conformity'), ('dangerous', 'Quarantine'), ('close', 'Closed'), ('return', 'Return')], string="Status")
    logistics_calendar = fields.Boolean('Logistics Calendar')
    production_calendar = fields.Boolean('Production Calendar')

    logistics_id = fields.Many2one('logistics.management','Transport Request')
    container_id = fields.Many2one('project.container','Container')

    updated_name = fields.Char('Name')
    name_ref = fields.Char('Ref Name',compute="_compute_name_ref")

    @api.depends('name')
    def _compute_name_ref(self):
        for loop in self:
            if loop.logistics_id:
                name_val = loop.name
                updated_name = None
                state=''
                vendor_ref = ''
                if loop.logistics_id:
                    load_status = None
                    if loop.logistics_id.is_full_load == True:
                        load_status = 'Full Load'+','
                    else:
                        load_status = str(loop.logistics_id.no_of_container)
                    if loop.logistics_id.vendor_ref:
                        vendor_ref = str(loop.logistics_id.vendor_ref)+','
                    if loop.logistics_id.pickup_state_id.name:
                        state=loop.logistics_id.pickup_state_id.name+','
                    updated_name = loop.logistics_id.name+'['+str(loop.logistics_id.partner_id.name)+','+str(vendor_ref)+load_status+state+']'
                else:
                    updated_name=loop.logistics_id.name
                loop.updated_name=loop.logistics_id.name
                loop.name = updated_name
            else:
                loop.updated_name=loop.name

            loop.name_ref=loop.name