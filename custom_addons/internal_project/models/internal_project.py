from odoo import fields, models, api, _
from odoo.exceptions import UserError


class InternalProject(models.Model):
    _name = 'internal.project'

    @api.depends('container_ids')
    def _compute_production_price(self):
        for rc in self:
            production_cost = 0.0
            if rc.container_ids:
                for line in rc.container_ids:
                    production_cost += line.forecast_sale_price
                    rc.update({
                        'production_cost': production_cost,
                    })
            else:
                rc.update({
                    'production_cost': production_cost,
                })


    name = fields.Char('Project')
    action_type = fields.Selection([('grinding', 'Grinding'),
                                    ('dismantling', 'Dismantling'),
                                    ('repackaging', 'Repackaging'),
                                    ('sorting', 'Sorting'),
                                    ('sorting_vrac', 'Vrac'),
                                    ('vrac', 'RC Vrac'),
                                    ('test', 'Test')], string="Action Type")
    location_id = fields.Many2one("stock.location", string="Location", domain="[('usage','=','internal')]")
    container_ids = fields.Many2many("stock.container", string='Containers', domain="[('state','=', ('to_be_sold'))]")
    partner_id = fields.Many2one('res.partner', string="Client Name", domain="[('internal_company', '=', True)]")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    production_cost = fields.Monetary('Production Cost', currency_field='currency_id', compute='_compute_production_price')
    rc_container_count = fields.Integer("Number of Containers", compute='_compute_container_count')
    container_count = fields.Integer("Number of Containers", compute='_compute_container')
    content_type_id = fields.Many2one("product.product", string="Content Type")
    net_weight = fields.Float("Container Net Weight(kg)", compute='_compute_container')
    project_containers = fields.Many2many("project.container", string="Containers")
    final_production_cost = fields.Monetary('Total Production Cost', currency_field='currency_id', compute='_compute_total_production_cost')
    state = fields.Selection([
        ('new', 'New'),
        ('processing', 'Processing'),
        ('done','Sorted/Treated')
    ], string="state", default="new")
    company_id = fields.Many2one('res.company', string='Company',  default=lambda self: self.env.user.company_id)

    def _compute_total_production_cost(self):
        for record in self:
            fractions = self.env["project.fraction"].search([('internal_project_id', '=', record.id)])
            production_cost = 0.0
            if fractions:
                for fraction in fractions:
                    production_cost += fraction.production_cost
                    record.update({
                        'final_production_cost': production_cost
                    })
            else:
                record.update({
                    'final_production_cost': production_cost
                })

    def _compute_container_count(self):
        for rc in self:
            rc.update({
                'rc_container_count': len(self.env["project.container"].search([('internal_project_id', '=', rc.id)])),
            })

    @api.depends('container_ids')
    def _compute_container(self):
        for rc in self:
            container_count = 0
            net_weight = 0.0
            rc_container_count = 0

            for record in rc.container_ids:
                net_weight += record.net_weight
            if rc.container_ids:
                container_count = len(rc.container_ids)
            else:
                container_count = container_count
                net_weight = net_weight

            rc.update({
                'container_count': container_count,
                'net_weight':net_weight,
            })

    @api.model
    def create(self, vals):
        # vals['name'] = self.env['ir.sequence'].next_by_code('internal.project.seq') or '/'
        if vals.get('action_type') == 'grinding':
            vals['name'] = self.env['ir.sequence'].next_by_code('internal.project.bro') or '/'
        elif vals.get('action_type') == 'dismantling':
            vals['name'] = self.env['ir.sequence'].next_by_code('internal.project.dem') or '/'
        elif vals.get('action_type') == 'repackaging':
            vals['name'] = self.env['ir.sequence'].next_by_code('internal.project.rec') or '/'
        elif vals.get('action_type') == 'sorting':
            vals['name'] = self.env['ir.sequence'].next_by_code('internal.project.tri') or '/'
        elif vals.get('action_type') == 'vrac':
            vals['name'] = self.env['ir.sequence'].next_by_code('internal.project.vra') or '/'
        elif vals.get('action_type') == 'sorting_vrac':
            vals['name'] = self.env['ir.sequence'].next_by_code('internal.project.svra') or '/'
        elif vals.get('action_type') == 'test':
            vals['name'] = self.env['ir.sequence'].next_by_code('internal.project.tes') or '/'
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('internal.project.seq') or '/'

        return super(InternalProject, self).create(vals)

    def action_close(self):
        containers = self.env['project.container'].search([('internal_project_id','=',self.id)])
        if containers:
            container_count = len(containers)
            closed_count = 0
            for container in containers:
                if container.state == 'close':
                    closed_count += 1
            if container_count == closed_count:
                self.state = 'done'
                # for cnt in self.container_ids:
                #     cnt.active = False

    def action_create_second_process(self):
        containers = []
        created = False
        if not self.container_ids:
            raise UserError(_('Please add some containers to proceed'))
        for rec in self.container_ids:
            container_obj = self.env['project.container'].search([('origin_container','=',rec.id)],limit=1)
            if container_obj:
                if container_obj.state != 'in_progress':
                    container_obj.state = 'cancel'
                else:
                    raise UserError(_('The container "%s" is already moved to production') % container_obj.name)

            container_id = self.env['project.container'].create({
                    'second_process' : True,
                    'partner_id' : self.partner_id.id,
                    'container_type_id' : rec.container_type_id.id,
                    'second_process_action_type' : self.action_type,
                    'main_product_id' : rec.content_type_id.product_tmpl_id.id,
                    'sub_product_id' : rec.content_type_id.id,
                    'location_id' : self.location_id.id,
                    'confirmation' : 'confirmed',
                    'origin_container' : rec.id,
                    'gross_weight' : rec.gross_weight,
                    'extra_tare' : rec.tare_weight,
                    'internal_project_id':self.id,
                    'second_process_cost': rec.forecast_sale_price,
                    'parent_rc_id':rec.id
                })
            containers.append(container_id.id)
            rec.state = 'second_process'
            created = True
            if rec.container_specific == 'weight':
                if rec.content_type_id.uom_id.uom_type == 'bigger':
                    quantity = rec.net_weight / rec.content_type_id.uom_id.factor_inv
                elif rec.content_type_id.uom_id.uom_type == 'smaller':
                    quantity = rec.net_weight * rec.content_type_id.uom_id.factor
                else:
                    quantity = rec.net_weight
            else:
                quantity = rec.total_number_of_pieces

            stock = self.env["stock.quant"].search([('product_id','=', rec.content_type_id.id),('location_id','=',rec.location_id.id)],limit=1)
            if stock:
                stock.sudo().write({'quantity':stock.quantity - quantity})
            dest_location_id = self.env["stock.location"].search([('name', '=', 'Virtual Location'), ('company_id', '=', rec.project_id.company_id.id)], limit=1)
            picking_type = self.env["stock.picking.type"].search([('code', '=', 'internal'), ('sequence_code', '=', 'INT'), ('company_id', '=', rec.project_id.company_id.id)], limit=1)
            vals = {
                    'location_id': self.location_id.id,
                    'project_entry_id': rec.project_id.id,
                    'picking_type_id': picking_type.id,
                    'move_type': 'direct',
                    'location_dest_id': dest_location_id.id,
                    'move_ids_without_package': [],
                }
            list_items = []
            list_items.append((0, 0, {
                    'product_id': rec.content_type_id.id,
                    'product_uom_qty': quantity,
                    'reserved_availability': quantity,
                    'quantity_done': quantity,
                    'name': rec.content_type_id.name,
                    'product_uom': rec.content_type_id.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': dest_location_id.id,
                }))
            vals['move_ids_without_package'] = list_items

            picking_id = self.env["stock.picking"].create(vals)
            picking_id.action_done()
        if created:
            if self.project_containers:
                self.project_containers = [(4, containers[0])]
            else:
                self.project_containers = [(6, 0, containers)]
            self.state = 'processing'

    
    def action_view_vrac_fractions(self):
        return{
            'name': _('VRAC Fractions'),
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'project.fraction',
             'domain': [('internal_project_id', '=', self.id)],
            'views_id':False,
            'views':[(self.env.ref('ppts_inventory_customization.project_fractions_tree_view').id or False, 'tree'),
                     (self.env.ref('ppts_inventory_customization.project_fractions_form_view').id or False, 'form')],
            }

    
    def action_view_project_containers(self):
        return{
            'name': _('2nd Process Containers'),
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'project.container',
             'domain': [('internal_project_id', '=', self.id)],
            'views_id':False,
            'views':[(self.env.ref('internal_project.project_container_tree_view_internal_project').id or False, 'tree'),
                     (self.env.ref('ppts_inventory_customization.project_container_form_view').id or False, 'form')],
            }



class ProejctContainer(models.Model):
    _inherit = "project.container"

    internal_project_id = fields.Many2one('internal.project', string="Internal Project")
    second_process_cost = fields.Float("Second Process Cost")
    parent_rc_id = fields.Many2one("stock.container", string="Parent Recipient")

    def action_create_fractions(self):
        action = self.env.ref('ppts_inventory_customization.action_create_fractions_view').read()[0]

        fraction_weight = 0.0
        if self.cross_dock:
            fraction_weight = self.net_gross_weight

        action['context'] = {
            'default_project_id': self.project_id.id,
            'search_default_source_container_id': self.id,
            'default_source_container_id': self.id,
            'default_supplier_id': self.project_id.origin.partner_id.id or False,
            'default_main_fraction_id': self.container_type_id.id or False,
            'default_container_weight': self.remaining_weight,
            # 'default_container_weight_uom_id':self.net_uom_id.id,
            'default_waste_code': self.sub_product_id.product_waste_code,
            # 'default_main_product_id': self.main_product_id.id,
            # 'default_sub_product_id': self.sub_product_id.id,
            'default_cross_dock': self.cross_dock,
            'default_fraction_weight': fraction_weight,
            'default_second_process':self.second_process,
            'default_internal_project_id':self.internal_project_id.id or False,
            'default_parent_rc_id': self.parent_rc_id.id or False
        }
        action['domain'] = [('source_container_id', '=', self.id)]
        quotations = self.env['project.fraction'].search([('source_container_id', '=', self.id)])
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('ppts_inventory_customization.project_fractions_form_view').id, 'form')]
            action['res_id'] = quotations.id
        return action



    def set_to_close(self):
        self.task_timer = False

        if not self.cross_dock and self.total_time == 0.0:
            raise UserError(_("Work hour for the container '%s' is 00:00. Please add work hour the container") % self.name)

        real_time = self.total_time

        hr, min = divmod(real_time, 60)
        hours = float(("%02d" % (hr)))
        minutes = float(("%02d" % (min)))

        container_cost = 0.0
        hourly_amount = 0.0
        if self.cross_dock:
            container_cost = self.env.company.cross_dock_cost * self.net_gross_weight
        else:
            if self.standard_rate:
                hourly_amount += self.env.company.standard_rate
            if self.ea_rate:
                hourly_amount += self.env.company.ea_rate
            if self.contractor_rate:
                hourly_amount += self.env.company.contract_rate
            container_cost = ((hours) * hourly_amount) + (minutes * hourly_amount * (1.0 / 60))

        self.container_cost = container_cost

        fraction_ids = self.env["project.fraction"].search([('source_container_id', '=', self.id)])

        if self.second_process:
            company_id = self.company_id.id
            if self.parent_rc_id.container_specific == 'weight':
                if self.parent_rc_id.content_type_id.uom_id.name == 'Tonne':
                    quantity = self.parent_rc_id.net_weight / 1000
                else:
                    quantity = self.parent_rc_id.net_weight
            else:
                quantity = self.parent_rc_id.total_number_of_pieces

            if self.child_container_ids:
                for line in self.child_container_ids:
                    source_location_id = line.parent_rc_id.location_id
                    product_uom = line.parent_rc_id.content_type_id.uom_id
                    product_id = line.parent_rc_id.content_type_id
                    project_id = line.parent_rc_id.project_id
                    if line.parent_rc_id.container_specific == 'weight':
                        if line.parent_rc_id.content_type_id.uom_id.name == 'Tonne':
                            quantity += line.parent_rc_id.net_weight / 1000
                        else:
                            quantity += line.parent_rc_id.net_weight
                    else:
                        quantity += line.parent_rc_id.total_number_of_pieces
            else:
                source_location_id = self.parent_rc_id.location_id
                product_uom = self.parent_rc_id.content_type_id.uom_id
                product_id = self.parent_rc_id.content_type_id
                project_id = self.parent_rc_id.project_id
            # stock = self.env["stock.quant"].search([('product_id','=', rec.content_type_id.id),('location_id','=',rec.location_id.id)],limit=1)
            # if stock:
            #     stock.sudo().write({'quantity':stock.quantity - quantity})
            dest_location_id = self.env["stock.location"].search([('name', 'ilike', 'Virtual Location'), ('usage', '=', 'production'), ('company_id', '=', company_id)], limit=1)
            picking_type = self.env["stock.picking.type"].search([('code', '=', 'internal'), ('sequence_code', '=', 'INT'), ('company_id', '=', company_id)], limit=1)
            vals = {
                    'location_id': source_location_id.id,
                    'project_entry_id': project_id.id,
                    'picking_type_id': picking_type.id,
                    'move_type': 'direct',
                    'location_dest_id': dest_location_id.id,
                    'move_ids_without_package': [],
                }
            list_items = []
            list_items.append((0, 0, {
                    'product_id': product_id.id,
                    'product_uom_qty': quantity,
                    'reserved_availability': quantity,
                    'quantity_done': quantity,
                    'name': product_id.name,
                    'product_uom': product_uom.id,
                    'location_id': source_location_id.id,
                    'location_dest_id': dest_location_id.id,
                }))
            vals['move_ids_without_package'] = list_items
            if vals.get('move_ids_without_package'):
                picking_id = self.env["stock.picking"].create(vals)
                picking_id.move_ids_without_package = list_items
                picking_id.action_done() 
                
        else:
            company_id = self.project_id.company_id.id
        picking_type = self.env["stock.picking.type"].search([('code', '=', 'internal'), ('sequence_code', '=', 'INT'), ('company_id', '=', company_id)], limit=1)
        
        if not self.second_process:
            dest_location_id = self.env["stock.location"].search([('name', '=', 'Stock'), ('company_id', '=', self.project_id.company_id.id)], limit=1)
        else:
            dest_location_id = self.env["stock.location"].search([('name', '=', 'Stock'), ('company_id', '=', self.company_id.id)], limit=1)
        vals = {
            'location_id': self.location_id.id,
            'project_entry_id': self.project_id.id,
            'picking_type_id': picking_type.id,
            'move_type': 'direct',
            'location_dest_id': dest_location_id.id,
            'move_ids_without_package': [],
        }

        list_items = []
        # if self.returnable_container and self.container_type_id.product_id:
        #     list_items.append((0, 0, {
        #         'product_id': self.container_type_id.product_id.id,
        #         'product_uom_qty': 1,
        #         'reserved_availability': 1,
        #         'quantity_done': 1,
        #         'name': self.container_type_id.product_id.name,
        #         'product_uom': self.container_type_id.product_id.uom_id.id,
        #         'location_id': self.location_id.id,
        #         'location_dest_id':8,
        #     }))
        #     vals['move_ids_without_package'] = list_items

        for fraction in fraction_ids:
            if fraction.state == 'new':
                raise UserError(_("Please close Fraction '%s' to process further") % fraction.name)

            if not fraction.is_scrap:
                if fraction.container_weight != 0.0:
                    weight_percentage = 100 * (float(fraction.fraction_weight) / float(fraction.container_weight))
                else:
                    weight_percentage = 0.0
                if self.second_process:
                    fraction.labour_cost = round(((fraction.source_container_id.second_process_cost * weight_percentage) / 100), 2)
                else:
                    fraction.labour_cost = round(((fraction.source_container_id.container_cost * weight_percentage) / 100), 2)

            if not fraction.sub_product_id.precious_metal:
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
        if vals.get('move_ids_without_package'):
            picking_id = self.env["stock.picking"].create(vals)
            picking_id.action_done()
        self.state = 'close'

        if self.internal_project_id:
            self.internal_project_id.action_close()
            self.parent_rc_id.is_internal_project_closed = True

        if self.child_container_ids:
            for rec in self.child_container_ids:
                rec.state = 'close'


class ProjectFractions(models.Model):
    _inherit = 'project.fraction'

    internal_project_id = fields.Many2one('internal.project', string="Internal Project ID")
    parent_rc_id = fields.Many2one("stock.container",string="Parent Recipient")

    @api.depends('labour_cost', 'source_container_id.container_cost')
    def _compute_production_price(self):
        for fraction in self:
            if not fraction.is_scrap and fraction.source_container_id.container_cost or fraction.source_container_id.second_process_cost and fraction.labour_cost:
                if fraction.sub_product_id.uom_id.uom_type == 'bigger':
                    final_weight = fraction.fraction_weight / fraction.sub_product_id.uom_id.factor_inv
                elif fraction.sub_product_id.uom_id.uom_type == 'smaller':
                    final_weight = fraction.fraction_weight * fraction.sub_product_id.uom_id.factor_inv
                else:
                    final_weight = fraction.fraction_weight
                sales_val = fraction.sub_product_id.lst_price * final_weight
                production_cost = sales_val * (1 - (fraction.project_id.company_id.margin_percentage / 100)) - fraction.labour_cost
                fraction.update({
                    'production_cost': production_cost
                })
            else:
                fraction.update({
                    'production_cost': 0.0
                })


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
            if self.recipient_container_id == self.parent_rc_id:
                self.recipient_container_id.fraction_line_ids.unlink()

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