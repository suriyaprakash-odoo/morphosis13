from odoo import api, fields, models,_
from odoo.exceptions import Warning,UserError
import math

class CloseContainerWizard(models.TransientModel):
    _name = 'close.container.wizard'

    # container_ids = fields.Many2many('project.container', string='Selected Containers',domain="[('state', '=', 'in_progress')]")
    contractor_rate = fields.Boolean("Contractor Rate")
    ea_rate = fields.Boolean("EA Rate")
    standard_rate = fields.Boolean("Standard Rate",default=True)
    weight_ok = fields.Boolean("Weight OK", default=True)
    quality_ok = fields.Boolean("Quality OK",default=True )
    release_to_stock = fields.Boolean("Release To Stock")
    second_process = fields.Boolean('Second Process')
    container_line = fields.One2many("close.container.line","wizard_id",string="Containers")
    select_all = fields.Boolean("Select All")
    select_all_for_process = fields.Boolean("Select All")
    # returnable_container = fields.Boolean("Reusable Container")
    lot_ids = fields.One2many('container.lot.line','wizard_id',string="LOT/Serial")

    def action_close_container(self):
        for container in self.container_line:

            if math.ceil(container.container_id.gross_weight)<=0:
                raise Warning("Container Id: '{}' gross weight should not be negative/zero".format(container.container_id.name))

            if container.close_container:
                container.container_id.contractor_rate = self.contractor_rate
                container.container_id.ea_rate = self.ea_rate
                container.container_id.standard_rate = self.standard_rate
                if container.container_id.project_id.project_type == 'reuse':
                    fraction_ids = self.env["project.fraction"].search([('source_container_id', '=', container.container_id.id)])
                    fraction_lst=[]
                    for fraction in fraction_ids:
                        if fraction.worker_id and fraction.recipient_container_id and (fraction.number_of_pieces or fraction.fraction_weight):
                            fraction.close_fraction()
                        else:
                            fraction_lst.append(fraction.name)
                    if fraction_lst:
                        raise UserError(_("Please add all the values in Fraction '%s' to process further") % str(fraction_lst))
                    else:
                        container.container_id.set_to_close()
                else:
                    container.container_id.set_to_close()

        if  self.lot_ids:
            for lot in self.lot_ids:
                if lot.close:
                    picking_type = self.env["stock.picking.type"].search([('code', '=', 'incoming'), ('company_id', '=', lot.lot_id.company_id.id)], limit=1)
                    vals = {
                        'partner_id': lot.container_id.partner_id.id,
                        'location_id': lot.container_id.partner_id.property_stock_customer.id,
                        'picking_type_id': picking_type.id,
                        'move_type': 'direct',
                        'location_dest_id': lot.dest_location_id.id,
                        # 'move_ids_without_package': [],
                    }
                    picking_id = self.env["stock.picking"].create(vals)

                    # list_items = []
                    stock_move = self.env["stock.move"].create({
                        'product_id': lot.product_id.id,
                        'product_uom_qty': 1,
                        'reserved_availability': 1,
                        # 'quantity_done': 1,
                        'name': lot.product_id.name,
                        'product_uom': lot.product_id.uom_id.id,
                        'location_id': lot.container_id.partner_id.property_stock_customer.id,
                        'location_dest_id': lot.dest_location_id.id,
                        'picking_id':picking_id.id
                    })
                    lot.lot_id.reuse_barcode = lot.reuse_barcode

                    move_line = self.env['stock.move.line'].create({
                        'move_id': stock_move.id,
                        'lot_id': lot.lot_id.id,
                        'product_uom_qty': 1,
                        'qty_done': 1,
                        'product_id': stock_move.product_id.id,
                        'product_uom_id': stock_move.product_id.uom_id.id,
                        'location_id': lot.container_id.partner_id.property_stock_customer.id,
                        'location_dest_id': lot.dest_location_id.id,
                        'picking_id':picking_id.id
                    })
                    print (move_line,"----------------------")

                    picking_id.action_done()

    @api.onchange('select_all')
    def _onchange_select_all(self):
        if self.container_line:
            if self.select_all:
                for line in self.container_line:
                    line.close_container = True
                for line in self.lot_ids:
                    line.close = True
            else:
                for line in self.container_line:
                    line.close_container = False
                for line in self.lot_ids:
                    line.close = False

            # self.create(self)
    # @api.onchange('returnable_container')
    # def _onchange_returnable_container(self):
    #     if self.returnable_container:
    #         if self.lot_ids:
    #             self.lot_ids.unlink()
    #             self.returnable_container = True
    #         list_items = []
    #         for line in self.container_line:
    #             if line.container_id.returnable_container:
    #                 list_items.append((0, 0, {
    #                     'container_id': line.container_id.id,
    #                     'location_id': line.container_id.location_id.id,
    #                 }))
    #         self.lot_ids = list_items


class ContainerLines(models.TransientModel):
    _name = 'close.container.line'

    container_id = fields.Many2one("project.container",string="Container ID")
    primary_product = fields.Many2one("product.template",string="Primary Type")
    gross_weight = fields.Float("Container Net Weight(Kg)", digits=(12,4))
    net_weight = fields.Float("Fractions Net Weight(Kg)", digits=(12,4))
    close_container = fields.Boolean("Close?")
    # second_process = fields.Boolean("Second Process")
    wizard_id = fields.Many2one("close.container.wizard", string="wizard id")
    count = fields.Integer("Count")
    weight_difference = fields.Float("Weight Difference(Kg)")
    scrap_weight = fields.Float("Scrap Weight(Kg)")
    release_to_stock = fields.Boolean("Release to Stock",default=True)

class ContainerLotLines(models.TransientModel):
    _name = 'container.lot.line'

    lot_id = fields.Many2one("stock.production.lot", string="LOT/Serial")
    product_id = fields.Many2one("product.product", string="Product")
    close = fields.Boolean("Release to Stock")
    wizard_id = fields.Many2one("close.container.wizard", string="wizard id")
    container_id = fields.Many2one("project.container", string="Container ID")
    location_id = fields.Many2one("stock.location", string="Location")
    dest_location_id = fields.Many2one("stock.location", string="Destination")
    reuse_barcode = fields.Char("Barcode")
    generate_barcode = fields.Boolean("Generate Barcode")

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.product_id = self.lot_id.product_id.id

    @api.onchange('generate_barcode')
    def _onchange_generate_barcode(self):
        if self.generate_barcode:
            self.reuse_barcode = self.env['ir.sequence'].next_by_code('reuse.barcode') or '/'
        else:
            self.reuse_barcode = ''