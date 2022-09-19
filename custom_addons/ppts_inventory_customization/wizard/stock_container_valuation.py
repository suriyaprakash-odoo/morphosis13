from odoo import fields, models, api, _
from datetime import timedelta, datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class StockContainerValuation(models.TransientModel):
    _name = 'stock.container.valuation'

    picking_container_ids = fields.Many2many('stock.container',relation='stock_container_table1', string='Stock Containers in Picking List', column="stock_container_valuation_id")

    loaded_container_ids = fields.Many2many('stock.container',relation='stock_container_table2', string='Loaded Stock Containers (Warehouse)', column="stock_container_valuation_id")

    loaded_donar_container_ids = fields.Many2many('project.container',relation='project_container_table2', string='Loaded Donar Containers (Warehouse)', column="project_container_valuation_id")

    show_missing_containers = fields.Boolean(string="Missing Containers",default=False)
    warehouse_done_containers = fields.Boolean(string="Warehouse Done Containers",default=False)

    show_missing_donar_containers = fields.Boolean(string="Missing Donar Containers",default=False)
    warehouse_done_donar_containers = fields.Boolean(string="Warehouse Done Donar Containers",default=False)

    container_missing_ids = fields.One2many("stock.container.missing","container_valuation_id","Missing Stock Containers")

    warehouse_missing_ids = fields.One2many("stock.warehouse.container.missing","stock_valuation_id","Missing Warehouse Stock Containers")

    project_container_missing_ids = fields.One2many("project.stock.container.missing","project_container_valuation_id","Missing Donar Containers")

    project_warehouse_missing_ids = fields.One2many("stock.warehouse.project.container.missing","project_stock_valuation_id","Missing Warehouse Donar Containers")

    select_all = fields.Boolean(string="Select All", default=False)

    select_all_warehouse = fields.Boolean(string="Select All", default=False)

    select_all_donar = fields.Boolean(string="Select All", default=False)

    select_all_warehouse_donar = fields.Boolean(string="Select All", default=False)

    message = fields.Char()
    
    
    # @api.model
    # def default_get(self, fields_name):
    #     res = super(StockContainerValuation, self).default_get(fields_name)

    #     stock_containers = self.env['stock.container'].sudo().search([('state','!=','done')])

    #     container_ids = stock_containers.ids
        
    #     res.update({
    #         'picking_container_ids': [(6, False, container_ids)]
    #     })
    #     return res
    

    @api.onchange("select_all")
    def onchange_select_all(self):
        if self.select_all:
            for missing_id in self.container_missing_ids:
                missing_id.select_field = True
        else:
            for missing_id in self.container_missing_ids:
                missing_id.select_field = False
    
    @api.onchange("select_all_warehouse")
    def onchange_select_all_warehouse(self):
        if self.select_all_warehouse:
            for missing_id in self.warehouse_missing_ids:
                missing_id.select_field = True
        else:
            for missing_id in self.warehouse_missing_ids:
                missing_id.select_field = False
    
    @api.onchange("select_all_donar")
    def onchange_select_all(self):
        if self.select_all_donar:
            for missing_id in self.project_container_missing_ids:
                missing_id.select_field = True
        else:
            for missing_id in self.project_container_missing_ids:
                missing_id.select_field = False
    
    @api.onchange("select_all_warehouse_donar")
    def onchange_select_all_warehouse(self):
        if self.select_all_warehouse_donar:
            for missing_id in self.project_warehouse_missing_ids:
                missing_id.select_field = True
        else:
            for missing_id in self.project_warehouse_missing_ids:
                missing_id.select_field = False

    
    def check_missing_containers(self):
        if not (self.loaded_container_ids or self.loaded_donar_container_ids):
            raise UserError("Please select containers")
        
        picking_container_ids = self.env['stock.container'].sudo().search([('state','!=','done')])
        system_ids = set(picking_container_ids.ids)
        loaded_ids = set(self.loaded_container_ids.ids)
        missing_ids = list(system_ids - loaded_ids)

        warehouse_done_ids = list(loaded_ids - system_ids)

        self.container_missing_ids = [(5, _, _)]
        if missing_ids:
            self.show_missing_containers = True
            self.message = ""
            missing_lines = []
            for missing_id in missing_ids:
                data = (0,0,{
                    'name': missing_id,
                    
                })
                missing_lines.append(data)
            self.container_missing_ids = missing_lines
        
        self.warehouse_missing_ids = [(5, _, _)]

        if warehouse_done_ids:
            self.warehouse_done_containers = True

            missing_lines = []
            for missing_id in warehouse_done_ids:
                data = (0,0,{
                    'name': missing_id,
                    
                })
                missing_lines.append(data)
            self.warehouse_missing_ids = missing_lines
        

        picking_donar_container_ids = self.env['project.container'].sudo().search([('state','not in',('new','close','cancel')),('project_id','!=',False)])
        system_ids = set(picking_donar_container_ids.ids)
        loaded_ids = set(self.loaded_donar_container_ids.ids)
        missing_ids = list(system_ids - loaded_ids)

        warehouse_done_ids = list(loaded_ids - system_ids)

        self.project_container_missing_ids = [(5, _, _)]
        if missing_ids:
            self.show_missing_donar_containers = True
            self.message = ""
            missing_lines = []
            for missing_id in missing_ids:
                data = (0,0,{
                    'name': missing_id,
                    
                })
                missing_lines.append(data)
            self.project_container_missing_ids = missing_lines
        
        self.project_warehouse_missing_ids = [(5, _, _)]

        if warehouse_done_ids:
            self.warehouse_done_donar_containers = True

            missing_lines = []
            for missing_id in warehouse_done_ids:
                data = (0,0,{
                    'name': missing_id,
                    
                })
                missing_lines.append(data)
            self.project_warehouse_missing_ids = missing_lines

        
        if not(self.container_missing_ids or self.warehouse_missing_ids or self.project_container_missing_ids or self.project_warehouse_missing_ids):
       
            self.message = "Containers Up To Date"
           
        self.select_all = False
        self.select_all_warehouse = False
        self.select_all_donar = False
        self.select_all_warehouse_donar = False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.container.valuation',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'name': 'Stock Container Valuation'
        }


    def update_to_done_stock_container(self):

        for missing_id in self.container_missing_ids.filtered(lambda l: l.select_field==True):
            missing_id.name.state = "done"
            missing_id.select_field = False

        self.select_all = False
        self.select_all_warehouse = False
        self.select_all_donar = False
        self.select_all_warehouse_donar = False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.container.valuation',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'name': 'Stock Container Valuation'
        }

    def update_to_open1(self):

        for missing_id in self.container_missing_ids.filtered(lambda l: l.select_field==True):
            missing_id.name.state = "open"
            missing_id.select_field = False
        self.select_all = False
        self.select_all_warehouse = False
        self.select_all_donar = False
        self.select_all_warehouse_donar = False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.container.valuation',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'name': 'Stock Container Valuation'
        }

    def update_to_open(self):

        for missing_id in self.warehouse_missing_ids.filtered(lambda l: l.select_field==True):
            missing_id.name.state = "open"
            missing_id.select_field = False
        self.select_all = False
        self.select_all_warehouse = False
        self.select_all_donar = False
        self.select_all_warehouse_donar = False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.container.valuation',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'name': 'Stock Container Valuation'
        }

    def update_to_sale1(self):

        for missing_id in self.container_missing_ids.filtered(lambda l: l.select_field==True):
            if missing_id.name.state!="to_be_sold":
                missing_id.name.close_container()
            missing_id.select_field = False
        self.select_all = False
        self.select_all_warehouse = False
        self.select_all_donar = False
        self.select_all_warehouse_donar = False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.container.valuation',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'name': 'Stock Container Valuation'
        }

    def update_to_sale(self):

        for missing_id in self.warehouse_missing_ids.filtered(lambda l: l.select_field==True):
            if missing_id.name.state!="to_be_sold":
                missing_id.name.close_container()
            missing_id.select_field = False
        self.select_all = False
        self.select_all_warehouse = False
        self.select_all_donar = False
        self.select_all_warehouse_donar = False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.container.valuation',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'name': 'Stock Container Valuation'
        }
    
    def update_to_confirm_donar(self):

        for missing_id in self.project_container_missing_ids.filtered(lambda l: l.select_field==True):
            project_container = missing_id.name

            if project_container.state == "done":
                # update stock

                if project_container.location_id:
                    stock_quant = self.env['stock.quant'].sudo().search([('product_id','=',project_container.sub_product_id.id),('location_id','=',project_container.location_id.id)],limit=1)

                    if stock_quant:

                        if stock_quant.product_uom_id.name == 'Tonne' or stock_quant.product_uom_id.name == 'tonne':
                            gross_weight = project_container.gross_weight/1000
                        else:
                            gross_weight = project_container.gross_weight

                        stock_quant.quantity = stock_quant.quantity - gross_weight
                        project_container.state = "confirmed"
                        missing_id.select_field = False
                        break
            else:
                project_container.state = "confirmed"
                missing_id.select_field = False
                
        self.select_all = False
        self.select_all_warehouse = False
        self.select_all_donar = False
        self.select_all_warehouse_donar = False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.container.valuation',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'name': 'Stock Container Valuation'
        }

    
    def update_to_confirm_warehouse_donar(self):

        for missing_id in self.project_warehouse_missing_ids.filtered(lambda l: l.select_field==True):
            project_container = missing_id.name

            if project_container.state == "close":
                # update stock

                if project_container.location_id:
                    stock_quant = self.env['stock.quant'].sudo().search([('product_id','=',project_container.sub_product_id.id),('location_id','=',project_container.location_id.id)],limit=1)

                    if stock_quant:

                        if stock_quant.product_uom_id.name == 'Tonne' or stock_quant.product_uom_id.name == 'tonne':
                            gross_weight = project_container.gross_weight/1000
                        else:
                            gross_weight = project_container.gross_weight

                        stock_quant.quantity = stock_quant.quantity - gross_weight
                        project_container.state = "confirmed"
                        missing_id.select_field = False
                        break
                
        self.select_all = False
        self.select_all_warehouse = False
        self.select_all_donar = False
        self.select_all_warehouse_donar = False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.container.valuation',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'name': 'Stock Container Valuation'
        }
    
    def update_to_close_donar(self):

        for missing_id in self.project_container_missing_ids.filtered(lambda l: l.select_field==True):

            if missing_id.name.state!="close":
                project_container = missing_id.name

                worker_id = self.env['hr.employee'].sudo().search([('name','=','Production Employee'),('is_worker','=',True)],limit=1)
                if not worker_id:
                    worker_id = self.env['hr.employee'].sudo().create({
                        'name': 'Production Employee',
                        'is_worker': True,
                    })

                # update timer and worker
                if not (project_container.total_time):
                    project_container.total_time = 20.0
                if not (project_container.manual_time):
                    project_container.manual_time = 20.0
                if not project_container.operator_ids:
                    project_container.operator_ids = [(6, False, worker_id.ids)]

                # create stock container
                            
                location = self.env['stock.location'].sudo().search([('company_id','=',project_container.company_id.id),('is_stock_location','=',True)],limit=1)

                
                stock_container = self.env['stock.container'].sudo().search([('source_container_id','=',project_container.id)],limit=1)

                if not stock_container:
                    data = {
                        'content_type_id': project_container.sub_product_id.id,
                        'container_type_id': project_container.container_type_id.id,
                        'location_id': location.id if location else False,
                        'related_company_id': project_container.company_id.id,
                        'absolute_tare_weight': project_container.extra_tare,
                        'tare_weight': project_container.container_type_id.tare_weight,
                        'gross_weight': project_container.gross_weight,
                        'max_weight': project_container.gross_weight,
                        'source_container_id': project_container.id,
                    }
                    stock_container = self.env['stock.container'].create(data)

                    # create fractions
                
                    fraction_id = self.env["project.fraction"].create({
                        'worker_id' : project_container.operator_ids[0].id if project_container.operator_ids else worker_id.id,
                        'main_product_id': project_container.main_product_id.id,
                        'sub_product_id': project_container.sub_product_id.id,
                        'recipient_container_id': stock_container.id,
                        'fraction_by':'weight',
                        'container_weight': project_container.gross_weight,
                        'fraction_weight': project_container.gross_weight,
                        'company_id': project_container.company_id.id,
                        'source_container_id': project_container.id,
                        'project_id': project_container.project_id.id,
                    })


                    fraction_id.close_fraction()
                else:
                    fraction_ids = self.env["project.fraction"].sudo().search([('recipient_container_id','=',stock_container.id)])

                    if fraction_ids:
                        total_fraction_weight = 0.00
                        for fraction in fraction_ids:
                            total_fraction_weight+=total_fraction_weight+fraction.fraction_weight
                            if fraction.state=="new":
                                fraction_id.close_fraction()
                                                
                        if(round(total_fraction_weight,2)<round(project_container.gross_weight,2)):
                            remaining_weight = project_container.gross_weight - total_fraction_weight

                            fraction_id = self.env["project.fraction"].create({
                                'worker_id' : project_container.operator_ids[0].id if project_container.operator_ids else worker_id.id,
                                'main_product_id': project_container.main_product_id.id,
                                'sub_product_id': project_container.sub_product_id.id,
                                'recipient_container_id': stock_container.id,
                                'fraction_by':'weight',
                                'container_weight': remaining_weight,
                                'fraction_weight': remaining_weight,
                                'company_id': project_container.company_id.id,
                                'source_container_id': project_container.id,
                                'project_id': project_container.project_id.id,
                            })

                            fraction_id.close_fraction()
                    else:
                        # create fractions
                
                        fraction_id = self.env["project.fraction"].create({
                            'worker_id' : project_container.operator_ids[0].id if project_container.operator_ids else worker_id.id,
                            'main_product_id': project_container.main_product_id.id,
                            'sub_product_id': project_container.sub_product_id.id,
                            'recipient_container_id': stock_container.id,
                            'fraction_by':'weight',
                            'container_weight': project_container.gross_weight,
                            'fraction_weight': project_container.gross_weight,
                            'company_id': project_container.company_id.id,
                            'source_container_id': project_container.id,
                            'project_id': project_container.project_id.id,
                        })

                        fraction_id.close_fraction()

                project_container.set_to_close()

                missing_id.select_field = False

        self.select_all = False
        self.select_all_warehouse = False
        self.select_all_donar = False
        self.select_all_warehouse_donar = False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.container.valuation',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'name': 'Stock Container Valuation'
        }


    def update_to_close_warehouse_donar(self):

        for missing_id in self.project_warehouse_missing_ids.filtered(lambda l: l.select_field==True):
            if missing_id.name.state!="close":
                project_container = missing_id.name
                worker_id = self.env['hr.employee'].sudo().search([('name','=','Production Employee'),('is_worker','=',True)],limit=1)
                if not worker_id:
                    worker_id = self.env['hr.employee'].sudo().create({
                        'name': 'Production Employee',
                        'is_worker': True,
                    })

                # update timer and worker
                if not (project_container.total_time):
                    project_container.total_time = 20.0
                if not (project_container.manual_time):
                    project_container.manual_time = 20.0
                if not project_container.operator_ids:
                    project_container.operator_ids = [(6, False, worker_id.ids)]

                # create stock container
                            
                location = self.env['stock.location'].sudo().search([('company_id','=',project_container.company_id.id),('is_stock_location','=',True)],limit=1)

                
                stock_container = self.env['stock.container'].sudo().search([('source_container_id','=',project_container.id)],limit=1)

                if not stock_container:
                    data = {
                        'content_type_id': project_container.sub_product_id.id,
                        'container_type_id': project_container.container_type_id.id,
                        'location_id': location.id if location else False,
                        'related_company_id': project_container.company_id.id,
                        'absolute_tare_weight': project_container.extra_tare,
                        'tare_weight': project_container.container_type_id.tare_weight,
                        'gross_weight': project_container.gross_weight,
                        'source_container_id': project_container.id,
                    }
                    stock_container = self.env['stock.container'].create(data)

                    # create fractions
                
                    fraction_id = self.env["project.fraction"].create({
                        'worker_id' : project_container.operator_ids[0].id if project_container.operator_ids else worker_id.id,
                        'main_product_id': project_container.main_product_id.id,
                        'sub_product_id': project_container.sub_product_id.id,
                        'recipient_container_id': stock_container.id,
                        'fraction_by':'weight',
                        'container_weight': project_container.gross_weight,
                        'fraction_weight': project_container.gross_weight,
                        'company_id': project_container.company_id.id,
                        'source_container_id': project_container.id,
                        'project_id': project_container.project_id.id,
                    })

                    fraction_id.close_fraction()
                else:
                    fraction_ids = self.env["project.fraction"].sudo().search([('recipient_container_id','=',stock_container.id)])

                    if fraction_ids:
                        total_fraction_weight = 0.00
                        for fraction in fraction_ids:
                            total_fraction_weight+=total_fraction_weight+fraction.fraction_weight
                            if fraction.state=="new":
                                fraction_id.close_fraction()
                        
                        if(round(total_fraction_weight,2)<round(project_container.gross_weight,2)):
                            remaining_weight = project_container.gross_weight - total_fraction_weight

                            fraction_id = self.env["project.fraction"].create({
                                'worker_id' : project_container.operator_ids[0].id if project_container.operator_ids else worker_id.id,
                                'main_product_id': project_container.main_product_id.id,
                                'sub_product_id': project_container.sub_product_id.id,
                                'recipient_container_id': stock_container.id,
                                'fraction_by':'weight',
                                'container_weight': remaining_weight,
                                'fraction_weight': remaining_weight,
                                'company_id': project_container.company_id.id,
                                'source_container_id': project_container.id,
                                'project_id': project_container.project_id.id,
                            })

                            fraction_id.close_fraction()
                    else:
                        # create fractions
                
                        fraction_id = self.env["project.fraction"].create({
                            'worker_id' : project_container.operator_ids[0].id if project_container.operator_ids else worker_id.id,
                            'main_product_id': project_container.main_product_id.id,
                            'sub_product_id': project_container.sub_product_id.id,
                            'recipient_container_id': stock_container.id,
                            'fraction_by':'weight',
                            'container_weight': project_container.gross_weight,
                            'fraction_weight': project_container.gross_weight,
                            'company_id': project_container.company_id.id,
                            'source_container_id': project_container.id,
                            'project_id': project_container.project_id.id,
                        })

                        fraction_id.close_fraction()

                project_container.set_to_close()

                missing_id.select_field = False
        self.select_all = False
        self.select_all_warehouse = False
        self.select_all_donar = False
        self.select_all_warehouse_donar = False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.container.valuation',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'name': 'Stock Container Valuation'
        }

    
    # def complete_process(self):
    #     for missing_id in self.container_missing_ids.filtered(lambda l: l.select_field==True):
    #         missing_id.name.state = "done"
    #         missing_id.select_field = False

    #     if self.container_missing_ids.filtered(lambda l: l.select_field==True):
    #         self.select_all = False
    #         self.select_all_warehouse = False


    def stock_container_tree_view(self):
        return {
            'name': "Missing Stock Container Details",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form,pivot',
            'res_model': 'stock.container',
            'target': 'current',
            'domain': [('id', '=', [x.name.id for x in self.container_missing_ids] )],
            # 'context': {
            #     'search_default_group_type': True,
            # }
        }
    
    def project_container_tree_view(self):
        return {
            'name': "Missing Donar Container Details",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form,pivot',
            'res_model': 'project.container',
            'target': 'current',
            'domain': [('id', '=', [x.name.id for x in self.project_container_missing_ids] )],
            # 'context': {
            #     'search_default_group_type': True,
            # }
        }

class MissingStockContainers(models.TransientModel):
    _name = 'stock.container.missing'

    container_valuation_id = fields.Many2one(comodel_name="stock.container.valuation")

    select_field = fields.Boolean(string="Select", default=False)

    name = fields.Many2one(comodel_name="stock.container", string="Container")

    content_type = fields.Many2one(comodel_name="product.product", string="Content Type", related="name.content_type_id")

    container_type = fields.Many2one(comodel_name="container.type", string="Container Type", related="name.container_type_id")

    project_id = fields.Many2one(comodel_name="project.entries", string="Project ID", related="name.project_id")

    picking_id = fields.Many2one(comodel_name="stock.picking", string="Shipment ID", related="name.picking_id")

    state = fields.Selection([('open', 'Open'), ('to_be_sold', 'Closed/To Sale'), ('lead', 'Lead/Opportunity'),('second_process', 'Moved to Second Process'), ('sold', 'Sold'), ('done', "Done")],string="State", related="name.state")


class WarehouseMissingStockContainers(models.TransientModel):
    _name = 'stock.warehouse.container.missing'

    stock_valuation_id = fields.Many2one(comodel_name="stock.container.valuation")

    select_field = fields.Boolean(string="Select", default=False)

    name = fields.Many2one(comodel_name="stock.container", string="Container")

    content_type = fields.Many2one(comodel_name="product.product", string="Content Type", related="name.content_type_id")

    container_type = fields.Many2one(comodel_name="container.type", string="Container Type", related="name.container_type_id")

    project_id = fields.Many2one(comodel_name="project.entries", string="Project ID", related="name.project_id")

    picking_id = fields.Many2one(comodel_name="stock.picking", string="Shipment ID", related="name.picking_id")


    state = fields.Selection([('open', 'Open'), ('to_be_sold', 'Closed/To Sale'), ('lead', 'Lead/Opportunity'),('second_process', 'Moved to Second Process'), ('sold', 'Sold'), ('done', "Done")],string="State", related="name.state")


class MissingProjectStockContainers(models.TransientModel):
    _name = 'project.stock.container.missing'

    project_container_valuation_id = fields.Many2one(comodel_name="stock.container.valuation")

    select_field = fields.Boolean(string="Select", default=False)

    name = fields.Many2one(comodel_name="project.container", string="Container")

    partner_ref = fields.Char('Vendor Reference', related="name.partner_ref")
    project_id = fields.Many2one("project.entries", string="Project ID", related="name.project_id")
    
    picking_id = fields.Many2one("stock.picking", string="Shipment ID", related="name.picking_id")

    container_type_id = fields.Many2one("container.type", string="Container Type", related="name.container_type_id")
    
    content_type = fields.Many2one("waste.type", string="Type of Waste", related="name.content_type")
    
    state = fields.Selection(
        [('new', 'New'), ('confirmed', 'Confirmed'), ('planned', 'Planned'), ('in_progress', 'Production'),
         ('non_conformity', 'Non Conformity'), ('dangerous', 'Quarantine'), ('close', 'Closed'), ('return', 'Return'),('cancel', 'Cancelled')],
        string="Status", related="name.state")


class WarehouseMissingProjectStockContainers(models.TransientModel):
    _name = 'stock.warehouse.project.container.missing'

    project_stock_valuation_id = fields.Many2one(comodel_name="stock.container.valuation")

    select_field = fields.Boolean(string="Select", default=False)

    name = fields.Many2one(comodel_name="project.container", string="Container")

    partner_ref = fields.Char('Vendor Reference', related="name.partner_ref")
    project_id = fields.Many2one("project.entries", string="Project ID", related="name.project_id")
    
    picking_id = fields.Many2one("stock.picking", string="Shipment ID", related="name.picking_id")

    container_type_id = fields.Many2one("container.type", string="Container Type", related="name.container_type_id")
    
    content_type = fields.Many2one("waste.type", string="Type of Waste", related="name.content_type")
    
    state = fields.Selection(
        [('new', 'New'), ('confirmed', 'Confirmed'), ('planned', 'Planned'), ('in_progress', 'Production'),
         ('non_conformity', 'Non Conformity'), ('dangerous', 'Quarantine'), ('close', 'Closed'), ('return', 'Return'),('cancel', 'Cancelled')],
        string="Status", related="name.state")

