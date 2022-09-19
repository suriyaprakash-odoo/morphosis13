from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class PickingTimingLine(models.Model):
    _name = 'picking.timing.line'

    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date', readonly=1)
    timer_duration = fields.Float(invisible=1, string='Time Duration (Minutes)')
    picking_id = fields.Many2one("stock.picking", string="Picking ID")
    user_id = fields.Many2one("res.users", string="User")
    name = fields.Char("Name")
    unit_amount = fields.Float("Unit Amount")

class ReceptionTimingLine(models.Model):
    _name = 'reception.timing.line'

    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date', readonly=1)
    timer_duration = fields.Float(invisible=1, string='Time Duration (Minutes)')
    picking_id = fields.Many2one("stock.picking", string="Picking ID")
    user_id = fields.Many2one("res.users", string="User")
    name = fields.Char("Name")
    unit_amount = fields.Float("Unit Amount")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    check_validate_button = fields.Boolean(compute="_compute_check_validate_button",default=False)
    check_move_to_reception_button = fields.Boolean(compute="_compute_check_move_to_reception_button",default=False)
    
    include_logistics = fields.Boolean('Does not Include Logistics')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('load_unload', 'Loading/Unloading'),
        ('release_lorry', 'Release Lorry'),
        ('reception', 'Recipient'),
        ('production', 'Production'),
        ('sorted_treated', 'Sorted/Treated'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Loading/Unloding: The loading/unloading of the truck is done \n"
             " * Production: Creation of containers is done \n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")

    weight_at_entry = fields.Float('Truck weight at entry(Kg)')
    entry_weight_uom_id = fields.Many2one('uom.uom', 'Weight Unit')
    weight_at_exit = fields.Float('Truck weight at exit(Kg)')
    exit_weight_uom_id = fields.Many2one('uom.uom', 'Weight Unit')
    received_containers = fields.Integer('Total No of containers arrived')
    is_container_match = fields.Boolean('Is No of containers matched?')
    container_price = fields.Float("Each Container Price", compute='_compute_each_container_price')
    entry_date_time = fields.Datetime('Truck arrival time')
    exit_date_time = fields.Datetime('Truck exit time')
    net_weight_of_shipment = fields.Float('Gross Weight(Kg)', digits=(12,4), compute='_compute_shipment_net_weight')
    net_weight_of_shipment_uom_id = fields.Many2one('uom.uom', 'Weight Unit')
    purchase_container_seal_number = fields.Char("Container Seal Number")
    purchase_truck_container_number = fields.Char("Truck Container Number")
    is_container_seal_match = fields.Boolean("Is container Seal Number matched?")
    is_truck_container_number_match = fields.Char("Is truck Container Number matched?")
    license_plate_number = fields.Char('Truck License Number')

    sale_logistics_pickup_date = fields.Date('Date of Pickup')
    sale_logistics_expected_delivery = fields.Date('Expected Delivery Date')
    sale_logistics_actual_pickup = fields.Date('Actual date of Pickup')
    sale_logistics_weight_at_entry = fields.Float('Truck weight at entry(Kg)')
    sale_logistics_weight_at_exit = fields.Float('Truck weight at exit(Kg)')
    sale_logistics_entry_date_time = fields.Datetime('Truck arrival time')
    sale_logistics_exit_date_time = fields.Datetime('Truck exit time')
    sale_logistics_no_of_container = fields.Integer('Number of Containers')
    is_sea_transport = fields.Boolean('Is Sea Tansport')
    container_seal_number = fields.Char('Container Seal Number')
    truck_licence_plate = fields.Char('Truck Number')
    truck_container_number = fields.Char("Truck Container Number")
    incoming_truck_registered = fields.Boolean('Truck Registered',default=False)
    buyer_ref = fields.Char("Buyer Reference")

    container_count = fields.Integer("Container Count", compute='_compute_containers_data')
    project_entry_id = fields.Many2one('project.entries', string='Project Entry')
    transporter_partner_id = fields.Many2one('res.partner', string='Transporter')
    transport_po_id = fields.Many2one('purchase.order', string="Transport Purchase Order")
    gross_weight = fields.Float('Gross weight(Kg)', compute='compute_gross_weight', digits=(12,4))
    overwrite_gross = fields.Boolean('Overwrite Gross weight(Kg)')
    new_gross_weight = fields.Float('Final Gross Weight(kg)', digits=(12,4))
    weight_uom_id = fields.Many2one('uom.uom', 'Weight Unit')
    pickup_date_type = fields.Selection([
        ('specific', 'Specific Date'),
        ('between', 'In between'),
        ('as_soon_as_possible', 'As soon as possible')
        ],string='Pickup date type')
    pickup_date = fields.Date('Date of Pickup')
    pickup_earliest_date = fields.Date('Earliest Date')
    pickup_latest_date = fields.Date('Latest Date')
    expected_delivery = fields.Date('Expected date of delivery')
    actual_delivery = fields.Date('Actual date of delivery')
    no_of_container = fields.Integer('Number of Containers')
    is_unloaded = fields.Boolean("Is Unloaded")

    logistics_updated = fields.Boolean('Logistics Updated')
    is_containers_created = fields.Boolean('Containers created?', compute="_compute_containers_creation", default=False)

    pickup_location_id = fields.Many2one('stock.location', string='Picking Location', 
        domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    is_internal_purchase = fields.Boolean("Is internal Purchase?")
    is_registered_package = fields.Boolean('Is Registered Package?', default=False)
    
    real_duration = fields.Float("Duration")
    task_timer = fields.Boolean(string='Timer', default=False)
    duration = fields.Float('Real Duration', compute='_compute_duration_new', store=True)
    timesheet_ids = fields.One2many("picking.timing.line", "picking_id", string="Timing Lines")
    total_time = fields.Float("Total Time(Minutes)", compute='_compute_total_duration_new')
    manual_time = fields.Float("Total Time(Minutes)")

    reception_real_duration = fields.Float("Duration")
    reception_task_timer = fields.Boolean(string='Timer', default=False)
    reception_duration = fields.Float('Real Duration', compute='_compute_duration_new', store=True)
    reception_timesheet_ids = fields.One2many("reception.timing.line", "picking_id", string="Timing Lines")
    reception_total_time = fields.Float("Total Time(Minutes)", compute='_compute_reception_total_duration_new')
    reception_manual_time = fields.Float("Total Time(Minutes)")
    
    is_user_working = fields.Boolean('Is Current User Working', compute='_compute_is_user_working_new', help="Technical field indicating whether the current user is working.")

    conteriner_image_line_ids = fields.One2many('container.image','conteriner_image_line_id', string="Contaienr Image Line ref")

    recipient_container_count = fields.Integer('Recipient Container', compute='_compute_recipient_container_count')

    vrac_container_count = fields.Integer('Vrac Container', compute='_compute_vrac_container_count')

    from_owner_id = fields.Many2one("res.partner", string="From Owner")
    to_owner_id = fields.Many2one("res.partner", string="To Owner")
    load_validated = fields.Boolean("Load Validated")

    worker_ids = fields.Many2many('hr.employee', string="Workers", domain="[('is_worker','=', True)]")
    unloading_charges = fields.Float('Unloading Charges', compute='_compute_unloading_charges')
    reception_charges = fields.Float('Reception Charges', compute='_compute_reception_charges')

    vendor_ref = fields.Char("Vendor Reference")

    project_type = fields.Selection([
        ('transfer', 'Dropship'),
        ('cross_dock', 'Cross Dock'),
        ('dismantle_sort', 'Dismantling'),
        ('reuse', 'Re-use'),
        ('sorting', 'Sorting'),
        ('refine', 'Refining'),
    ], string='Project Type',related='project_entry_id.project_type')


    check_register_truck_incoming_button = fields.Boolean(default=False, compute="_compute_check_register_truck_incoming_outgoing_button")

    check_register_truck_outgoing_button = fields.Boolean(default=False, compute="_compute_check_register_truck_incoming_outgoing_button")

    check_update_transport_detail_button = fields.Boolean(default=False, compute="_compute_check_update_transport_detail_button")

    check_release_truck_outgoing_button = fields.Boolean(default=False, compute="_compute_check_release_truck_outgoing_button")

    check_update_container_outgoing_button = fields.Boolean(default=False, compute="_compute_check_update_container_outgoing_button")


    project_container = fields.Many2one(comodel_name="project.container", string="Project Container")

    def move_to_sorted(self):
        self.state = 'sorted_treated'

    @api.depends("state","is_internal_purchase", "picking_type_code")
    def _compute_check_release_truck_outgoing_button(self):
        if self.is_internal_purchase==False and self.state=="release_lorry" and self.picking_type_code=="outgoing":
            self.check_release_truck_outgoing_button=True
        else:
            self.check_release_truck_outgoing_button=False
    
    @api.depends("state","is_internal_purchase", "picking_type_code")
    def _compute_check_update_container_outgoing_button(self):
        if self.is_internal_purchase==False and self.state in ["assigned", "load_unload"] and self.picking_type_code=="outgoing":
            self.check_update_container_outgoing_button=True
        else:
            self.check_update_container_outgoing_button=False


    @api.depends("state","is_internal_purchase")
    def _compute_check_validate_button(self):
        if self.is_internal_purchase and self.state=="assigned":
            self.check_validate_button=True
        elif self.state=="sorted_treated":
            self.check_validate_button=True
        else:
            self.check_validate_button=False
    
    @api.depends("state","is_internal_purchase","picking_type_code")
    def _compute_check_move_to_reception_button(self):
        if self.is_internal_purchase==False and self.state=="release_lorry" and self.picking_type_code == "outgoing":
            self.check_move_to_reception_button=True
        elif self.state=="release_lorry" and self.picking_type_code == "outgoing":
            self.check_move_to_reception_button=True
        else:
            self.check_move_to_reception_button=False
    

    @api.depends("state","picking_type_code","is_unloaded","logistics_updated")
    def _compute_check_register_truck_incoming_outgoing_button(self):
        if self.picking_type_code == "incoming" and self.state in ['assigned']:
            self.check_register_truck_outgoing_button = False
            if self.logistics_updated == True and self.is_unloaded == True:
                self.check_register_truck_incoming_button = True
            else:
                self.check_register_truck_incoming_button = False

        elif self.picking_type_code == "outgoing" and self.state in ['assigned']:
            self.check_register_truck_incoming_button = False
            if self.logistics_updated == True and self.is_unloaded == False:
                self.check_register_truck_outgoing_button = True
            else:
                self.check_register_truck_outgoing_button = False
        else:
            self.check_register_truck_incoming_button = False
            self.check_register_truck_outgoing_button = False
    
    @api.depends("state")
    def _compute_check_update_transport_detail_button(self):
        if self.state in ['assigned'] or self.logistics_updated == False or self.is_internal_purchase == False or self.is_registered_package == False:

            self.check_update_transport_detail_button = True
        else:
            self.check_update_transport_detail_button = False

    @api.depends('weight_at_entry','weight_at_exit','sale_logistics_weight_at_entry','sale_logistics_weight_at_exit')
    def compute_gross_weight(self):
        if self.picking_type_id.sequence_code == 'OUT':
            self.gross_weight = self.sale_logistics_weight_at_exit - self.sale_logistics_weight_at_entry
        elif self.picking_type_id.sequence_code == 'IN':
            self.gross_weight = self.weight_at_entry - self.weight_at_exit
        else:
            self.gross_weight = 0.0

    def action_truck_loaded(self):
        for i in self:
            i.state = 'release_lorry'
            i.is_unloaded = True

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
            self.vendor_ref = ref + short_code + str(self.partner_id.lot_sequence_number)

    def name_get(self):
        result = []
        for picking in self:
            if picking.partner_id:
                name = picking.name + ' [' + picking.partner_id.name + ']'
                result.append((picking.id, name))
            else:
                name = picking.name
                result.append((picking.id, name))
        return result


    @api.depends('total_time','manual_time','worker_ids')
    def _compute_unloading_charges(self):
        for shipment in self:
            if shipment.total_time == 0.0:
                real_time = shipment.manual_time
            else:
                real_time = shipment.total_time

            hr, min = divmod(real_time, 60)
            hours = float(("%02d" % (hr)))
            minutes = float(("%02d" % (min)))

            unloading_cost = ((hours) * shipment.project_entry_id.company_id.standard_unloading_rate) + (minutes * shipment.project_entry_id.company_id.standard_unloading_rate * (1.0 / 60))
            if shipment.worker_ids:
                shipment.update({
                    'unloading_charges' : unloading_cost * len(shipment.worker_ids)
                })
            else:
                shipment.update({
                        'unloading_charges' : 0.0
                    })


    @api.depends('reception_total_time','reception_manual_time')
    def _compute_reception_charges(self):
        for shipment in self:
            if shipment.reception_total_time == 0.0:
                real_time = shipment.reception_manual_time
            else:
                real_time = shipment.reception_total_time

            hr, min = divmod(real_time, 60)
            hours = float(("%02d" % (hr)))
            minutes = float(("%02d" % (min)))

            reception_cost = ((hours) * shipment.project_entry_id.company_id.standard_reception_rate) + (minutes * shipment.project_entry_id.company_id.standard_reception_rate * (1.0 / 60))
            shipment.update({
                    'reception_charges' : reception_cost
                })

    def update_picking_time(self):
        vals = ({'default_duration': self.total_time})
        return {
            'name': "Update Unloading Time",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update.picking.time',
            'target': 'new',
            'context': vals,
        }


    def update_reception_time(self):
        vals = ({'default_duration': self.reception_total_time})
        return {
            'name': "Update Recipient Time",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update.reception.time',
            'target': 'new',
            'context': vals,
        }


    @api.depends('total_time', 'manual_time')
    def _compute_time_update_new(self):
        for rec in self:
            if rec.total_time != 0.00 or rec.manual_time != 0.00:
                rec.update({
                    'is_time_updated': True
                })
            else:
                rec.update({
                    'is_time_updated': False
                })

    @api.depends('timesheet_ids.timer_duration', 'manual_time')
    def _compute_total_duration_new(self):
        for rc in self:
            total_time = 0.0
            for line in rc.timesheet_ids:
                total_time += line.timer_duration

            if rc.manual_time != 0.0:
                total_time = rc.manual_time

            rc.update({
                'total_time': total_time,
            })

    def _compute_duration_new(self):
        self

    def _compute_is_user_working_new(self):
        """ Checks whether the current user is working """
        for order in self:
            if order.timesheet_ids.filtered(lambda x: (x.user_id.id == self.env.user.id) and (not x.date_end)):
                order.is_user_working = True
            else:
                order.is_user_working = False

    @api.model
    @api.constrains('task_timer')
    def toggle_start_new(self):
        if self.task_timer is True:
            self.write({'is_user_working': True, 'manual_time': 0.0})
            time_line = self.env['picking.timing.line']
            for time_sheet in self:
                time_line.create({
                    'name': self.env.user.name + ': ' + time_sheet.name,
                    'picking_id': time_sheet.id,
                    'user_id': self.env.user.id,
                    # 'container_id': time_sheet.container_id.id,
                    'date_start': datetime.now(),
                })
        else:
            self.write({'is_user_working': False})
            time_line_obj = self.env['picking.timing.line']
            domain = [('picking_id', 'in', self.ids), ('date_end', '=', False)]
            for time_line in time_line_obj.search(domain):
                time_line.write({'date_end': fields.Datetime.now()})
                if time_line.date_end:
                    diff = fields.Datetime.from_string(time_line.date_end) - fields.Datetime.from_string(time_line.date_start)
                    time_line.timer_duration = round(diff.total_seconds() / 60.0, 2)
                    time_line.unit_amount = round(diff.total_seconds() / (60.0 * 60.0), 2)
                else:
                    time_line.unit_amount = 0.0
                    time_line.timer_duration = 0.0

    def start_loading_timer(self):
        self.task_timer = True


    @api.depends('reception_total_time', 'reception_manual_time')
    def _compute_reception_time_update_new(self):
        for rec in self:
            if rec.reception_total_time != 0.00 or rec.reception_manual_time != 0.00:
                rec.update({
                    'is_time_updated': True
                })
            else:
                rec.update({
                    'is_time_updated': False
                })

    @api.depends('reception_timesheet_ids.timer_duration', 'reception_manual_time')
    def _compute_reception_total_duration_new(self):
        for rc in self:
            total_time = 0.0
            for line in rc.reception_timesheet_ids:
                total_time += line.timer_duration

            if rc.reception_manual_time != 0.0:
                total_time = rc.reception_manual_time

            rc.update({
                'reception_total_time': total_time,
            })

    def _compute_reception_duration_new(self):
        self

    @api.model
    @api.constrains('reception_task_timer')
    def reception_toggle_start_new(self):
        if self.reception_task_timer is True:
            self.write({'is_user_working': True, 'reception_manual_time': 0.0})
            time_line = self.env['reception.timing.line']
            for time_sheet in self:
                time_line.create({
                    'name': self.env.user.name + ': ' + time_sheet.name,
                    'picking_id': time_sheet.id,
                    'user_id': self.env.user.id,
                    # 'container_id': time_sheet.container_id.id,
                    'date_start': datetime.now(),
                })
        else:
            self.write({'is_user_working': False})
            time_line_obj = self.env['reception.timing.line']
            domain = [('picking_id', 'in', self.ids), ('date_end', '=', False)]
            for time_line in time_line_obj.search(domain):
                time_line.write({'date_end': fields.Datetime.now()})
                if time_line.date_end:
                    diff = fields.Datetime.from_string(time_line.date_end) - fields.Datetime.from_string(time_line.date_start)
                    time_line.timer_duration = round(diff.total_seconds() / 60.0, 2)
                    time_line.unit_amount = round(diff.total_seconds() / (60.0 * 60.0), 2)
                else:
                    time_line.unit_amount = 0.0
                    time_line.timer_duration = 0.0

    def start_reception_timer(self):
        self.reception_task_timer = True


    def _compute_containers_creation(self):
        containers_obj = self.env['project.container'].search([('picking_id' , '=' , self.id),('project_id' , '=' , self.project_entry_id.id)])
        if containers_obj:
            self.is_containers_created = True
        else:
            self.is_containers_created = False

    def action_view_recipient_containers(self):
        picking_obj = self.env['stock.picking'].browse(self[0].id)
        return {
            'name': _('Recipient Containers'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.container',
            'domain': [('picking_id', '=', picking_obj.id),('project_id', '=', picking_obj.project_entry_id.id)],
            'views_id': False,
            'views': [(self.env.ref('ppts_inventory_customization.stock_container_tree_view').id or False, 'tree'),
                      (self.env.ref('ppts_inventory_customization.stock_container_form_view').id or False, 'form')],
        }
    
    def action_view_vrac_containers(self):
        fraction_obj = self.env['project.fraction'].sudo().search([('project_id','=',self.project_entry_id.id),('is_vrac','=',True)])
        container_ids = []
        for fraction in fraction_obj:
            container_ids.append(fraction.recipient_container_id.id)
        container_ids = list(set(container_ids))
        return {
            'name': _('Vrac Containers'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.container',
            'domain': [('id','in',container_ids)],
            'res_id': container_ids if container_ids else False,
            'views_id': False,
            'views': [(self.env.ref('ppts_inventory_customization.stock_container_tree_view').id or False, 'tree'),
                      (self.env.ref('ppts_inventory_customization.stock_container_form_view').id or False, 'form')],
        }

    def action_create_containers(self):
        action = self.env.ref('ppts_inventory_customization.action_create_containers').read()[0]

        action['context'] = {
            'default_project_id': self.project_entry_id.id or False,
            'search_default_picking_id': self.id,
            'default_picking_id': self.id,
            # 'default_gross_weight': self.gross_weight,
            # 'default_gross_uom_id': self.weight_uom_id.id,
            # 'default_sales_team_id': self.user_id.id,
            # 'default_medium_id': self.medium_id.id,
            'search_default_cnt_type': True
        }
        action['domain'] = [('picking_id', '=', self.id)]
        containers = self.env['project.container'].search([('picking_id', '=', self.id)])
        if len(containers) == 1:
            action['views'] = [(self.env.ref('ppts_inventory_customization.project_container_form_view').id, 'form')]
            action['res_id'] = containers.id
        return action

    def truck_notification(self):
        if self.picking_type_id.sequence_code == 'IN':
            template_id = self.env.ref('ppts_inventory_customization.email_template_incoming_shipment').id
            mail_template = self.env['mail.template'].browse(template_id)

            if mail_template:
                mail_template.send_mail(self.id, force_send=True)

        if self.picking_type_id.sequence_code == 'OUT':
            template_id = self.env.ref('ppts_inventory_customization.email_template_outgoing_shipment').id
            mail_template = self.env['mail.template'].browse(template_id)

            if mail_template:
                mail_template.send_mail(self.id, force_send=True)

    def load_unload_notification(self):
        if self.picking_type_id.sequence_code == 'IN':
            template_id = self.env.ref('ppts_inventory_customization.email_template_truck_unloaded_notification').id
            mail_template = self.env['mail.template'].browse(template_id)

            if mail_template:
                mail_template.send_mail(self.id, force_send=True)

        if self.picking_type_id.sequence_code == 'OUT':
            template_id = self.env.ref('ppts_inventory_customization.email_template_truck_loaded_notification').id
            mail_template = self.env['mail.template'].browse(template_id)

            if mail_template:
                mail_template.send_mail(self.id, force_send=True)

    def _compute_recipient_container_count(self):
        for picking in self:
            rc_obj = self.env['stock.container'].search([('project_id', '=', picking.project_entry_id.id),('picking_id', '=', picking.id)])
            if rc_obj:
                picking.update({
                        'recipient_container_count' : len(rc_obj)
                    })
            else:
                picking.update({
                        'recipient_container_count' : 0
                    })
    
    def _compute_vrac_container_count(self):
        for picking in self:
            fraction_obj = self.env['project.fraction'].sudo().search([('project_id','=',picking.project_entry_id.id),('is_vrac','=',True)])
            container_ids = []
            for fraction in fraction_obj:
                container_ids.append(fraction.recipient_container_id.id)
            container_ids = list(set(container_ids))

            picking.vrac_container_count = len(container_ids)


    def _compute_containers_data(self):
        for picking in self:
            container_count = 0
            containers = self.env['project.container'].search([('picking_id', '=', picking.id)])
            if containers:
                container_count = len(containers)
            picking.container_count = container_count

    def _compute_shipment_net_weight(self):
        for picking in self:
            if picking.weight_at_entry != 0.00 and picking.weight_at_exit != 0.00:
                picking.net_weight_of_shipment = picking.weight_at_entry - picking.weight_at_exit
            else:
                picking.net_weight_of_shipment = 0.00

    def _compute_each_container_price(self):
        for picking in self:
            if picking.project_entry_id and picking.received_containers:
                if picking.project_entry_id.origin.amount_total != 0.0:
                    purchase_price = picking.project_entry_id.origin.amount_total
                    single_container_price = purchase_price / picking.received_containers
                    picking.update({
                        'container_price': single_container_price,
                    })
                else:
                    picking.update({
                        'container_price': 0.0
                    })
            else:
                picking.update({
                    'container_price': 0.0
                })

    def action_send_container_mismatch(self):
        '''
        This function opens a window to compose an email, with the edit send mismatch intimation template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('ppts_inventory_customization', 'email_template_container_mismatched')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})

        ctx.update({
            'default_model': 'stock.picking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'model_description': 'Mismatch of received containers',
            'mark_so_as_sent': True
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

    def button_unload(self):
        self.state = 'unload'

    def move_to_reception(self):
        
        def date_by_adding_business_days(from_date, add_days):
            business_days_to_add = add_days
            current_date = from_date
            while business_days_to_add > 0:
                current_date += timedelta(days=1)
                weekday = current_date.weekday()
                if weekday >= 5: # sunday = 6
                    continue
                business_days_to_add -= 1
            return current_date

        fifteen_days_date = date_by_adding_business_days(datetime.now().date(), 15)

        self.project_entry_id.fifteen_days_date = fifteen_days_date
        self.project_entry_id.status = 'reception'

        logistics_obj = self.env['logistics.management'].search([('origin' , '=' , self.project_entry_id.id),('status' , '=' , 'approved')], limit=1)
        if logistics_obj:
            logistics_obj.status = 'delivered'
            
        self.state = 'reception'

    def go_to_reception(self):
        self.state = 'reception'

    def move_to_production(self):
        fraction_obj = self.env['project.fraction'].search([('project_id', '=', self.project_entry_id.id),('is_vrac', '=', True)])
        if self.project_entry_id and not self.is_containers_created and not self.is_internal_purchase and not self.sub_contract and self.recipient_container_count == 0:
            if not fraction_obj:
                raise UserError('Please make sure the containers are created against this shipment')
        else:
            self.state = 'production'

    def button_finish(self):
        fraction_obj = self.env['project.fraction'].search([('project_id', '=', self.project_entry_id.id),('is_vrac', '=', True)])
        if self.project_entry_id and not self.is_containers_created and not self.is_internal_purchase and not self.sub_contract and self.recipient_container_count == 0:
            if not fraction_obj:
                raise UserError('Please make sure the containers are created against this shipment')
        if self.container_count >= 1:
            containers = self.env["project.container"].search([('picking_id', '=', self.id)])
            not_closed_container_count = 0
            for container in containers:
                if container.state != 'close':
                    not_closed_container_count = not_closed_container_count + 1
                if not_closed_container_count != 0:
                    raise UserError(_('Please make sure the container "%s" is closed.') % container.name)
                else:
                    self.state = 'sorted_treated'
        else:
            self.state = 'sorted_treated'


    def action_done(self):
        # OVERRIDE
        res = super(StockPicking, self).action_done()
        sale_order_obj = self.env['sale.order'].sudo().search([('name','=',self.origin)],limit=1)
        self.task_timer = False
        if self.picking_type_id.code == 'internal':
            if self.to_owner_id:
                move_line = self.env["stock.move.line"].search([('picking_id', '=', self.id)])
                for mv in move_line:
                    quant = self.env["stock.quant"].search([('lot_id', '=', mv.lot_id.id)])
                    if quant:
                        quant.sudo().write({'owner_id' : self.to_owner_id.id})

        if self.picking_type_id.sequence_code == 'IN':
            fraction_obj = self.env['project.fraction'].search([('project_id', '=', self.project_entry_id.id),('is_vrac', '=', True)])
            if self.project_entry_id and not self.is_containers_created and not self.is_internal_purchase and not self.sub_contract and self.recipient_container_count == 0:
                if not fraction_obj:
                    raise UserError('Please make sure the containers are created against this shipment')
            if self.container_count >= 1:
                containers = self.env["project.container"].search([('picking_id', '=', self.id)])
                not_closed_container_count = 0
                for container in containers:
                    if container.state != 'close':
                        not_closed_container_count = not_closed_container_count + 1
                    if not_closed_container_count != 0:
                        raise UserError(_('Please make sure the container "%s" is closed.') % container.name)
                    else:
                        self.project_entry_id.status = 'srt'
                        self.project_entry_id.origin.is_sorted = True
            else:
                self.project_entry_id.status = 'srt'        
                self.project_entry_id.origin.is_sorted = True

        if self.picking_type_id.sequence_code == 'OUT':
            sale_obj = self.env['sale.order'].search([('name', '=', self.origin)])
            sale_obj.shipment_validated = True
            for line in self.move_ids_without_package:
                if line.container_ids:
                    for rec in line.container_ids:
                        for line_fraction in rec.fraction_line_ids:
                            if line_fraction.is_to_sell == True and line_fraction.sale_order_id.id == sale_obj.id and line_fraction.weight == 0.0:
                                line_fraction.unlink()
                        for container_line in line.product_id.container_product_ids:
                            if not container_line.container_id.is_scrap_container == True:
                                if container_line.container_id == rec:
                                    if sale_order_obj.is_contrack_work:
                                        container_line.container_id.sudo().state = "taf"
                                    else:
                                        pass
                            elif container_line.container_id.is_vrac == True:
                                pass
                            elif container_line.container_id.is_scrap_container == True:
                                container_line.container_id.state = 'done'
                                    # container_line.container_id.active = False
                                container_line.unlink()
                            else:
                                for fraction_line in container_line.container_id.fraction_line_ids:
                                    if fraction_line.is_to_sell == True and fraction_line.sale_order_id == sale_obj.id:
                                        fraction_line.unlink()

        return res


class ContainerImages(models.Model):
    _name = 'container.image'

    conteriner_image = fields.Binary('Container Image')
    conteriner_image_line_id = fields.Many2one('stock.picking', string="Stock Picking Ref")