from odoo import fields, models, api, _

class ProjectFractions(models.Model):
    _name = 'project.fraction'
    _description = 'Project Fractions'

    name = fields.Char("Name")
    project_id = fields.Many2one("project.entries",string="Project ID")
    source_container = fields.Char("Source Container")
    container_weight = fields.Float("Source container weight(Kg)")
    supplier_id = fields.Many2one("res.partner",string="Supplier")
    sales_team_id = fields.Many2one("res.users", string="Sales Team")
    main_fraction_type = fields.Selection([('','')])
    sub_fraction_type = fields.Selection([('','')])
    fraction_weight = fields.Float("Fraction Weight(Kg)")
    number_of_pieces = fields.Integer("Number of pieces")
    labour_cost = fields.Float("Labour Cost")
    # service_cost = fields.Float("Service Cost")
    # service_provider_id = fields.Char("Service Provider ID")
    # transport_cost = fields.Float("Transport Cost")
    status = fields.Selection([('new','New'),('in_progress','In Progress'),('stock','Stock'),('container','Container'),('sold','Sold')],default='new')
    dest_container = fields.Char("Destination Container(s)")
    standard_waste_code = fields.Text("Standard waste code")
    client_waste_code = fields.Char("Client waste Code")

    @api.model
    def create(self, vals):
        if 'project_id' in vals:
            print (vals.get("project_id"))
            project_id = self.env['project.entries'].browse(vals.get("project_id"))
            fr_seq = self.env['ir.sequence'].next_by_code('project.fraction') or '/'
            vals['name'] = str(project_id.name) + '/'+ fr_seq
        return super(ProjectFractions, self).create(vals)