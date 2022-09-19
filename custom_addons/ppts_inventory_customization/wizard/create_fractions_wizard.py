from odoo import fields, models, api, _
from odoo.exceptions import UserError


class CreateFractionWizard(models.TransientModel):
    _name = 'create.fraction.wizard'

    @api.model
    def default_get(self, fields_list):
        res = super(CreateFractionWizard, self).default_get(fields_list)
        if self._context.get('active_id'):
            container_id = self.env["project.container"].browse(self._context.get('active_id'))
            fractions_ids = self.env["project.fraction"].search([('source_container_id', '=', self._context.get('active_id'))])
            if len(fractions_ids) >= 1 and container_id.net_weight == container_id.net_gross_weight:
                res['action'] = 'close'
            elif len(fractions_ids) >= 1:
                res['action'] = 'update'
            else:
                res['action'] = 'create'
            res['have_batteries'] = container_id.have_batteries
            res['batteries_weight'] = container_id.batteries_weight
        return res

    main_product_id = fields.Many2one("product.template", string="Primary Type")
    template_id = fields.Many2one("fraction.template", string="Fraction Template")
    fraction_weight = fields.Float("Fraction Weight(Kg)", digits=(12,4))
    line_ids = fields.One2many("fraction.wizard.line", "wizard_id", string="Fractions")
    action = fields.Selection([('create', 'Create'), ('update', 'Update'), ('close', 'Close')], string="Action")
    fraction_ids = fields.One2many("fraction.line.items", "item_id", string="Fractions")
    container_type_id = fields.Many2one("container.type", string="Container Type")
    create_individual_fractions = fields.Boolean('Create Individual Fractions')
    worker_id = fields.Many2one("hr.employee", string="Operator", domain="[('is_worker','=', True)]")
    have_batteries = fields.Boolean('Batteries')
    batteries_weight = fields.Float('Batteries Weight', digits=(12,4))

    @api.onchange('main_product_id')
    def onchange_main_product_id(self):
        if self._context.get('active_id'):
            container_id = self.env["project.container"].browse(self._context.get('active_id'))
            res_domain = {'domain': {
                'worker_id': "[('id', '=', False)]",
            }}
            if container_id.operator_ids:
                res_domain['domain']['worker_id'] = "[('id', 'in', %s)]" % container_id.operator_ids.ids
            else:
                res_domain['domain']['worker_id'] = []
            return res_domain

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            self.line_ids.unlink()
            container_lines = []
            for line in self.template_id.product_ids:
                container_lines.append((0, 0, {
                    'product_id': line.id,
                    'container_type_id': self.container_type_id.id,
                }))
            self.line_ids = container_lines

    # @api.onchange('create_individual_fractions')
    # def onchange_create_individual_fractions(self):
    #     if self.create_individual_fractions:
    #         self.line_ids.unlink()

    @api.onchange('action')
    def onchange_action(self):
        if self.action == 'update':
            self.fraction_ids.unlink()
            self.action = 'update'
            fractions_ids = self.env["project.fraction"].search([('source_container_id', '=', self._context.get('active_id'))])
            if len(fractions_ids) >= 1:
                container_lines = []
                for line in fractions_ids:
                    container_lines.append((0, 0, {
                        'fraction_id': line.id,
                        'recipient_container_id': line.recipient_container_id.id,
                        'product_id': line.sub_product_id.id,
                        'fraction_weight': line.fraction_weight,
                        'number_of_pieces': line.number_of_pieces,
                        'worker_id': line.worker_id.id,
                        'state': line.state
                    }))
                self.fraction_ids = container_lines

        elif self.action == 'close':
            self.fraction_ids.unlink()
            self.action = 'close'
            fractions_ids = self.env["project.fraction"].search([('source_container_id', '=', self._context.get('active_id')),(('state', '=', 'new'))])
            if len(fractions_ids) >= 1:
                container_lines = []
                for line in fractions_ids:
                    container_lines.append((0, 0, {
                        'fraction_id': line.id,
                        'recipient_container_id': line.recipient_container_id.id,
                        'product_id': line.sub_product_id.id,
                        'fraction_weight': line.fraction_weight,
                        'number_of_pieces': line.number_of_pieces,
                        'worker_id': line.worker_id.id,
                        'state': line.state
                    }))
                self.fraction_ids = container_lines
        else:
            self.fraction_ids.unlink()
            self.action='create'


    def action_create_fraction(self):
        self._context.get('active_id')
        container_id = self.env["project.container"].browse(self._context.get('active_id'))

        fraction_obj = self.env['project.fraction'].search([('source_container_id', '=', self.id)])
        actual_fraction_weight = 0.0
        if fraction_obj:
            for fraction in fraction_obj:
                actual_fraction_weight += fraction.fraction_weight
        remaining_container_weight = container_id.net_gross_weight - actual_fraction_weight

        fractions = []
        for line in self.line_ids:
            if line.fraction_weight != 0.0 or line.number_of_pieces != 0.0:
                vals = {
                    'project_id': container_id.project_id.id,
                    'partner_ref': container_id.partner_ref,
                    'source_container_id': container_id.id,
                    'supplier_id': container_id.project_id.origin.partner_id.id or False,
                    # 'main_fraction_id': container_id.container_type_id.id or False,
                    'container_weight': remaining_container_weight,
                    'waste_code': line.product_id.product_waste_code,
                    'main_product_id': line.product_id.product_tmpl_id.id,
                    'sub_product_id': line.product_id.id,
                    'cross_dock': container_id.cross_dock,
                    'fraction_weight': line.fraction_weight,
                    'second_process': container_id.second_process,
                    'internal_project_id': container_id.internal_project_id.id or False,
                    'recipient_container_id': line.recipient_container_id.id,
                    'number_of_pieces': line.number_of_pieces,
                    'parent_rc_id': container_id.parent_rc_id.id,
                    'company_id': container_id.company_id.id,
                    'worker_id': self.worker_id.id,
                }

                fraction_id = self.env["project.fraction"].create(vals)
                fractions.append(fraction_id.id)
            if container_id.project_id.is_registered_package == True:
                fraction_id.close_fraction()

        action = self.env.ref('ppts_inventory_customization.action_create_fractions_view').read()[0]
        action['domain'] = [('id', 'in', fractions)]
        return action


    def action_update_fractions(self):
        if self.fraction_ids:
            for line in self.fraction_ids:
                line.fraction_id.write({
                    'fraction_weight': line.fraction_weight,
                    'recipient_container_id': line.recipient_container_id.id,
                    'number_of_pieces': line.number_of_pieces,
                    'worker_id': line.worker_id.id,
                })


    def close_fractions(self):
        if self.fraction_ids:
            for line in self.fraction_ids:
                line.fraction_id.write({
                    'fraction_weight': line.fraction_weight,
                    'recipient_container_id': line.recipient_container_id.id,
                    'number_of_pieces': line.number_of_pieces,
                    'worker_id': line.worker_id.id,
                })
                line.fraction_id.close_fraction()


class FractionLine(models.TransientModel):
    _name = 'fraction.wizard.line'

    wizard_id = fields.Many2one("create.fraction.wizard")
    product_id = fields.Many2one("product.product", string="Secondary Type")
    product_tmpl_id = fields.Many2one("product.template", related='product_id.product_tmpl_id', string="Product Template")
    recipient_container_id = fields.Many2one("stock.container", "Recipient Container",
                                             domain="[('is_container_full','=',False),'|',('content_type_id','=',product_id),('primary_content_type_id','=',product_tmpl_id),('state','in',('open','second_process'))]")
    fraction_weight = fields.Float("Fraction Weight(Kg)", digits=(12,4))
    number_of_pieces = fields.Integer("Piece Count")
    container_type_id = fields.Many2one("container.type", string="Container Type")
    worker_id = fields.Many2one("hr.employee", string="Operator", domain="[('is_worker','=', True)]")

    @api.onchange('number_of_pieces')
    @api.depends('number_of_pieces')
    def onchange_number_of_pieces(self):
        if self.number_of_pieces:
            if self.product_id.product_template_attribute_value_ids.uom_id.uom_type == 'bigger':
                final_weight = (self.product_id.product_template_attribute_value_ids.piece_weight / self.product_id.product_template_attribute_value_ids.uom_id.factor_inv) * self.number_of_pieces
            elif self.product_id.product_template_attribute_value_ids.uom_id.uom_type == 'smaller':
                final_weight = ((self.product_id.product_template_attribute_value_ids.piece_weight / self.product_id.product_template_attribute_value_ids.uom_id.factor) * self.number_of_pieces)
            else:
                final_weight = self.product_id.product_template_attribute_value_ids.piece_weight * self.number_of_pieces

            self.fraction_weight = final_weight

class Fraction(models.TransientModel):
    _name = "fraction.line.items"

    item_id = fields.Many2one("create.fraction.wizard")
    product_id = fields.Many2one("product.product", string="Secondary Type")
    product_tmpl_id = fields.Many2one("product.template", related='product_id.product_tmpl_id', string="Product Template")
    recipient_container_id = fields.Many2one("stock.container", "Recipient Container",
                                             domain="[('is_container_full','=',False),'|',('content_type_id','=',product_id),('primary_content_type_id','=',product_tmpl_id),('state','in',('open','second_process'))]")
    fraction_weight = fields.Float("Fraction Weight(Kg)", digits=(12,4))
    number_of_pieces = fields.Integer("Piece Count")
    fraction_id = fields.Many2one("project.fraction", string="Fraction")
    worker_id = fields.Many2one("hr.employee", string="Operator", domain="[('is_worker','=', True)]")
    state = fields.Selection([('new', 'Open'), ('closed', 'Closed')], string="State",readonly=True)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template")