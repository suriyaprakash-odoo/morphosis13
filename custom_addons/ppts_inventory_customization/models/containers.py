from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ContainerType(models.Model):
    _name = 'container.type'
    _description = 'Project Container Type'

    name = fields.Char("Container Type")
    tare_weight = fields.Float("Tare Weight(Kg)")
    capacity_weight = fields.Float("Capacity(Kg)")
    container_dimentions = fields.Char("Dimentions")
    container_length = fields.Integer('Container Length')
    container_width = fields.Integer('Container Width')
    container_height = fields.Integer('Container Height')
    reusable_container = fields.Boolean("Reusable Container?")
    product_id = fields.Many2one("product.product", string="Related Product")

    is_multi_product = fields.Boolean('Is Multi-Product')
    primary_content_type_id = fields.Many2one('product.template', string="Primary Product")
    secondary_content_type_id = fields.Many2many('product.product', string="Secondary Product",
                                                 domain="[('product_tmpl_id','=',primary_content_type_id)]")
    stock_volume = fields.Float("Stock Volume", compute='_compute_stock_volume')

    def _compute_stock_volume(self):
        for rec in self:
            stock_volume = 0.0
            donors = self.env['project.container'].search(
                [('container_type_id', '=', rec.id), ('state', '!=', 'close')])
            for dc in donors:
                stock_volume += dc.net_gross_weight

            recipients = self.env['stock.container'].search(
                [('container_type_id', '=', rec.id), ('state', 'not in', ('sold', 'done'))])
            for rc in recipients:
                stock_volume += rc.net_weight

            rec.update({
                'stock_volume': stock_volume
            })


class ActionTimingLine(models.Model):
    _name = 'action.timing.line'

    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date', readonly=1)
    timer_duration = fields.Float(invisible=1, string='Time Duration (Minutes)')
    container_id = fields.Many2one("project.container", string="Container ID")
    user_id = fields.Many2one("res.users", string="User")
    name = fields.Char("Name")
    unit_amount = fields.Float("Unit Amount")


class ProjectContainer(models.Model):
    _name = 'project.container'
    _description = 'Project Containers'
    _inherit = ['mail.thread']

    name = fields.Char("Sequence ID")
    partner_ref = fields.Char('Vendor Reference')
    project_id = fields.Many2one("project.entries", string="Project ID",
                                 domain="[('status','in', ('reception','wip'))]")
    project_entry_line_id = fields.Many2one('project.entries.line', string="Project Entry Line ID",
                                            domain="[('project_entry_id','=',project_id)]")
    picking_id = fields.Many2one("stock.picking", string="Shipment ID",
                                 domain="[('project_entry_id','=', project_id),('project_entry_id','!=', False)]",
                                 tracking=True)
    container_type_id = fields.Many2one("container.type", string="Container Type", required=1, tracking=True)
    gross_weight = fields.Float("Gross Weight(Kg)", digits=(12, 4), tracking=True)
    # gross_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    net_weight = fields.Float("Fraction Net Weight(Kg)", digits=(12, 4), compute='_compute_fractions_weight',
                              tracking=True)
    quantity = fields.Integer("Count")
    # net_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    content_type = fields.Many2one("waste.type", string="Type of Waste", tracking=True)
    confirmation = fields.Selection([('confirmed', 'Conformed'), ('non_conformity', 'Non Conformity')],
                                    string="Quality", required=1, tracking=True)
    fraction_count = fields.Integer("Fraction Count", compute='_compute_fraction_data')
    state = fields.Selection(
        [('new', 'New'), ('confirmed', 'Confirmed'), ('planned', 'Planned'), ('in_progress', 'Production'),
         ('non_conformity', 'Non Conformity'), ('dangerous', 'Quarantine'), ('close', 'Closed'), ('return', 'Return'),('cancel', 'Cancelled')],
        string="Status",
        default='new', tracking=True)
    action_date = fields.Date("Action Date", tracking=True)
    action_date_end = fields.Date("Action End Date", tracking=True)
    action_type = fields.Selection([('internal', 'Internal'),
                                    ('external', 'External')], string="Action Type")

    external_action_type = fields.Selection([('sorting', 'Sorting'),
                                             ('refining', 'Refining'),
                                             ('test', 'Test')], string="Client Action Type")

    second_process_action_type = fields.Selection([('grinding', 'Grinding'),
                                                   ('dismantling', 'Dismantling'),
                                                   ('repackaging', 'Repackaging'),
                                                   ('sorting', 'Sorting'),
                                                   ('sorting_vrac', 'Vrac'),
                                                   ('vrac', 'RC Vrac'),
                                                   ('test', 'Test')], string="Second Process Action")
    intended_action = fields.Selection([('vrac', 'Vrac'),
                                        ('development', 'Développeur'),
                                        ('engineering', 'Ingénierie'),
                                        ('qhse', 'QHSE')], string="Action Prévue")

    worker_ids = fields.Many2many('hr.employee', string="Assigned Workers", domain="[('is_worker','=', True)]")
    timesheet_ids = fields.One2many("action.timing.line", "container_id", string="Timing Lines")
    task_timer = fields.Boolean(string='Timer', default=False)
    is_user_working = fields.Boolean('Is Current User Working', compute='_compute_is_user_working',
                                     help="Technical field indicating whether the current user is working.")
    duration = fields.Float('Real Duration', compute='_compute_duration', store=True)
    contractor_rate = fields.Boolean("Contractor Rate")
    ea_rate = fields.Boolean("EA Rate")
    standard_rate = fields.Boolean("Standard Rate")
    total_time = fields.Float("Total Time(Minutes)", compute='_compute_total_duration')
    operator_ids = fields.Many2many("hr.employee", 'hr_employee_operators_rel', 'worker_id', string="Operator",
                                    tracking=True, domain="[('is_worker','=', True)]")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    container_cost = fields.Monetary('Container Cost', currency_field='currency_id', compute='_compute_container_price')
    actual_container_cost = fields.Monetary('Actual Container Cost', currency_field='currency_id',
                                            compute='_compute_actual_container_price')
    main_product_id = fields.Many2one("product.template", string="Primary Type", tracking=True)
    sub_product_id = fields.Many2one("product.product", string="Secondary Type",
                                     domain="[('product_tmpl_id','=',main_product_id)]", tracking=True)
    is_child_container = fields.Boolean("Is Child Container")
    parent_container_id = fields.Many2one("project.container", string="Parent Container",
                                          domain="[('picking_id', '=', picking_id),('main_product_id','=',main_product_id),('is_child_container' , '!=' , True)]")
    child_container_ids = fields.Many2many("project.container", 'project_container_rel', 'project_container_id',
                                           'pc_id', string="Child Container",
                                           domain="[('picking_id', '=', picking_id),('main_product_id','=',main_product_id),('is_child_container' , '=' , True)]")
    child_count = fields.Integer("child count", compute='_compute_container_count', )
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    location_id = fields.Many2one("stock.location", string="Location",
                                  domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                  check_company=True)
    non_conformity_type = fields.Selection(
        [('dangerous', 'Dangerous Material'), ('content_mismatch', 'Content Mismatch'),
         ('quantity', 'Incorrect Quantity')], string="Non Conformity Type", tracking=True)
    reconfirmed = fields.Boolean("Reconfirmed?")
    penalty_amount = fields.Float("Penalty Amount")
    return_shipment_id = fields.Many2one("stock.picking", string="RETURN ORDER")
    net_gross_weight = fields.Float("Net Weight(Kg)", digits=(12, 4), compute='_compute_net_gross_weight')
    manual_time = fields.Float("Total Time(Minutes)")
    supervisor_id = fields.Many2one("hr.employee", string="Supervisor", tracking=True,
                                    domain="[('is_supervisor','=', True)]")
    returnable_container = fields.Boolean("Returnable Container")
    fr_count = fields.Integer("FR count")
    extra_tare = fields.Float("Absolute Tare Weight(Kg)")
    partner_id = fields.Many2one("res.partner", string="Client Name")
    notes = fields.Text("Notes")
    fifteen_day_notice = fields.Boolean(related='project_id.is_fifteen_days', string="15 Days Notice")
    cross_dock = fields.Boolean("Cross Dock")
    second_process = fields.Boolean("Second Process")
    origin_container = fields.Many2one('stock.container', 'Origin')
    is_time_updated = fields.Boolean('Is time updated', default=False, compute="_compute_time_updation")
    chronopost_number = fields.Many2one('carton.line', domain="[('carton_id' , '=' , project_id)]")
    is_registered_package = fields.Boolean('Is Chronopost Package')
    cross_dock_lines = fields.One2many("cross.dock.line", "container_id", string="Recipient Container")
    volume = fields.Float("Volume", compute="_compute_container_volume")
    cnt_type = fields.Selection(
        [('Parent Containers', 'Parent/Ungrouped Containers'), ('Child Containers', 'Child Containers')],
        default='Parent Containers', string="Parent/Child")
    vendor_ref = fields.Char("Vendor Reference")
    spot_value = fields.Monetary('Spot Value', currency_field='currency_id', compute='_compute_spot_value')
    remaining_weight = fields.Float("Remaining Weight(Kg)")
    description = fields.Char("Description")
    not_received = fields.Boolean('Not Received')
    not_received_reason = fields.Char('Reason')
    have_batteries = fields.Boolean('Batteries')
    batteries_weight = fields.Float('Batteries Weight', digits=(12, 4))
    fifteen_days_date = fields.Date(related='project_id.fifteen_days_date', string="15 Days Treatment Date")
    pricing_type = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('variable', 'Variable Price')
    ], string="Pricing", related='project_id.pricing_type')
    declared = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Declear?")

    def print_barcode(self):
        return self.env.ref('ppts_inventory_customization.report_project_container_barcode').report_action(self)

    def complete_non_conformity_cross_dock(self):
        vals = {
            'content_type_id': self.sub_product_id.id,
            'container_type_id': self.container_type_id.id,
            'tare_weight': self.container_type_id.tare_weight,
            'max_weight': self.container_type_id.capacity_weight,
            'location_id': self.location_id.id,
            'related_company_id': self.company_id.id,
            'project_id': self.project_id.id,
            'picking_id': self.picking_id.id,
            'net_weight_dup': self.net_gross_weight,
            'total_number_of_pieces_dup': self.quantity,
            'partner_id': self.partner_id.id,
            'container_specific': 'count' if self.quantity != 0 else 'weight',
            'cross_dock': True,
            'absolute_tare_weight': self.extra_tare
        }
        recipient_container_obj = self.env['stock.container'].create(vals)
        self.state = 'close'

    def _compute_remaining_weight(self):
        for rec in self:
            fractions = self.env["project.fraction"].search(
                [('source_container_id', '=', rec.id), ('state', '=', 'closed')])
            fraction_weight = 0.0
            for fr in fractions:
                fraction_weight += fr.fraction_weight
            rec.update({
                'remaining_weight': rec.net_gross_weight - fraction_weight
            })

    def _compute_spot_value(self):
        for rec in self:
            if rec.sub_product_id.uom_id.name == 'Tonne':
                quantity = (rec.net_gross_weight / 1000) * ((100 - rec.company_id.sale_margin_a) / 100)
            # elif rec.sub_product_id.uom_id.uom_type == 'kg':
            #     quantity = (rec.net_gross_weight * 1000) * ((100 - rec.company_id.sale_margin_a) / 100)
            else:
                quantity = rec.net_gross_weight * ((100 - rec.company_id.sale_margin_a) / 100)

            rec.update({
                'spot_value': quantity * rec.sub_product_id.list_price
            })

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

    def _compute_container_volume(self):
        for container in self:
            volume = 0.0
            if container.sub_product_id:
                volume = container.net_gross_weight * container.sub_product_id.density
            container.update({
                'volume': volume
            })

    def send_daily_action_plan(self):
        today = datetime.now().date()
        self.set_containers_inprogress()
        container_ids = self.env["project.container"].search(
            [('state', '=', 'in_progress'), ('action_date', '<=', today), ('action_date_end', '>=', today)])
        supervisors = []
        for d_container in container_ids:
            if d_container.supervisor_id and d_container.supervisor_id not in supervisors:
                supervisors.append(d_container.supervisor_id)
        for supervisor in supervisors:
            data = []
            for container in container_ids:
                vals = {}
                if supervisor.id == container.supervisor_id.id:
                    type = dict(container._fields['action_type'].selection).get(container.action_type)
                    vals.update({
                        'container': container.name,
                        'client': container.partner_id.name,
                        'action': type,
                        'location': container.location_id.name,
                        'workers': str([x.name for x in container.worker_ids])[1:-1].replace("'", "").replace('"', "")
                    })
                    data.append(vals)
            template_id = self.env.ref('ppts_inventory_customization.email_daily_action_plan')
            if template_id:
                template_id.with_context(
                    {'action_list': data, 'email_to': supervisor.work_email, 'name': supervisor.name, }).send_mail(
                    container.id, force_send=True)
        return True

    def set_containers_inprogress(self):
        today = datetime.now().date()
        container_ids = self.env["project.container"].search([('state', '=', 'planned'), ('action_date', '=', today)])
        for container in container_ids:
            container.state = 'in_progress'
        return True

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            picking_id = self.env["stock.picking"].search([('project_entry_id', '=', self.project_id.id)], limit=1)
            self.picking_id = picking_id.id
            self.partner_id = self.project_id.partner_id.id

    @api.depends('total_time', 'manual_time')
    def _compute_time_updation(self):
        for rec in self:
            if rec.total_time != 0.00 or rec.manual_time != 0.00:
                rec.update({
                    'is_time_updated': True
                })
            else:
                rec.update({
                    'is_time_updated': False
                })

    @api.depends('gross_weight', 'extra_tare')
    def _compute_net_gross_weight(self):
        for container in self:
            if container.child_container_ids:
                net_weight = 0.0
                for child_container in container.child_container_ids:
                    net_weight += child_container.net_gross_weight
                container.update({
                    'net_gross_weight': net_weight
                })
            else:
                net_weight = 0.00
                if container.extra_tare > 0.0:
                    net_weight = container.gross_weight - container.extra_tare
                else:
                    net_weight = container.gross_weight - container.container_type_id.tare_weight
                container.update({
                    'net_gross_weight': net_weight
                })

    def _compute_fractions_weight(self):
        for container in self:
            fractions = self.env["project.fraction"].search([('source_container_id', '=', container.id)])
            net_weight = 0.0
            for fr in fractions:
                net_weight += fr.fraction_weight
            container.update({
                'net_weight': net_weight
            })

    def _compute_container_count(self):
        for container in self:
            child_count = len(container.child_container_ids)
            container.update({
                'child_count': child_count
            })

    def _compute_actual_container_price(self):
        for container in self:
            fraction_obj = self.env['project.fraction'].search(
                [('project_id', '=', container.project_id.id), ('source_container_id', '=', container.id)])
            container_cost = 0.0
            if fraction_obj:
                for fraction in fraction_obj:
                    container_cost += fraction.production_cost
            else:
                container_cost = 0.0

            container.update({
                'actual_container_cost': container_cost
            })

    def _compute_container_price(self):
        for container in self:
            fraction_obj = self.env['project.fraction'].search(
                [('project_id', '=', container.project_id.id), ('source_container_id', '=', container.id)])
            container_cost = 0.0
            if fraction_obj:
                for fraction in fraction_obj:
                    container_cost += fraction.fraction_production_cost
            else:
                container_cost = 0.0

            container.update({
                'container_cost': container_cost
            })

            # container_obj = self.env['project.container'].search([('project_id', '=', container.project_id.id),('picking_id', '=', container.picking_id.id)])
            # rc_obj = self.env['stock.container'].search([('project_id', '=', container.project_id.id),('picking_id', '=', container.picking_id.id)])
            # sale_order_obj = self.env['sale.order'].search([('project_entree_id', '=', container.project_id.id),('project_entry_line_id', '=', container.project_entry_line_id.id)])
            # quantity = 0
            # for line in container.project_id.project_entry_ids:
            #     quantity += line.product_qty
            # if container.project_entry_line_id and container.gross_weight != 0.00:
            #     final_additional_sale_cost = 0.0
            #     additional_cost = 0.0
            #     unloading_cost = 0.0
            #     total_additional_sale_price = 0.0
            #     if container.project_entry_line_id.product_uom.name == 'Tonne':
            #         weight = container.project_entry_line_id.product_qty * 1000
            #     else:
            #         weight = container.project_entry_line_id.product_qty
            #     weight_percentage = ((container.net_gross_weight/weight) * 100)
            #     total_offer_price = container.project_entry_line_id.offer_price * container.project_entry_line_id.product_qty
            #     container_len = int(len(container_obj)) + int(len(rc_obj))
            #     if container.project_id.extra_purchase_cost != 0.0:
            #         additional_cost = container.project_id.extra_purchase_cost / quantity
            #     else:
            #         additional_cost = 0.0

            #     if container.picking_id.unloading_charges != 0.0:
            #         unloading_cost = container.picking_id.unloading_charges / quantity
            #     else:
            #         unloading_cost = 0.0

            #     if sale_order_obj:
            #         # total_additional_sale_price = 0.0
            #         for rec in sale_order_obj:
            #             total_additional_sale_price += rec.amount_total
            #         if container.project_entry_line_id.product_uom.name == 'Tonne':
            #             so_div_weight = container.project_entry_line_id.product_qty
            #         else:
            #             so_div_weight = container.project_entry_line_id.product_qty/1000
            #         if total_additional_sale_price != 0.0:
            #             final_additional_sale_cost = total_additional_sale_price/so_div_weight
            #         else:
            #             final_additional_sale_cost = 0.0

            #     container.update({
            #             'container_cost' : (((container.net_gross_weight/1000) * (container.project_entry_line_id.offer_price + additional_cost + unloading_cost)) - final_additional_sale_cost)
            #         })
            # else:
            #     container.update({
            #             'container_cost' : 0.0
            #         })

    @api.depends('timesheet_ids.timer_duration', 'manual_time')
    def _compute_total_duration(self):
        for rc in self:
            total_time = 0.0
            for line in rc.timesheet_ids:
                total_time += line.timer_duration

            if rc.manual_time != 0.0:
                total_time = rc.manual_time

            rc.update({
                'total_time': total_time,
            })

    def _compute_duration(self):
        self

    def _compute_is_user_working(self):
        """ Checks whether the current user is working """
        for order in self:
            if order.timesheet_ids.filtered(lambda x: (x.user_id.id == self.env.user.id) and (not x.date_end)):
                order.is_user_working = True
            else:
                order.is_user_working = False

    @api.model
    @api.constrains('task_timer')
    def toggle_start(self):
        if self.task_timer is True:
            self.write({'is_user_working': True, 'manual_time': 0.0})
            time_line = self.env['action.timing.line']
            for time_sheet in self:
                time_line.create({
                    'name': self.env.user.name + ': ' + time_sheet.name,
                    'container_id': time_sheet.id,
                    'user_id': self.env.user.id,
                    # 'container_id': time_sheet.container_id.id,
                    'date_start': datetime.now(),
                })
        else:
            self.write({'is_user_working': False})
            time_line_obj = self.env['action.timing.line']
            domain = [('container_id', 'in', self.ids), ('date_end', '=', False)]
            for time_line in time_line_obj.search(domain):
                time_line.write({'date_end': fields.Datetime.now()})
                if time_line.date_end:
                    diff = fields.Datetime.from_string(time_line.date_end) - fields.Datetime.from_string(
                        time_line.date_start)
                    time_line.timer_duration = round(diff.total_seconds() / 60.0, 2)
                    time_line.unit_amount = round(diff.total_seconds() / (60.0 * 60.0), 2)
                else:
                    time_line.unit_amount = 0.0
                    time_line.timer_duration = 0.0

    def calculate_gross_weight(self):

        containers_obj = self.env['project.container'].search(
            [('id', '!=', self.id), ('project_id', '=', self.project_id.id), ('picking_id', '=', self.picking_id.id)])

        no_gross_count = 0

        for container in containers_obj:
            if not container.gross_weight and container.parent_container_id != self:
                no_gross_count = no_gross_count + 1

        if no_gross_count == 0:
            total_gross = 0
            for container in containers_obj:
                total_gross = total_gross + container.gross_weight
            self.gross_weight = self.picking_id.net_weight_of_shipment - total_gross
            # self.gross_uom_id = self.picking_id.net_weight_of_shipment_uom_id
            child_obj = self.env['project.container'].search([
                ('id', '!=', self.id),
                ('project_id', '=', self.project_id.id),
                ('picking_id', '=', self.picking_id.id),
                ('is_child_container', '=', True),
                ('parent_container_id', '=', self.id)
            ])
            if child_obj:
                container_gross_weight = self.gross_weight / int(len(child_obj))
            for child in child_obj:
                child.gross_weight = container_gross_weight
                # child.gross_uom_id = self.gross_uom_id
        else:
            raise UserError(_('Please enter Gross weight for container'))

    def set_inprogress(self):
        if not self.operator_ids:
            if not (self.action_date or self.action_date_end or self.supervisor_id or self.worker_ids):
                raise UserError(_('Please select Operator/Create Action plan'))
            else:
                raise UserError(_('Please select Operators'))
        else:
            self.state = 'in_progress'

    def name_get(self):
        result = []
        for record in self:
            ref = ''
            if record.vendor_ref:
                ref = ' -' + record.vendor_ref
            else:
                ref = ''
            if record.partner_id.company_type == 'company':
                name = record.name + ' [' + record.partner_id.name + ref + ']'
                result.append((record.id, name))
            elif record.partner_id.company_type == 'person' and record.partner_id.parent_id:
                name = record.name + ' [' + record.partner_id.parent_id.name + ref + ']'
                result.append((record.id, name))
            else:
                name = record.name
                result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):

        project_id = self.env['project.entries'].browse(vals.get("project_id"))
        stock_picking_id = self.env['stock.picking'].browse(vals.get("picking_id"))
        ir_sequence_id = False
        if vals.get('refining_container_id'):
            ir_sequence_id = True
            vals['name'] = str(self.env['refining.containers'].browse(vals.get('refining_container_id')).name)

        if not ir_sequence_id and stock_picking_id:
            ir_sequence_id = self.env['ir.sequence'].search([('code', '=', stock_picking_id.name)])
            if ir_sequence_id and project_id:
                vals['name'] = str(project_id.name) + '/' + self.env['ir.sequence'].next_by_code(
                    stock_picking_id.name) or '/'

        if not ir_sequence_id:
            if vals.get('second_process') == True:
                recipient_container_obj = self.env['internal.project'].browse(vals.get('internal_project_id'))
                # vals['name'] = str(recipient_container_obj.name) + '/CT0001'
                sequence_id = self.env['ir.sequence'].create(
                    {'name': recipient_container_obj.name, 'code': recipient_container_obj.name, 'prefix': 'CE',
                     'padding': 2, 'number_increment': 1, 'number_next_actual': 1})
                if sequence_id:
                    vals['name'] = str(recipient_container_obj.name) + '/' + self.env['ir.sequence'].next_by_code(
                        recipient_container_obj.name) or '/'
            else:
                sequence_id = self.env['ir.sequence'].create(
                    {'name': stock_picking_id.name, 'code': stock_picking_id.name, 'prefix': 'CE', 'padding': 2,
                     'number_increment': 1, 'number_next_actual': 1})
                if sequence_id:
                    vals['name'] = str(project_id.name) + '/' + self.env['ir.sequence'].next_by_code(
                        stock_picking_id.name) or '/'

        res = super(ProjectContainer, self).create(vals)

        # if res.cross_dock:
        #     res.state = 'in_progress'
        if res.project_id.project_type == "reuse":
            res.state = "in_progress"
        elif res.confirmation == 'confirmed':
            res.state = 'confirmed'
        elif res.confirmation == 'non_conformity':
            try:
                template_id = self.env.ref('ppts_inventory_customization.non_conformity_notification_email')
            except ValueError:
                template_id = False
            if res.project_id.user_id.partner_id.email:
                res.location_id = res.location_id.id
                res.non_conformity_type = res.non_conformity_type
                type = dict(self._fields['non_conformity_type'].selection).get(res.non_conformity_type)
                template_id.with_context({'type': type}).send_mail(res.id, force_send=True)
            else:
                raise UserError(_('Please enter email address for %s') % res.project_id.user_id.partner_id.name)
            res.state = 'non_conformity'

        # updated stage to production for registered packages start(21/12/2020)
        if res.project_id.project_type == "reuse":
            res.state = "in_progress"
        # updated stage to production for registered packages end

        return res

    def unlink(self):
        for line in self:
            sequence_id = self.env['ir.sequence'].search([('code', '=', line.name)])
            if sequence_id:
                sequence_id.active = False
        return super(ProjectContainer, self).unlink()

    def action_create_fractions(self):
        action = self.env.ref('ppts_inventory_customization.action_create_fractions_view').read()[0]

        fraction_weight = 0.0
        if self.cross_dock:
            fraction_weight = self.net_gross_weight

        fraction_obj = self.env['project.fraction'].search([('source_container_id', '=', self.id)])
        actual_fraction_weight = 0.0
        if fraction_obj:
            for fraction in fraction_obj:
                actual_fraction_weight += fraction.fraction_weight
        remaining_container_weight = self.net_gross_weight - actual_fraction_weight

        action['context'] = {
            'default_project_id': self.project_id.id,
            'default_partner_ref': self.partner_ref,
            'search_default_source_container_id': self.id,
            'default_source_container_id': self.id,
            'default_supplier_id': self.project_id.origin.partner_id.id or False,
            'default_main_fraction_id': self.container_type_id.id or False,
            'default_container_weight': remaining_container_weight,
            'default_worker_id': self.operator_id.id,
            # 'default_container_weight_uom_id':self.net_uom_id.id,
            'default_waste_code': self.sub_product_id.product_waste_code,
            # 'default_main_product_id': self.main_product_id.id,
            # 'default_sub_product_id': self.sub_product_id.id,
            'default_cross_dock': self.cross_dock,
            'default_fraction_weight': fraction_weight,
            'default_second_process': self.second_process,
            'default_internal_project_id': self.internal_project_id.id or False,
            'default_company_id': self.company_id.id or False
        }
        action['domain'] = [('source_container_id', '=', self.id)]
        quotations = self.env['project.fraction'].search([('source_container_id', '=', self.id)])
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('ppts_inventory_customization.project_fractions_form_view').id, 'form')]
            action['res_id'] = quotations.id
        return action

    def _compute_fraction_data(self):
        for container in self:
            fraction_count = 0
            fractions = self.env['project.fraction'].search([('source_container_id', '=', container.id)])
            if fractions:
                fraction_count = len(fractions)
            container.fraction_count = fraction_count

    def confirm_container(self):
        if self.gross_weight:
            if self.confirmation == 'confirmed':
                if self.location_id:
                    self.state = 'confirmed'
                else:
                    raise UserError(_("Please enter location for the container"))
            elif self.confirmation == 'non_conformity':
                return {
                    'name': "Move to Quarantine",
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'non.conformity.wizard',
                    'target': 'new',
                    # 'context': vals,
                }
        else:
            raise UserError(_("Please enter the Gross Weight"))

    def re_confirm_container(self):
        # self.confirmation = 'confirmed'
        # self.state = 'confirmed'

        return {
            'name': "Reconfirm Container",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'reconfirm.wizard',
            'target': 'new',
            # 'context': vals,
        }

    def update_work_time(self):
        vals = ({'default_duration': self.total_time})
        return {
            'name': "Create Action Plan",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update.time',
            'target': 'new',
            'context': vals,
        }

    def action_create_return_order(self):
        if self.return_shipment_id:
            raise UserError(_("Already return order is created for this container"))
        else:
            picking_type = self.env["stock.picking.type"].search([('code', '=', 'outgoing')], limit=1)
            dest_location = self.env["stock.location"].search([('usage', '=', 'supplier')], limit=1)

            vals = {
                'partner_id': self.project_id.partner_id.id,
                'location_id': self.location_id.id,
                'project_entry_id': self.project_id.id,
                'picking_type_id': picking_type.id,
                'move_type': 'direct',
                'location_dest_id': dest_location.id,
                # 'move_ids_without_package': []
            }
            # list_items=[]
            # list_items.append((0, 0, {
            #     'product_id': self.main_product_id.id,
            #     'product_uom_qty':1,
            #     'name': self.main_product_id.name,
            #     'product_uom':1
            #     # 'location_id': self.location_id.id,
            #     # 'location_dest_id':dest_location.id,
            # }))
            # vals['move_ids_without_package'] = list_items

            picking_id = self.env["stock.picking"].create(vals)
            self.return_shipment_id = picking_id.id

    def create_container_actions(self):
        container_ids = [];
        vals = {}
        containers = self.env['project.container'].search([('id', 'in', self.env.context.get('active_ids'))])
        list_items = []
        for line in containers:
            list_items.append((0, 0, {
                'container_id': line.id,
                'external_action_type': line.external_action_type,
            }))
        vals = ({'default_action_date': containers.action_date if len(containers) == 1 else '',
                 'default_action_date_end': containers.action_date_end if len(containers) == 1 else '',
                 # 'default_supervisor_id': containers.supervisor_id.id if containers.supervisor_id else None,
                 # 'default_worker_ids': containers.worker_ids.ids if containers.worker_ids else None,
                 'default_container_line': list_items})
        return {
            'name': "Create Action Plan",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.action.wizard',
            'target': 'new',
            'context': vals,
        }

    def set_to_close(self):
        self.task_timer = False
        real_time = 0.0
        if not self.cross_dock and self.total_time == 0.0 and self.manual_time == 0.0:
            raise UserError(
                _("Work hour for the container '%s' is 00:00. Please add work hour the container") % self.name)
        if self.total_time == 0.0:
            real_time = self.manual_time
        else:
            real_time = self.total_time

        hr, min = divmod(real_time, 60)
        hours = float(("%02d" % (hr)))
        minutes = float(("%02d" % (min)))

        hourly_amount = 0.0
        if self.standard_rate:
            hourly_amount += self.env.company.standard_rate
        if self.ea_rate:
            hourly_amount += self.env.company.ea_rate
        if self.contractor_rate:
            hourly_amount += self.env.company.contract_rate
        self.container_cost = ((hours) * hourly_amount) + (minutes * hourly_amount * (1.0 / 60))

        fraction_ids = self.env["project.fraction"].search([('source_container_id', '=', self.id)])

        if not self.second_process:
            dest_location_id = self.env["stock.location"].search(
                [('name', '=', 'Stock'), ('company_id', '=', self.project_id.company_id.id)], limit=1)
            picking_type = self.env["stock.picking.type"].search(
                [('code', '=', 'internal'), ('sequence_code', '=', 'INT'),
                 ('company_id', '=', self.project_id.company_id.id)], limit=1)
        else:
            dest_location_id = self.env["stock.location"].search(
                [('name', '=', 'Stock'), ('company_id', '=', self.company_id.id)], limit=1)
            picking_type = self.env["stock.picking.type"].search(
                [('code', '=', 'internal'), ('sequence_code', '=', 'INT'), ('company_id', '=', self.company_id.id)],
                limit=1)

        vals = {
            'location_id': self.location_id.id,
            'project_entry_id': self.project_id.id,
            'picking_type_id': picking_type.id,
            'move_type': 'direct',
            'location_dest_id': dest_location_id.id,
            'move_ids_without_package': [],
        }

        list_items = []
        if self.returnable_container and self.container_type_id.product_id:
            list_items.append((0, 0, {
                'product_id': self.container_type_id.product_id.id,
                'product_uom_qty': 1,
                'reserved_availability': 1,
                'quantity_done': 1,
                'name': self.container_type_id.product_id.name,
                'product_uom': self.container_type_id.product_id.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': dest_location_id.id,
            }))
            vals['move_ids_without_package'] = list_items

        for fraction in fraction_ids:
            if fraction.state == 'new':
                raise UserError(_("Please close Fraction '%s' to process further") % fraction.name)

            if not fraction.is_scrap:
                weight_percentage = 100 * (float(fraction.fraction_weight) / float(fraction.container_weight))
                fraction.labour_cost = round(((fraction.source_container_id.container_cost * weight_percentage) / 100),
                                             2)

            quantity = 0.00
            if fraction.fraction_by == 'weight':
                if fraction.sub_product_id.uom_id.name == 'Tonne':
                    quantity = fraction.fraction_weight / 1000
                else:
                    quantity = fraction.fraction_weight
            else:
                quantity = fraction.number_of_pieces

            list_items.append((0, 0, {
                'product_id': fraction.sub_product_id.id,
                'product_uom_qty': quantity,
                'reserved_availability': quantity,
                'quantity_done': quantity,
                'name': fraction.sub_product_id.name,
                'product_uom': fraction.sub_product_id.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': dest_location_id.id,
            }))
            vals['move_ids_without_package'] = list_items
            vals['project_container'] = self.id
        picking_id = self.env["stock.picking"].create(vals)
        picking_id.action_done()
        self.state = 'close'
        if self.child_container_ids:
            for rec in self.child_container_ids:
                rec.state = 'close'

    def create_fractions(self):
        vals = (
        {'default_main_product_id': self.main_product_id.id, 'default_container_type_id': self.container_type_id.id})
        return {
            'name': "Create Fractions",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.fraction.wizard',
            'target': 'new',
            'context': vals,
        }

    def close_container_wizard_button(self):
        container_lines = []
        lot_ids = []
        for rec in self:
            if rec.state == 'in_progress':
                net_weight = 0.0
                scrap_weight = 0.0
                fraction_ids = self.env["project.fraction"].search([('source_container_id', '=', rec.id)])
                for fraction in fraction_ids:
                    if fraction.state == "new":
                        UserError(_("Please make sure the fraction '%s' is closed") % fraction.name)
                    if fraction.is_scrap:
                        scrap_weight += fraction.fraction_weight
                    else:
                        net_weight += fraction.fraction_weight
                container_lines.append((0, 0, {
                    'container_id': rec.id,
                    'gross_weight': rec.net_gross_weight,
                    'net_weight': net_weight,
                    'primary_product': rec.main_product_id.id,
                    'count': rec.quantity,
                    'weight_difference': rec.net_gross_weight - net_weight - scrap_weight,
                    'scrap_weight': scrap_weight,
                }))

                if rec.returnable_container:
                    lot_ids.append((0, 0, {
                        'container_id': rec.id,
                        'location_id': rec.location_id.id,
                        # 'reuse_barcode': rec.reuse_barcode
                    }))
            else:
                raise UserError(_("Container can be closed only when it is in 'Production' state"))
        vals = ({'default_container_line': container_lines, 'default_lot_ids': lot_ids})
        return {
            'name': "Close Containers",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'close.container.wizard',
            'target': 'new',
            'context': vals,
        }

    def close_container_wizard(self):
        if self.env.context.get('active_ids'):
            containers = self.env['project.container'].search([('id', 'in', self.env.context.get('active_ids'))])

        container_lines = []
        lot_ids = []
        for rec in containers:
            if rec.state == 'in_progress':
                net_weight = 0.0
                scrap_weight = 0.0
                fraction_ids = self.env["project.fraction"].search([('source_container_id', '=', rec.id)])
                for fraction in fraction_ids:
                    if fraction.state == "new":
                        UserError(_("Please make sure the fraction '%s' is closed") % fraction.name)
                    if fraction.is_scrap:
                        scrap_weight += fraction.fraction_weight
                    else:
                        net_weight += fraction.fraction_weight
                container_lines.append((0, 0, {
                    'container_id': rec.id,
                    'gross_weight': rec.net_gross_weight,
                    'net_weight': net_weight,
                    'primary_product': rec.main_product_id.id,
                    'count': rec.quantity,
                    'weight_difference': rec.net_gross_weight - net_weight - scrap_weight,
                    'scrap_weight': scrap_weight,
                }))

                if rec.returnable_container:
                    lot_ids.append((0, 0, {
                        'container_id': rec.id,
                        'location_id': rec.location_id.id,
                        # 'reuse_barcode': rec.reuse_barcode
                    }))
            else:
                raise UserError(_("Container can be closed only when it is in 'Production' state"))
        vals = ({'default_container_line': container_lines, 'default_lot_ids': lot_ids})
        return {
            'name': "Close Containers",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'close.container.wizard',
            'target': 'new',
            'context': vals,
        }

    def group_container_wizard(self):
        container_ids = []
        group_container_weight = 0.00
        _logger.info("@++++++++++++ Group Container Context IDs. %s", self.env.context.get('active_ids'))
        containers = self.env['project.container'].search([('id', 'in', self.env.context.get('active_ids'))])
        _logger.info("@************ Group Container Container IDs. %s", containers)
        project = False
        picking_id = False
        for rec in containers:
            if not project:
                project = rec.project_id.id
            if not picking_id:
                picking_id = rec.picking_id.id
            if project == rec.project_id.id:
                if rec.state in ('new', 'confirmed'):
                    container_ids.append(rec.id)
                    group_container_weight += rec.gross_weight
            else:
                raise UserError(_("Containers can be grouped for the same project"))

        vals = ({'default_container_ids': container_ids, 'default_project': project, 'default_picking_id': picking_id,
                 'default_grouped_containers_weight': group_container_weight})
        _logger.info("@************ Selected Container Container IDs. %s", container_ids)
        _logger.info("@************ Group Container vals. %s", vals)
        _logger.info("@************ Group Container weight. %s", group_container_weight)
        return {
            'name': "Group Containers",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'group.container.wizard',
            'target': 'new',
            'context': vals,
        }

    def complete_cross_dock(self):
        total_weight = 0.0
        for line_l in self.cross_dock_lines:
            total_weight += line_l.weight
        if total_weight > self.net_gross_weight:
            raise UserError(_('Total weight of containers can not be greater than the unallocated weight!'))
        self.cross_dock = True
        for line in self.cross_dock_lines:
            fraction_vals = {
                'project_id': self.project_id.id,
                'source_container_id': self.id,
                'supplier_id': self.project_id.origin.partner_id.id or False,
                'container_weight': self.net_gross_weight,
                'waste_code': self.sub_product_id.product_waste_code,
                'main_product_id': self.main_product_id.id,
                'sub_product_id': self.sub_product_id.id,
                'cross_dock': self.cross_dock,
                'fraction_weight': self.net_gross_weight,
                'second_process': self.second_process,
                'internal_project_id': self.internal_project_id.id or False,
                'recipient_container_id': line.recp_id.id,
            }
            fraction_id = self.env["project.fraction"].create(fraction_vals)
            fraction_id.close_fraction()
            self.set_to_close()
            line.recp_id.close_container()

        return True

    def close_fractions_bulk(self):
        fractions = self.env['project.fraction'].search([('source_container_id', '=', self.id), ('state', '=', 'new')])
        list_items = []
        for line in fractions:
            list_items.append((0, 0, {
                'fraction_id': line.id,
                'main_product_id': line.main_product_id.id,
                'sub_product_id': line.sub_product_id.id,
                'fraction_weight': line.fraction_weight,
                'number_of_pieces': line.number_of_pieces,
                'recipient_container_id': line.recipient_container_id.id
            }))

        vals = ({'default_fraction_line': list_items, 'default_container_id': self.id})
        return {
            'name': "Close Fractions",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'close.fraction.wizard',
            'target': 'new',
            'context': vals,
        }


class CrossDockLine(models.Model):
    _name = 'cross.dock.line'
    _rec_name = 'recp_id'

    weight = fields.Float("Weight(Kg)", digits=(12, 4))
    recp_id = fields.Many2one("stock.container", string="Recipient Container")
    container_id = fields.Many2one("project.container")
    rcp_name = fields.Char(related='recp_id.name', string="Recipient Name")
    container_type_id = fields.Many2one("container.type", string="Container Type")
    location_id = fields.Many2one("stock.location", string="Location")
    sub_product_id = fields.Many2one("product.product", string="Secondary Type")
    cross_dock = fields.Boolean("Cross Dock?")


class StockContainer(models.Model):
    _name = 'stock.container'
    _inherit = ['mail.thread']

    @api.depends('fraction_line_ids.weight', 'net_weight_dup')
    def _compute_net_weight(self):
        for rc in self:
            container_weight = 0.0
            if rc.fraction_line_ids:
                for line in rc.fraction_line_ids:
                    container_weight += line.weight
                rc.update({
                    'net_weight': container_weight,
                    'net_weight_dup': container_weight
                })
            elif not rc.fraction_line_ids and rc.net_weight_dup > 0.0:
                rc.update({
                    'net_weight': rc.net_weight_dup,
                })
            else:
                rc.update({
                    'net_weight': 0.0,
                })

    @api.depends('fraction_line_ids.number_of_pieces', 'total_number_of_pieces_dup')
    def _compute_pieces(self):
        for rc in self:
            piece_count = 0
            if rc.fraction_line_ids:
                for line in rc.fraction_line_ids:
                    piece_count += line.number_of_pieces
                rc.update({
                    'total_number_of_pieces': piece_count,
                    'total_number_of_pieces_dup': piece_count
                })
            elif not rc.fraction_line_ids and rc.total_number_of_pieces_dup > 0:
                rc.update({
                    'total_number_of_pieces': rc.total_number_of_pieces_dup,
                })
            else:
                rc.update({
                    'total_number_of_pieces': 0,
                })


    @api.depends('content_type_id')
    def compute_content_type_id(self):
        for rc in self:
            if rc.content_type_id:
                print(rc.content_type_id.product_tmpl_id)
                rc.update({
                        'sub_product_name':rc.content_type_id.product_template_attribute_value_ids.name
                    })
            else:
                pass

    name = fields.Char("Sequence")
    max_weight = fields.Float("Maximum Weight(Kg)", digits=(12, 4), tracking=True)
    # uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    content_type_id = fields.Many2one("product.product", string="Content Type", tracking=True)
    sub_product_name = fields.Char('Sub Product Name', compute='compute_content_type_id', store=True)
    container_type_id = fields.Many2one("container.type", string="Container Type", tracking=True)
    net_weight = fields.Float("Net Weight(Kg)", digits=(12, 4), compute='_compute_net_weight', tracking=True)
    fraction_line_ids = fields.One2many("fraction.line", 'container', string="Fractions", tracking=True)
    state = fields.Selection([('open', 'Open'), ('to_be_sold', 'Closed/To Sale'), ('lead', 'Lead/Opportunity'),('second_process', 'Moved to Second Process'), ('subcontract', 'Sub Contract'), ('sold', 'Sold'), ('taf', 'TAF'),('done', "Done")], string="State", default='open', tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    forecast_sale_price = fields.Monetary('Production Cost', currency_field='currency_id',
                                          compute='_compute_production_price', tracking=True)
    forecast_sale_price_dup = fields.Monetary('Production Cost', currency_field='currency_id')
    is_scrap_container = fields.Boolean('Is Scrap Container')
    is_container_full = fields.Boolean("Is Container Full", compute='_compute_container_full_load', store=True)
    created_date = fields.Date("Created Date", default=lambda self: fields.Datetime.now())
    existing_barcode = fields.Char("Existing Barcode")
    tare_weight = fields.Float("Tare Weight(Kg)")
    net_weight_dup = fields.Float("Net Weight(Kg)", digits=(12, 4))
    total_number_of_pieces_dup = fields.Integer("Number of Pieces Duplicate")
    total_number_of_pieces = fields.Integer("Number of Pieces", compute='_compute_pieces')
    container_specific = fields.Selection([
        ('weight', 'Weight'),
        ('count', 'Count')
    ], string="Container by Weight/Count", default="weight")
    partner_id = fields.Many2one('res.partner', string="Client")
    client_name = fields.Char("Client Importé")
    cross_dock = fields.Boolean("Cross Dock?")
    location_id = fields.Many2one('stock.location', string='Storage Location', domain="[('usage','=','internal')]")
    is_vrac = fields.Boolean('Is Vrac Container')
    is_imported_stock = fields.Boolean('Is Imported Stock')
    potential_sales_cost = fields.Monetary('Potential Sales Cost', compute='_compute_potential_sales_cost',
                                           currency_field='currency_id')

    is_multi_product_container = fields.Boolean('Is Multi-Product Container')
    primary_content_type_id = fields.Many2one('product.template', string='Primary Content Type')
    secondary_content_type_id = fields.Many2many('product.product', string='Secondary Content Type',
                                                 domain="[('product_tmpl_id','=',primary_content_type_id)]")
    related_company_id = fields.Many2one('res.company', string="Related Owner")

    project_id = fields.Many2one('project.entries', string="Project ID")
    project_entry_line_id = fields.Many2one('project.entries.line', string="Project Entry Line ID",
                                            domain="[('project_entry_id','=',project_id)]")
    picking_id = fields.Many2one('stock.picking', string="Shipment ID")
    partner_id = fields.Many2one('res.partner', string="Client Name")
    source_container_id = fields.Many2one('project.container', string='Source Container ID')
    penalty_amount = fields.Monetary('Panalty Amount', currency_field='currency_id')
    gross_weight = fields.Float('Gross Weight(Kg)', digits=(12, 4), compute='_compute_gross_weight')
    active = fields.Boolean("Active", default=True)
    absolute_tare_weight = fields.Float('Absolute Tare Weight(Kg)', default=0.0)
    is_first_tare_update = fields.Boolean('Is First Update', default=False)
    sale_order_ids = fields.Many2many("sale.order", string="Sale Orders")
    so_count = fields.Integer("SO Count", compute='_so_count')
    container_cost = fields.Monetary('Container Cost', currency_field='currency_id',
                                     compute='_compute_recipient_container_price')
    estimated_container_cost = fields.Monetary('Estimated Container Cost', currency_field='currency_id',
                                               compute='_compute_estimated_container_cost')

    is_sales_cost_updated = fields.Boolean('Sales Cost Updated')
    volume = fields.Float("Volume", compute="_compute_stock_volume")
    cost_per_ton = fields.Monetary("Cost per Tonne", currency_field='currency_id', compute="_cost_per_tonne")
    cost_per_ton_dup = fields.Monetary("Cost per Tonne", currency_field='currency_id')
    is_internal_project_closed = fields.Boolean('Is Internal Project Closed?')

    # @api.depends('forecast_sale_price')
    def _cost_per_tonne(self):
        for container in self:
            cost_per_ton = 0.0
            if container.forecast_sale_price and container.net_weight:
                cost_per_ton = container.forecast_sale_price / (container.net_weight / 1000)
            container.update({
                'cost_per_ton': cost_per_ton,
                'cost_per_ton_dup': cost_per_ton
            })

    def _compute_stock_volume(self):
        for container in self:
            volume = 0.0
            if container.content_type_id:
                volume = container.net_weight * container.content_type_id.density
            elif container.is_multi_product_container and container.container_type_id:
                volume = container.net_weight * ((container.container_type_id.container_length / 100) * (
                            container.container_type_id.container_width / 100) * (
                                                             container.container_type_id.container_height / 100))
            container.update({
                'volume': volume
            })

    def _compute_estimated_container_cost(self):
        for container in self:
            quantity = 0
            for line in container.project_id.project_entry_ids:
                quantity += line.product_qty
            if container.project_entry_line_id and container.net_weight != 0.00:
                if container.project_id.extra_purchase_cost != 0.0:
                    additional_cost = container.project_id.extra_purchase_cost / quantity
                else:
                    additional_cost = 0.0

                if container.picking_id.unloading_charges != 0.0:
                    unloading_cost = container.picking_id.unloading_charges / quantity
                else:
                    unloading_cost = 0.0

                if container.picking_id.reception_charges != 0.0:
                    unloading_cost = container.picking_id.reception_charges / quantity
                else:
                    unloading_cost = 0.0

                cross_dock_cost = (container.net_weight / 1000) * container.project_id.company_id.cross_dock_cost
                if container.project_id.margin_class == 'class_a':
                    margin_class = container.project_id.company_id.sale_margin_a
                if container.project_id.margin_class == 'class_b':
                    margin_class = container.project_id.company_id.sale_margin_b
                if container.project_id.margin_class == 'class_c':
                    margin_class = container.project_id.company_id.sale_margin_c

                if container.project_id.is_ecologic:
                    container.update({
                        'estimated_container_cost': ((container.net_weight / 1000) * ((
                                                                                          container.content_type_id.ecologic_price) + additional_cost + unloading_cost + unloading_cost + cross_dock_cost))
                    })
                else:
                    container.update({
                        'estimated_container_cost': ((container.net_weight / 1000) * ((
                                                                                                  container.content_type_id.lst_price * (
                                                                                                      1 - (
                                                                                                          margin_class / 100))) + additional_cost + unloading_cost + unloading_cost + cross_dock_cost))
                    })
            else:
                container.update({
                    'estimated_container_cost': 0.0
                })

    def _compute_recipient_container_price(self):
        for container in self:
            credit_note_obj = self.env['account.move'].search(
                [('project_id', '=', container.project_id.id), ('type', '=', 'in_refund')])
            quantity = 0.0
            product_offer_price = 0.0
            for line in container.project_id.origin.mask_po_line_ids:
                if line.product_uom.name == 'Tonne':
                    quantity += line.product_qty
                else:
                    quantity += line.product_qty / 1000
                if line.product_id.id == container.content_type_id.id:
                    product_offer_price = line.price_unit
                else:
                    product_offer_price = product_offer_price

            total_credit = 0.0
            for credit_note in credit_note_obj:
                total_credit += credit_note.amount_total

            if quantity != 0.0:
                container_cost = (((container.net_weight / 1000) * product_offer_price) + (
                            ((container.net_weight / 1000) / quantity) * container.project_id.extra_purchase_cost) + (((
                                                                                                                                   container.net_weight / 1000) / quantity) * container.picking_id.unloading_charges) + (
                                              ((
                                                           container.net_weight / 1000) / quantity) * container.picking_id.reception_charges) + (
                                              (
                                                          container.net_weight / 1000) * container.project_id.company_id.cross_dock_cost)) - (
                                             ((container.net_weight / 1000) / quantity) * total_credit)
            else:
                container_cost = 0

            container.update({
                'container_cost': container_cost
            })

    def open_sale_orders(self):
        return {
            'name': _('Sale Order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', 'in', self.sale_order_ids.ids)],
            'views_id': False,
            'views': [(self.env.ref('sale.view_order_tree').id or False, 'tree'),
                      (self.env.ref('sale.view_order_form').id or False, 'form')],
        }

    @api.depends('sale_order_ids')
    def _so_count(self):
        for container in self:
            container.update({
                'so_count': len(container.sale_order_ids)
            })

    @api.depends('net_weight')
    def _compute_gross_weight(self):
        for container in self:
            if container.container_specific == 'weight':
                if container.absolute_tare_weight == 0.0:
                    container.update({
                        'gross_weight': container.net_weight + container.tare_weight
                    })
                else:
                    container.update({
                        'gross_weight': container.net_weight + container.absolute_tare_weight
                    })
            else:
                container.update({
                    'gross_weight': container.tare_weight
                })

    @api.onchange('absolute_tare_weight')
    def onchange_absolute_tare_weight(self):
        if self.cross_dock == True:
            if self.is_first_tare_update == False:
                tare_weight = self.absolute_tare_weight - self.tare_weight
                self.net_weight_dup = self.net_weight_dup - abs(self.absolute_tare_weight - self.tare_weight)
                self.is_first_tare_update = True
            else:
                self.net_weight_dup = self.gross_weight - self.absolute_tare_weight
        else:
            self.net_weight_dup = self.gross_weight

    @api.onchange('is_scrap_container')
    def _onchange_vrac(self):
        if self.is_scrap_container:
            return {
                'domain': {'location_id': [('scrap_location', '=', True)]},
            }

    @api.onchange('is_vrac')
    def _onchange_scrap(self):
        if self.is_vrac:
            return {
                'domain': {'location_id': [('is_vrac_location', '=', True)]},
            }

    def close_container(self):
        if self.cross_dock:
            dest_location_id = self.env["stock.location"].search(
                [('name', '=', 'Stock'), ('company_id', '=', self.project_id.company_id.id)], limit=1)
            picking_type = self.env["stock.picking.type"].search(
                [('code', '=', 'internal'), ('sequence_code', '=', 'INT'),
                 ('company_id', '=', self.project_id.company_id.id)], limit=1)
            vals = {
                'location_id': self.location_id.id,
                'project_entry_id': self.project_id.id,
                'picking_type_id': picking_type.id,
                'move_type': 'direct',
                'location_dest_id': dest_location_id.id,
                'move_ids_without_package': [],
            }
            list_items = []
            quantity = 0.0
            if self.container_specific == 'weight':
                if self.content_type_id.uom_id.name == 'Tonne':
                    quantity = self.net_weight / 1000
                else:
                    quantity = self.net_weight
            else:
                quantity = self.total_number_of_pieces
            print(self.content_type_id.name, '---')
            list_items.append((0, 0, {
                'product_id': self.content_type_id.id,
                'product_uom_qty': quantity,
                'reserved_availability': quantity,
                'quantity_done': quantity,
                'name': self.content_type_id.name,
                'product_uom': self.content_type_id.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': dest_location_id.id,
            }))
            # vals['move_ids_without_package'] = list_items
            # picking_id = self.env["stock.picking"].create(vals)
            # picking_id.move_ids_without_package = list_items
            # picking_id.action_done()

            quantity = 0.0
            if self.container_specific == 'weight':
                if self.content_type_id.uom_id.name == 'Tonne':
                    quantity = self.net_weight / 1000
                elif self.content_type_id.uom_id.uom_type == 'kg':
                    quantity = self.net_weight * 1000
                else:
                    quantity = self.net_weight
            else:
                quantity = self.total_number_of_pieces

            if not self.is_multi_product_container:
                stock_location = self.env["stock.location"].search(
                    [("is_stock_location", '=', True), ('company_id', '=', self.related_company_id.id)], limit=1)

                stock_vals = {
                    'product_id': self.content_type_id.id,
                    'location_id': stock_location.id,
                    'quantity': quantity,
                }
                self.env["stock.quant"].sudo().create(stock_vals)
            else:
                stock_location = self.env["stock.location"].search(
                    [("is_stock_location", '=', True), ('company_id', '=', self.related_company_id.id)], limit=1)
                for rec in self.secondary_content_type_id:
                    quantity = 0.0
                    final_quantity = 0.0
                    for line in self.fraction_line_ids:
                        if rec.id == line.fraction_id.sub_product_id.id:
                            if line.fraction_id.fraction_by == 'weight':
                                quantity += line.weight
                            else:
                                quantity += line.number_of_pieces

                    if self.container_specific == 'weight':
                        if rec.uom_id.name == 'Tonne':
                            final_quantity = quantity / 1000
                        else:
                            final_quantity = quantity
                    else:
                        final_quantity = quantity

                    stock_vals = {
                        'product_id': rec.id,
                        'location_id': stock_location.id,
                        'quantity': final_quantity,
                    }
                    self.env["stock.quant"].sudo().create(stock_vals)

        self.state = 'to_be_sold'

    @api.depends('net_weight')
    def _compute_potential_sales_cost(self):
        for container in self:
            if not container.is_multi_product_container:
                if container.container_specific == 'weight':
                    sales_cost = 0
                    if container.net_weight != 0:
                        if container.content_type_id.uom_id.name == 'Tonne':
                            sales_cost = (container.net_weight / 1000) * container.content_type_id.lst_price
                        # elif container.content_type_id.uom_id.name == 'kg':
                        #     sales_cost = (container.net_weight*1000) * container.content_type_id.lst_price 
                        else:
                            sales_cost = container.net_weight * container.content_type_id.lst_price
                        if container.cross_dock:
                            if container.penalty_amount != 0:
                                sales_cost = sales_cost + container.penalty_amount
                            else:
                                sales_cost = sales_cost
                        else:
                            sales_cost = sales_cost
                        if sales_cost != 0:
                            container.update({
                                'potential_sales_cost': sales_cost
                            })
                        else:
                            container.update({
                                'potential_sales_cost': 0.0
                            })
                    else:
                        container.update({
                            'potential_sales_cost': 0.0
                        })
                else:
                    sales_cost = 0
                    if container.total_number_of_pieces != 0:
                        sales_cost = container.total_number_of_pieces * container.content_type_id.lst_price
                        if container.cross_dock:
                            if container.penalty_amount != 0:
                                sales_cost = sales_cost + container.penalty_amount
                            else:
                                sales_cost = sales_cost
                        else:
                            sales_cost = sales_cost
                        if sales_cost != 0:
                            container.update({
                                'potential_sales_cost': sales_cost
                            })
                        else:
                            container.update({
                                'potential_sales_cost': 0.0
                            })
                    else:
                        container.update({
                            'potential_sales_cost': 0.0
                        })
            else:
                if container.container_specific == 'weight':
                    sales_cost = 0
                    for line in container.fraction_line_ids:
                        if line.fraction_id.sub_product_id.uom_id.name == 'Tonne':
                            quantity = line.weight / 1000
                        # elif line.fraction_id.sub_product_id.uom_id.name == 'kg':
                        #     quantity = line.weight * 1000
                        else:
                            quantity = line.weight
                        sales_cost = quantity * line.fraction_id.sub_product_id.lst_price
                    if sales_cost != 0:
                        container.update({
                            'potential_sales_cost': sales_cost
                        })
                    else:
                        container.update({
                            'potential_sales_cost': 0.0
                        })
                else:
                    sales_cost = 0
                    for line in container.fraction_line_ids:
                        sales_cost = line.number_of_pieces * line.fraction_id.sub_product_id.lst_price
                    if sales_cost != 0:
                        container.update({
                            'potential_sales_cost': sales_cost
                        })
                    else:
                        container.update({
                            'potential_sales_cost': 0.0
                        })

    @api.depends('net_weight', 'max_weight')
    def _compute_container_full_load(self):
        for container in self:
            if container.max_weight > 0.0 and container.max_weight == container.net_weight:
                container.update({
                    'is_container_full': True
                })
            else:
                container.update({
                    'is_container_full': False
                })

    # @api.depends('fraction_line_ids.production_cost')
    def _compute_production_price(self):
        for container in self:
            if container.cross_dock:
                if container.net_weight != 0.0:
                    container.update({
                        'forecast_sale_price': container.container_cost,
                        'forecast_sale_price_dup': container.container_cost
                    })
                else:
                    container.update({
                        'forecast_sale_price': 0.0,
                        'forecast_sale_price_dup': 0.0
                    })
            else:
                production_cost = 0.0
                if container.fraction_line_ids:
                    for line in container.fraction_line_ids:
                        production_cost += line.production_cost
                    container.update({
                        'forecast_sale_price': production_cost
                    })
                elif container.forecast_sale_price_dup:
                    if container.forecast_sale_price_dup > 0.0:
                        container.update({
                            'forecast_sale_price': container.forecast_sale_price_dup,
                        })
                    else:
                        container.update({
                            'forecast_sale_price': 0.0,
                        })
                else:
                    container.update({
                        'forecast_sale_price': 0.0,
                    })

    @api.onchange('container_type_id')
    def onchange_max_weight(self):
        if self.container_type_id:
            self.max_weight = self.container_type_id.capacity_weight
            self.tare_weight = self.container_type_id.tare_weight
            # self.uom_id = self.container_type_id.capacity_weight_uom_id
            if self.container_type_id.is_multi_product:
                self.is_multi_product_container = True
                self.primary_content_type_id = self.container_type_id.primary_content_type_id
                self.secondary_content_type_id = self.container_type_id.secondary_content_type_id

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('recipient.container.seq') or '/'
        res = super(StockContainer, self).create(vals)
        # if vals.get('fraction_line_ids'):
        rc_vals = []
        rc_line = {}
        rc_line.update({'container_id': res.id, 'net_weight': res.net_weight})
        rc_vals.append((0, 0, rc_line))
        res.content_type_id.container_product_ids = rc_vals
        return res

    def write(self, values):
        res = super(StockContainer, self).write(values)
        if values.get('fraction_line_ids'):
            if self.content_type_id.container_product_ids:
                lst = []
                for line in self.content_type_id.container_product_ids:
                    lst.append(line.container_id.id)
                    if line.container_id.id == self.id:
                        line.update({'net_weight': self.net_weight})
                if self.id not in lst:
                    rc_vals = []
                    rc_line = {}
                    rc_line.update({'container_id': self.id, 'net_weight': self.net_weight})
                    rc_vals.append((0, 0, rc_line))
                    self.content_type_id.container_product_ids = rc_vals
            else:
                rc_vals = []
                rc_line = {}
                rc_line.update({'container_id': self.id, 'net_weight': self.net_weight})
                rc_vals.append((0, 0, rc_line))
                self.content_type_id.container_product_ids = rc_vals

        return res

    def create_lead_from_rc(self):
        container_ids = []
        containers = self.env['stock.container'].search([('id', 'in', self.env.context.get('active_ids'))])
        for rec in containers:
            if rec.state == 'to_be_sold':
                container_ids.append(rec.id)
            elif rec.state == 'lead':
                container_ids.append(rec.id)
                # raise UserError(_('CRM Lead is already created for this container "%s"') % rec.name)

        vals = ({'default_container_ids': container_ids})
        return {
            'name': "Create Lead",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.lead.rc',
            'target': 'new',
            'context': vals,
        }

    def second_process_from_rc(self):
        container_ids = []
        containers = self.env['stock.container'].search([('id', 'in', self.env.context.get('active_ids'))])
        for rec in containers:
            if rec.state == 'to_be_sold':
                container_ids.append(rec.id)
            elif rec.state == 'lead':
                raise UserError(_('Lead is already created for this container "%s"') % rec.name)
            elif rec.state == 'second_process':
                don_con_obj = self.env['project.container'].search([('parent_rc_id','=',rec.id)])
                if don_con_obj.state == 'in_progress':
                    raise UserError(_('The container "%s" is already moved to Production') % rec.name)
                else:
                    container_ids.append(rec.id)
                # raise UserError(_('The container "%s" is already moved to Second Process') % rec.name)

        vals = ({'default_container_ids': container_ids})
        return {
            'name': "Second Process",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'second.process.rc',
            'target': 'new',
            'context': vals,
        }


class FractionLine(models.Model):
    _name = 'fraction.line'

    name = fields.Char("Fraction")
    fraction_id = fields.Many2one("project.fraction", string="Fraction")
    supplier_id = fields.Many2one("res.partner", string="Supplier", related='fraction_id.supplier_id')
    weight = fields.Float("Weight(Kg)", digits=(12, 4))
    number_of_pieces = fields.Integer("Number of Pieces")
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    container = fields.Many2one("stock.container", string="Container")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    production_cost = fields.Monetary('Production Cost', currency_field='currency_id',
                                      compute='_compute_production_cost')
    is_to_sell = fields.Boolean('To Sell')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    @api.depends('fraction_id.production_cost')
    def _compute_production_cost(self):
        for fraction in self:
            if fraction.fraction_id and fraction.fraction_id.production_cost:
                fraction.update({
                    'production_cost': fraction.fraction_id.production_cost
                })
            else:
                fraction.update({
                    'production_cost': 0.0
                })
