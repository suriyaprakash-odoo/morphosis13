from odoo import fields, models, api, _

class ContainerTypeLine(models.Model):
    _name = "container.type.line"
    _rec_name = "container_type_id"

    product_id = fields.Many2one('product.product',string="Product")
    container_type_id = fields.Many2one('container.type',string="Container Type")
    container_length = fields.Integer('Container Length')
    container_width = fields.Integer('Container Width')
    container_height = fields.Integer('Container Height')
    final_container_height = fields.Integer('Extra Height')
    container_dimentions = fields.Char('Container Dimentions')
    container_count = fields.Integer('No of Container')
    project_line_id = fields.Many2one('project.entries.line', string='Project entry line Reference')

    @api.onchange('container_type_id')
    def onchange_container_dimension(self):
        self.container_length = self.container_type_id.container_length
        self.container_width = self.container_type_id.container_width
        self.container_height = self.container_type_id.container_height

    # @api.model
    # def create(self,vals):
    #     res = super(ContainerTypeLine, self).create(vals)
    #     if vals.get('container_count'):
    #         # res.project_line_id.project_entry_id.no_of_container = 0
    #         res.project_line_id.project_entry_id.no_of_container += int(vals.get('container_count'))
    #     return res
    #
    # def write(self,vals):
    #     previous_count = 0
    #     if vals.get('container_count'):
    #         previous_count = self.container_count
    #
    #     res = super(ContainerTypeLine, self).write(vals)
    #
    #     if previous_count != 0:
    #         self.project_line_id.project_entry_id.no_of_container = self.project_line_id.project_entry_id.no_of_container - previous_count
    #         self.project_line_id.project_entry_id.no_of_container += int(vals.get('container_count'))
    #
    #     return res
    #
    # def unlink(self):
    #     for rec in self:
    #         rec.project_line_id.project_entry_id.no_of_container = rec.project_line_id.project_entry_id.no_of_container - rec.container_count
    #
    #     return super(ContainerTypeLine, self).unlink()

class ProjectEntriesLine(models.Model):
    _inherit = 'project.entries.line'

    container_type_line_ids = fields.One2many('container.type.line','project_line_id',string="Container Type Line")
    container_count = fields.Integer(string='Containers count',compute='_compute_container_count')

    @api.depends('container_type_line_ids.container_count')
    def _compute_container_count(self):
        count =0
        for rec in self:
            if rec.container_type_line_ids:
                for line in rec.container_type_line_ids:
                    rec.container_count += line.container_count
                    count +=line.container_count
            else:
                rec.container_count = rec.container_count
                count +=rec.container_count
        if count:
            print(self.env.context)


# class SilverRefiningCost(models.Model):
#     _inherit = "silver.refining.cost"
#
#     container_ids = fields.Many2many('project.container', string='Containers', domain=[('state', '=', 'close')])
#     rc_container_ids = fields.Many2many('stock.container', string="Recipient Containers")
#
#     def update_actual_result(self):
#         actual_total = 0.0
#         donors = []
#         if self.rc_container_ids:
#             for rc in self.rc_container_ids:
#                 if rc.content_type_id.precious_metal in ('silver','gold','palladium','platinum','rhodium','ruthenium','iridium'):
#                     actual_total += rc.net_weight
#                 for fraction in rc.fraction_line_ids:
#                     if fraction.fraction_id.source_container_id:
#                         donors.append(fraction.fraction_id.source_container_id.id)
#             self.actual_result = actual_total * 1000
#             self.container_ids = [(6, 0, donors)]
#
#     @api.onchange('project_id')
#     def _onchange_project_id(self):
#         domain = {}
#         if self.project_id.id:
#             domain = {'rc_container_ids': [('content_type_id.precious_metal', 'in', ('silver','gold','palladium','platinum','rhodium','ruthenium','iridium'))]}
#         return {'domain': domain}
#
#
# class GoldRefiningCost(models.Model):
#     _inherit = "gold.refining.cost"
#
#     container_ids = fields.Many2many('project.container', string='Containers', domain=[('state', '=', 'close')])
#     rc_container_ids = fields.Many2many('stock.container', string="Recipient Containers")
#
#     def update_actual_result(self):
#         actual_total = 0.0
#         donors = []
#         for rc in self.rc_container_ids:
#             if rc.content_type_id.precious_metal in ('silver', 'gold', 'palladium', 'platinum', 'rhodium', 'ruthenium', 'iridium'):
#                 actual_total += rc.net_weight
#             for fraction in rc.fraction_line_ids:
#                 if fraction.fraction_id.source_container_id:
#                     donors.append(fraction.fraction_id.source_container_id.id)
#         self.actual_result = actual_total * 1000
#         self.container_ids = [(6, 0, donors)]
#
#     @api.onchange('project_id')
#     def _onchange_project_id(self):
#         domain = {}
#         if self.project_id.id:
#             domain = {'rc_container_ids': [('content_type_id.precious_metal', 'in', ('silver', 'gold', 'palladium', 'platinum', 'rhodium', 'ruthenium', 'iridium'))]}
#         return {'domain': domain}
#
# class PalladiumRefiningCost(models.Model):
#     _inherit = "palladium.refining.cost"
#
#     container_ids = fields.Many2many('project.container', string='Containers', domain=[('state', '=', 'close')])
#     rc_container_ids = fields.Many2many('stock.container', string="Recipient Containers")
#
#     def update_actual_result(self):
#         actual_total = 0.0
#         donors = []
#         for rc in self.rc_container_ids:
#             if rc.content_type_id.precious_metal in ('silver','gold','palladium','platinum','rhodium','ruthenium','iridium'):
#                 actual_total += rc.net_weight
#             for fraction in rc.fraction_line_ids:
#                 if fraction.fraction_id.source_container_id:
#                     donors.append(fraction.fraction_id.source_container_id.id)
#         self.actual_result = actual_total * 1000
#         self.container_ids = [(6, 0, donors)]
#
#     @api.onchange('project_id')
#     def _onchange_project_id(self):
#         domain = {}
#         if self.project_id.id:
#             domain = {'rc_container_ids': [('content_type_id.precious_metal', 'in', ('silver','gold','palladium','platinum','rhodium','ruthenium','iridium'))]}
#         return {'domain': domain}
#
# class PlatinumRefiningCost(models.Model):
#     _inherit = "platinum.refining.cost"
#
#     container_ids = fields.Many2many('project.container', string='Containers', domain=[('state', '=', 'close')])
#     rc_container_ids = fields.Many2many('stock.container', string="Recipient Containers")
#
#     def update_actual_result(self):
#         actual_total = 0.0
#         donors = []
#         for rc in self.rc_container_ids:
#             if rc.content_type_id.precious_metal in ('silver', 'gold', 'palladium', 'platinum', 'rhodium', 'ruthenium', 'iridium'):
#                 actual_total += rc.net_weight
#             for fraction in rc.fraction_line_ids:
#                 if fraction.fraction_id.source_container_id:
#                     donors.append(fraction.fraction_id.source_container_id.id)
#         self.actual_result = actual_total * 1000
#         self.container_ids = [(6, 0, donors)]
#
#     @api.onchange('project_id')
#     def _onchange_project_id(self):
#         domain = {}
#         if self.project_id.id:
#             domain = {'rc_container_ids': [('content_type_id.precious_metal', 'in', ('silver', 'gold', 'palladium', 'platinum', 'rhodium', 'ruthenium', 'iridium'))]}
#         return {'domain': domain}
#
# class CopperRefiningCost(models.Model):
#     _inherit = "copper.refining.cost"
#
#     container_ids = fields.Many2many('project.container', string='Containers', domain=[('state', '=', 'close')])
#     rc_container_ids = fields.Many2many('stock.container', string="Recipient Containers")
#
#     def update_actual_result(self):
#         actual_total = 0.0
#         donors = []
#         for rc in self.rc_container_ids:
#             if rc.content_type_id.precious_metal in ('silver', 'gold', 'palladium', 'platinum', 'rhodium', 'ruthenium', 'iridium'):
#                 actual_total += rc.net_weight
#             for fraction in rc.fraction_line_ids:
#                 if fraction.fraction_id.source_container_id:
#                     donors.append(fraction.fraction_id.source_container_id.id)
#         self.actual_result = actual_total * 1000
#         self.container_ids = [(6, 0, donors)]
#
#     @api.onchange('project_id')
#     def _onchange_project_id(self):
#         domain = {}
#         if self.project_id.id:
#             domain = {'rc_container_ids': [('content_type_id.precious_metal', 'in', ('silver', 'gold', 'palladium', 'platinum', 'rhodium', 'ruthenium', 'iridium'))]}
#         return {'domain': domain}
#
# class RhodiumRefiningCost(models.Model):
#     _inherit = "rhodium.refining.cost"
#
#     container_ids = fields.Many2many('project.container', string='Containers', domain=[('state', '=', 'close')])
#     rc_container_ids = fields.Many2many('stock.container', string="Recipient Containers")
#
#     def update_actual_result(self):
#         actual_total = 0.0
#         donors = []
#         for rc in self.rc_container_ids:
#             if rc.content_type_id.precious_metal in ('silver', 'gold', 'palladium', 'platinum', 'rhodium', 'ruthenium', 'iridium'):
#                 actual_total += rc.net_weight
#             for fraction in rc.fraction_line_ids:
#                 if fraction.fraction_id.source_container_id:
#                     donors.append(fraction.fraction_id.source_container_id.id)
#         self.actual_result = actual_total * 1000
#         self.container_ids = [(6, 0, donors)]
#
#     @api.onchange('project_id')
#     def _onchange_project_id(self):
#         domain = {}
#         if self.project_id.id:
#             domain = {'rc_container_ids': [('content_type_id.precious_metal', 'in', ('silver', 'gold', 'palladium', 'platinum', 'rhodium', 'ruthenium', 'iridium'))]}
#         return {'domain': domain}
#
# class RutheniumRefiningCost(models.Model):
#     _inherit = "ruthenium.refining.cost"
#
#     container_ids = fields.Many2many('project.container', string='Containers', domain=[('state', '=', 'close')])
#     rc_container_ids = fields.Many2many('stock.container', string="Recipient Containers")
#
#     def update_actual_result(self):
#         actual_total = 0.0
#         donors = []
#         for rc in self.rc_container_ids:
#             if rc.content_type_id.precious_metal in ('silver','gold','palladium','platinum','rhodium','ruthenium','iridium'):
#                 actual_total += rc.net_weight
#             for fraction in rc.fraction_line_ids:
#                 if fraction.fraction_id.source_container_id:
#                     donors.append(fraction.fraction_id.source_container_id.id)
#         self.actual_result = actual_total * 1000
#         self.container_ids = [(6, 0, donors)]
#
#     @api.onchange('project_id')
#     def _onchange_project_id(self):
#         domain = {}
#         if self.project_id.id:
#             domain = {'rc_container_ids': [('content_type_id.precious_metal', 'in', ('silver','gold','palladium','platinum','rhodium','ruthenium','iridium'))]}
#         return {'domain': domain}
#
# class IridiumRefiningCost(models.Model):
#     _inherit = "iridium.refining.cost"
#
#     container_ids = fields.Many2many('project.container', string='Containers', domain=[('state', '=', 'close')])
#     rc_container_ids = fields.Many2many('stock.container', string="Recipient Containers")
#
#     def update_actual_result(self):
#         actual_total = 0.0
#         donors = []
#         for rc in self.rc_container_ids:
#             if rc.content_type_id.precious_metal in ('silver', 'gold', 'palladium', 'platinum', 'rhodium', 'ruthenium', 'iridium'):
#                 actual_total += rc.net_weight
#             for fraction in rc.fraction_line_ids:
#                 if fraction.fraction_id.source_container_id:
#                     donors.append(fraction.fraction_id.source_container_id.id)
#         self.actual_result = actual_total * 1000
#         self.container_ids = [(6, 0, donors)]
#
#     @api.onchange('project_id')
#     def _onchange_project_id(self):
#         domain = {}
#         if self.project_id.id:
#             domain = {'rc_container_ids': [('content_type_id.precious_metal', 'in', ('silver', 'gold', 'palladium', 'platinum', 'rhodium', 'ruthenium', 'iridium'))]}
#         return {'domain': domain}