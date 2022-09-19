from odoo import fields, models, api, _
from odoo.exceptions import UserError

class CreateContainers(models.TransientModel):
    _name = 'create.container.wizard'

    @api.model
    def default_get(self, fields_name):
        res = super(CreateContainers, self).default_get(fields_name)
        if self._context.get('default_project_id'):
            res.update({'project_id': self._context.get('default_project_id')})

        return res

    project_id = fields.Many2one("project.entries", string="Project ID", required=1, domain="[('status','in', ('reception','wip'))]")
    project_entry_line_id = fields.Many2one('project.entries.line', string="Project Entry Line ID", domain="[('project_entry_id','=',project_id)]")
    picking_id = fields.Many2one("stock.picking", string="Shipment ID", required=1, domain="[('project_entry_id','=', project_id),('project_entry_id','!=', False)]")
    container_type_id = fields.Many2one("container.type", string="Container Type")
    gross_weight = fields.Float("Gross Weight(Kg)", digits=(12,4))
    quantity = fields.Integer("Count")
    confirmation = fields.Selection([('confirmed', 'Conformed'), ('non_conformity', 'Non Conformity')], string="Quality", required=1, tracking=True)
    action_type = fields.Selection([('internal', 'Internal'),
                                    ('external', 'External')], string="Action Type")
                                    # ('waiting', 'Waiting'),
                                    # ('cross_dock','Cross Dock'),
                                    # ('dismantling', 'Dismantling'),
                                    # ('re-use', 'Re-use'),
                                    # ('sorting', 'Sorting'),
                                    # ('repack', 'Repackaging'),
                                    # ('refining', 'Refining'),
                                    # ('loose', 'Vrac')], string="Action Type")

    external_action_type = fields.Selection([('sorting', 'Sorting'),
                                             ('refining', 'Refining')], string="Client Action Type")

    intended_action = fields.Selection([('vrac', 'Vrac'),
                                    ('development', 'Développeur'),
                                    ('engineering','Ingénierie'),
                                    ('qhse', 'QHSE')], string="Action Prévue")
    
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    location_id = fields.Many2one("stock.location", string="Location",
                                  domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    returnable_container = fields.Boolean("Returnable Container")
    extra_tare = fields.Float("Extra Tare Weight(Kg)")
    partner_id = fields.Many2one(related='project_id.partner_id', string="Client Name")
    notes = fields.Text("Notes")
    fifteen_day_notice = fields.Boolean(related='project_id.is_fifteen_days', string="15 Days Notice")
    container_count = fields.Integer("Number of Containers", default=1)
    main_product_id = fields.Many2one("product.template", string="Primary Type", tracking=True)
    sub_product_id = fields.Many2one("product.product", string="Secondary Type", domain="[('product_tmpl_id','=',main_product_id)]", tracking=True)
    non_conformity_type = fields.Selection([('dangerous', 'Dangerous Material'), ('content_mismatch', 'Content Mismatch'), ('quantity', 'Incorrect Quantity')], string="Non Conformity Type")
    cross_dock = fields.Boolean("Cross Dock?")
    unallocated_weight = fields.Float('Unallocated Weight(Kg)', digits=(12,4))
    allocated_weight = fields.Float('Allocated Weight(Kg)', digits=(12,4))
    crossdock_unallocated_weight = fields.Float('Unallocated Weight(Kg)', digits=(12,4))
    crossdock_allocated_weight = fields.Float('Allocated Weight(Kg)', digits=(12,4), compute='_crossdock_allocated_weight')
    tare_weight = fields.Float('Tare Weight(Kg)')
    net_weight_of_shipment = fields.Float('Net Weight of Shipment(Kg)', digits=(12,4))
    is_registered_package = fields.Boolean('Is Chronopost Package')
    recipient_container_id = fields.Many2one("stock.container", string="Recipient Container",
                                             domain="[('is_container_full','=',False),'|',('content_type_id','=',sub_product_id),('state','=','open')]")
    recipient_container_dup = fields.Char(related='recipient_container_id.name',string="Recipient Container")
    container_ids = fields.Many2many("project.container",string="Containers")
    fraction_ids = fields.Many2many("project.fraction",string="Fractions")
    cnt_created = fields.Boolean("Created")
    container_lines = fields.One2many("bulk.container.line","wiz_id",string="Recipient Containers")
    is_refining = fields.Boolean("Is Refining")
    add_desc = fields.Boolean("Add Description")
    description = fields.Char("Description")
    operator_id = fields.Many2one("hr.employee", "Operator",domain="[('is_worker','=', True)]")
    fifteen_days_date = fields.Date(related='project_id.fifteen_days_date',string="15 Days Treatment Date")

    # @api.onchange('action_type')
    # def onchange_action_type(self):
    #     res={'domain':{'recipient_container_id': "[('is_vrac', '=', False)]"}}
    #     if self.action_type == 'loose':
    #         res={'domain':{'recipient_container_id': "[('is_vrac', '=', True)]"}}
    #         if self.unallocated_weight >= 0.0:
    #             self.gross_weight = self.unallocated_weight
        
    # def create_vrac_process(self):
    #     if self.action_type == 'loose':
    #         container_weight = self.unallocated_weight - self.gross_weight
    #         tare_weight = 0.0
    #         if self.extra_tare:
    #             tare_weight = self.extra_tare
    #         else:
    #             tare_weight = self.tare_weight
    #         fraction_id = self.env["project.fraction"].create({
    #             'project_id': self.project_id.id,
    #             'worker_id' : self.operator_id.id,
    #             'is_vrac' : True,
    #             'main_product_id': self.main_product_id.id,
    #             'sub_product_id': self.sub_product_id.id,
    #             'recipient_container_id':self.recipient_container_id.id,
    #             'fraction_by':'weight',
    #             'container_weight':container_weight,
    #             'fraction_weight': self.gross_weight - tare_weight,
    #             'company_id': self.project_id.company_id.id,
    #         })
    #         fraction_id.close_fraction()

    #         return {
    #             'name': _('Fraction'),
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'project.fraction',
    #             'res_id': fraction_id.id,
    #             'view_id': False,
    #             'target': 'current',
    #         }


    @api.onchange('main_product_id','action_type')
    def onchange_main_product_id(self):
        if self.main_product_id and self.action_type == 'internal':
            non_trie_product = False
            non_trie = self.env["product.product"].search([('product_tmpl_id','=',self.main_product_id.id)],limit=1)
            if non_trie:
                non_trie_product = non_trie.id
            self.sub_product_id = non_trie_product

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            picking_id = self.env["stock.picking"].search([('project_entry_id', '=', self.project_id.id)], limit=1)
            self.picking_id = picking_id.id
            gross_weight = 0.0
            if picking_id.overwrite_gross:
                self.net_weight_of_shipment = picking_id.new_gross_weight
                gross_weight = picking_id.new_gross_weight
            else:
                self.net_weight_of_shipment = picking_id.net_weight_of_shipment
                gross_weight = picking_id.net_weight_of_shipment
            # if self.project_id.project_type != 'cross_dock':
            allocated_weight = 0.00
            dc_weight = 0.0
            fraction_weight = 0.0
            rc_weight = 0.0
            container_obj = self.env['project.container'].search([('project_id', '=', self.project_id.id), ('is_child_container', '!=', True)])
            rc_obj = self.env['stock.container'].search([('project_id', '=', self.project_id.id), ('picking_id', '=', picking_id.id)])
            fraction_obj = self.env['project.fraction'].search([('project_id', '=', self.project_id.id), ('is_vrac', '=', True)])
            if container_obj:
                for rec in container_obj:
                    dc_weight += rec.gross_weight
            if rc_obj:
                for rc in rc_obj:
                    rc_weight += rc.gross_weight
            if fraction_obj:
                for fraction in fraction_obj:
                    fraction_weight += fraction.fraction_weight
            allocated_weight = dc_weight + rc_weight + fraction_weight
            tolerance_weight = gross_weight + (gross_weight * self.company_id.tolerance_percentage/100)                        
            if allocated_weight != 0.0:
                self.allocated_weight = allocated_weight
                self.unallocated_weight = tolerance_weight - allocated_weight
            else:
                self.unallocated_weight = tolerance_weight
                self.crossdock_unallocated_weight = tolerance_weight
                self.allocated_weight = 0.00

            if self.project_id.project_type == 'refine':
                self.is_refining = True
            else:
                self.is_refining = False


    @api.depends('container_lines')
    def _crossdock_allocated_weight(self):
        for rec in self:
            allocated_weight = 0
            unallocated_weight = 0
            for line in rec.container_lines:
                allocated_weight += line.weight
            tolerance_weight = rec.net_weight_of_shipment + (rec.net_weight_of_shipment * rec.company_id.tolerance_percentage/100)
            if rec.container_lines:
                unallocated_weight = tolerance_weight - allocated_weight
            else:
                unallocated_weight = tolerance_weight
            rec.update({
                    'crossdock_allocated_weight' : allocated_weight,
                    'crossdock_unallocated_weight' : unallocated_weight
                })

    @api.onchange('container_type_id')
    def onchange_container_id(self):
        if self.container_type_id:
            self.tare_weight = self.container_type_id.tare_weight
            self.returnable_container = self.container_type_id.reusable_container

    def action_complete_cross_dock(self):
        if not self.confirmation == 'non_conformity':
            new_contaienrs_total_weight = 0.0
            for weight in self.container_lines:
                if weight.absolute_tare_weight == 0:
                    new_contaienrs_total_weight += weight.weight - weight.tare_weight
                else:
                    new_contaienrs_total_weight += weight.weight - weight.absolute_tare_weight
            no_container_capacity = 0
            for rec in self.container_lines:
                if rec.container_type_id.capacity_weight == 0:
                    no_container_capacity += 1
            if not self.unallocated_weight < new_contaienrs_total_weight:
                if no_container_capacity == 0:
                    if self.container_lines:
                        internal_project_containers = []                        
                        for weight in self.container_lines:
                            vals = {
                                'content_type_id' : self.sub_product_id.id,
                                'container_type_id' : weight.container_type_id.id,
                                'tare_weight' : weight.container_type_id.tare_weight,
                                'max_weight' : weight.container_type_id.capacity_weight,
                                'location_id' : self.location_id.id,
                                'related_company_id' : self.company_id.id,
                                'project_id' : self.project_id.id,
                                'project_entry_line_id' : self.project_entry_line_id.id if self.project_entry_line_id else False,
                                'picking_id' : self.picking_id.id,
                                'net_weight_dup' : (weight.weight - weight.tare_weight) if weight.absolute_tare_weight == 0 else (weight.weight - weight.absolute_tare_weight), 
                                'total_number_of_pieces_dup' :self.quantity,
                                'partner_id': self.partner_id.id,
                                'container_specific' : 'count' if self.quantity != 0 else 'weight',
                                'cross_dock' : True,
                                'absolute_tare_weight' : weight.absolute_tare_weight,
                                'total_number_of_pieces_dup' : weight.number_of_pieces_qty,
                            }
                            recipient_container_obj = self.env['stock.container'].create(vals)
                            recipient_container_obj.close_container()
                            if weight.is_second_process:
                                internal_project_containers.append(recipient_container_obj.id)
                        if len(internal_project_containers) != 0:
                            ctx = ({
                                'default_container_ids' : internal_project_containers,
                                'default_partner_id' : self.company_id.partner_id.id
                                })
                            form_id = self.env.ref('internal_project.inernal_project_view_form').id
                            return {
                                'name': _('Internal Project'),
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'internal.project',
                                'view_id': False,
                                'views': [(form_id, 'form')],
                                'target': 'current',
                                'context': ctx,
                            }
                    else:
                        raise UserError('Please Enter the gross weight of each containers')
                else:
                    raise UserError('Update the maximum capacity of the conatiner type')
            else:
                if not self.project_id.project_type=="refine":
                    raise UserError(_('Total weight of containers can not be greater than the unallocated weight!'))
        else:
            new_contaienrs_total_weight = 0
            for weight in self.container_lines:
                new_contaienrs_total_weight += weight.weight
            if not self.unallocated_weight < new_contaienrs_total_weight:
                if self.container_lines:
                    for weight in self.container_lines:
                        vals = {
                            'project_id': self.project_id.id,
                            'partner_ref' : self.project_id.partner_ref,
                            'picking_id': self.picking_id.id,
                            'container_type_id': weight.container_type_id.id,
                            'gross_weight': (weight.weight - weight.tare_weight) if weight.absolute_tare_weight == 0 else (weight.weight - weight.absolute_tare_weight),
                            'quantity': self.quantity,
                            'main_product_id': self.main_product_id.id,
                            'sub_product_id': self.sub_product_id.id,
                            'action_type': self.action_type,
                            'intended_action': self.intended_action,
                            'confirmation': self.confirmation,
                            'location_id': self.location_id.id,
                            'extra_tare': self.extra_tare,
                            'returnable_container': self.returnable_container,
                            'notes': self.notes,
                            'non_conformity_type': self.non_conformity_type,
                            'partner_id': self.partner_id.id,
                            'fifteen_day_notice': self.fifteen_day_notice,
                            'cross_dock': True,
                            'is_registered_package': self.is_registered_package,
                            'extra_tare' : weight.absolute_tare_weight
                        }                        
                        non_conformity_container_obj = self.env['project.container'].create(vals)
                else:
                    raise UserError('Please Enter the gross weight of each containers')                
            else:
                if not self.project_id.project_type=="refine":
                    raise UserError(_('Total weight of containers can not be greater than the unallocated weight!'))

    def action_create_containers(self):
        if self.is_refining and self.container_count > 1:
            raise UserError('You can create only one container at a time for the refining projects')

        if self.refining_container_id:
            name = self.env['project.container'].search([('name','=', self.refining_container_id.name)])
            if name:
                raise UserError('Container with the same name "%s" created already!' % self.refining_container_id.name)

        if self.container_count:
            new_contaienrs_total_weight = self.container_count * self.gross_weight
            if (not self.unallocated_weight < new_contaienrs_total_weight) or self.is_refining:
                count = 0
                containers = []
                while count < self.container_count:
                    vals = {
                        'project_id': self.project_id.id,
                        'partner_ref' : self.project_id.partner_ref,
                        'picking_id': self.picking_id.id,
                        'container_type_id': self.container_type_id.id,
                        'gross_weight': self.gross_weight,
                        'quantity': self.quantity,
                        'main_product_id': self.main_product_id.id,
                        'sub_product_id': self.sub_product_id.id,
                        'action_type': self.action_type,
                        'external_action_type': self.external_action_type,
                        'intended_action': self.intended_action,
                        'confirmation': self.confirmation,
                        'location_id': self.location_id.id,
                        'extra_tare': self.extra_tare,
                        'returnable_container': self.returnable_container,
                        'notes': self.notes,
                        'non_conformity_type': self.non_conformity_type,
                        'partner_id': self.partner_id.id,
                        'fifteen_day_notice': self.fifteen_day_notice,
                        'is_registered_package': self.is_registered_package,
                        'description':self.description,
                        'refining_container_id':self.refining_container_id.id,
                        'is_refining':self.is_refining,
                        'state': 'in_progress' if self.project_id.project_type=="reuse" else 'confirmed', 
                    }
                    container_id = self.env["project.container"].create(vals)
                    containers.append(container_id.id)
                    count += 1
                    if self.project_id.project_type == 'refine':
                        if self.sub_product_id.uom_id.uom_type == 'bigger':
                            quantity = (self.gross_weight - self.tare_weight) / self.sub_product_id.uom_id.factor_inv
                        elif self.sub_product_id.uom_id.uom_type == 'smaller':
                            quantity = (self.gross_weight - self.tare_weight) * self.sub_product_id.uom_id.factor
                        else:
                            quantity = self.gross_weight
                        stock_vals = {
                            'product_id': self.sub_product_id.id,
                            'location_id': self.location_id.id,
                            'quantity': quantity,
                        }
                        self.env["stock.quant"].sudo().create(stock_vals)


                tree_id = self.env.ref('ppts_inventory_customization.project_container_tree_view').id
                form_id = self.env.ref('ppts_inventory_customization.project_container_form_view').id

                return {
                    'name': _('Containers'),
                    'type': 'ir.actions.act_window',
                    'domain': [('id', '=', [x for x in containers])],
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'project.container',
                    'view_id': False,
                    'views': [(tree_id, 'tree'), (form_id, 'form')],
                    'target': 'current',
                }
            else:
                raise UserError('The total weight of new containers exceeds unallocated weight.Please check the weight!')

        else:
            raise UserError(_("Please add number of containers"))

class ContainerWizardLine(models.TransientModel):
    _name = 'bulk.container.line'
    _rec_name = 'recp_id'

    weight = fields.Float("Weight(Kg)", digits=(12,4))
    recp_id = fields.Many2one("stock.container", string="Recipient Container",domain="[('content_type_id','=',sub_product_id),('is_container_full','=',False),('state','in',('open','second_process')),('is_multi_product_container','=',True)]")
    wiz_id = fields.Many2one("create.container.wizard")
    rcp_name = fields.Char(related='recp_id.name',string="Recipient Name")
    container_type_id = fields.Many2one("container.type", string="Container Type")
    location_id = fields.Many2one("stock.location", string="Location")
    sub_product_id = fields.Many2one("product.product", string="Secondary Type")
    cross_dock = fields.Boolean("Cross Dock?")
    absolute_tare_weight = fields.Float('Absolute Tare Weight(Kg)', default = 0.0)
    tare_weight = fields.Float('Tare Weight(Kg)')
    number_of_pieces_qty = fields.Float('Quantity')
    is_second_process = fields.Boolean('Second Process?')

    @api.onchange('container_type_id')
    def onchange_container_type_id(self):
        if self.container_type_id:
            self.tare_weight = self.container_type_id.tare_weight

