from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning
from datetime import datetime
import math

class LaboratoryReport(models.Model):
    _name = 'laboratory.report'

    name = fields.Char("Name")
    sent_date = fields.Date("Material sent date")
    partner_id = fields.Many2one("res.partner", string="Client")
    description = fields.Text("Description")
    received_date = fields.Date("Material received date")
    report_date = fields.Date("Report Date")
    user_id = fields.Many2one("res.users",string="Responsible")
    project_id = fields.Many2one("project.entries", string="Project")
    document_ids = fields.One2many('lab.documents', 'lab_id', string="Documents")
    sample_description = fields.Text(string="Déscription")
    metal_type = fields.Selection([('cendres', 'Cendres'), ('boue', 'Boue'), ('liquide', 'Liquide'), ('poudre', 'Poudre'), ('solides', 'Solides')], string="Classe")
    requested_date = fields.Date(string="Date demandée")
    actual_report_date = fields.Date(string="Date du Rapport")


    silver = fields.Boolean("Silver")
    gold = fields.Boolean("Gold")
    palladium = fields.Boolean("Palladium")
    platinum = fields.Boolean("Platinum")
    copper = fields.Boolean("Copper")
    rhodium = fields.Boolean("Rhodium")
    ruthenium = fields.Boolean("Ruthenium")
    iridium = fields.Boolean("iridium")

    silver_analysis_ids = fields.One2many("silver.analysis.result", "laboratory_id", string="Silver Analysis Result")

    gold_analysis_ids = fields.One2many("gold.analysis.result", "laboratory_id", string="Gold Analysis Result")

    palladium_analysis_ids = fields.One2many("palladium.analysis.result", "laboratory_id", string="Palladium Analysis Result")

    platinum_analysis_ids = fields.One2many("platinum.analysis.result", "laboratory_id", string="Platinum Analysis Result")

    copper_analysis_ids = fields.One2many("copper.analysis.result", "laboratory_id", string="Copper Analysis Result")

    rhodium_analysis_ids = fields.One2many("rhodium.analysis.result", "laboratory_id", string="Rhodium Analysis Result")

    ruthenium_analysis_ids = fields.One2many("ruthenium.analysis.result", "laboratory_id", string="Ruthenium Analysis Result")

    iridium_analysis_ids = fields.One2many("iridium.analysis.result", "laboratory_id", string="Iridium Analysis Result")

    

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('lab.report.seq') or '/'
        res = super(LaboratoryReport, self).create(vals)
        if res.partner_id.short_code:
            res.name =  vals['name'] + '/' + res.partner_id.short_code
        if res.document_ids:
            for line in res.document_ids:
                docs = self.env["project.documents"].search([('file_char','=',line.file_char),('project_id','=',res.project_id.id)])
                if not docs:
                    self.env["project.documents"].create({'project_doc':line.project_doc, 'name':line.name,'file_char':line.file_char,'project_id':res.project_id.id})
        return res


    def write(self, values):
        res = super(LaboratoryReport, self).write(values)
        if self.document_ids:
            for line in self.document_ids:
                docs = self.env["project.documents"].search([('file_char','=',line.file_char),('project_id','=',self.project_id.id)])
                if not docs:
                    self.env["project.documents"].create({'project_doc':line.project_doc, 'name':line.name,'file_char':line.file_char,'project_id':self.project_id.id})
        return res

class LaboratoryReportDocument(models.Model):
    _name = 'lab.documents'

    name = fields.Char("Description")
    project_doc = fields.Binary("Document")
    file_char = fields.Char("File Name")
    lab_id = fields.Many2one("laboratory.report", string="Report ID")

class RefiningContainersInherit(models.Model):
    _inherit = 'refining.containers'

class SilverAnalysisResult(models.Model):
    _name = "silver.analysis.result"
    _description = "Silver Analysis Result"

    laboratory_id = fields.Many2one(comodel_name='laboratory.report', string="Laboratory Report")

    project_id = fields.Many2one(comodel_name='project.entries', string="Project Entries", related="laboratory_id.project_id")

    container_id = fields.Many2one(comodel_name="refining.containers", string="Container")

    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')

    quantity = fields.Float(string="Taille de l'échantillon", digits=(16,4))
    estimated_result = fields.Float(string="Estimated Result", digits=(16,4))
    actual_result = fields.Float(string="Actual Result", digits=(16,4))

    @api.model
    def create(self, vals):

        if math.ceil(vals.get('quantity'))==0:
            raise Warning("Please add the quantity in silver analysis")

        if math.ceil(vals.get('estimated_result'))==0:
            raise Warning("Please add the Estimated Result in silver analysis")
        
        if math.ceil(vals.get('actual_result'))==0:
            raise Warning("Please add the Actual Result in silver analysis")

        res = super(SilverAnalysisResult, self).create(vals)

        container_id = self.env['project.container'].search([('name','=',res.container_id.name)],limit=1)

        if not container_id:
            raise Warning("Please make sure the selected container is created and mapped in silver treatment.")

        refining_obj = self.env['silver.refining.cost'].search([('sample_ct_id','=',container_id.id),('silver_cost_id','=',res.project_id.id)])
        for refining_line in refining_obj:
            if refining_line.refining_sample_id == res.refining_sample_id:
                refining_line.analysis_for_certification = res.actual_result
            elif refining_line.refining_sample_id_1 == res.refining_sample_id:
                refining_line.reference_sample_analysis = res.actual_result
            elif refining_line.refining_sample_id_2 == res.refining_sample_id:
                refining_line.actual_result = res.actual_result
            else:
                raise Warning("Please make sure the selected sample is added in Silver treatment costs")  
        # get_refining_cost = self.env['silver.refining.cost'].search([('sample_ct_id','=',container_id.id),('silver_cost_id','=',res.project_id.id)],limit=1)
        # if not get_refining_cost:
        #     raise Warning("Please make sure silver treatment costs have these selected container")
        # get_refining_cost.reference_sample_analysis = res.actual_result

        return res
    
    def write(self, vals):
        res = super(SilverAnalysisResult, self).write(vals)

        if math.ceil(self.quantity)==0:
            raise Warning("Please add the quantity in silver analysis")

        if math.ceil(self.estimated_result)==0:
            raise Warning("Please add the Estimated Result in silver analysis")
        
        if math.ceil(self.actual_result)==0:
            raise Warning("Please add the Actual Result in silver analysis")

        if vals.get('actual_result'):
            container_id = self.env['project.container'].search([('name','=',self.container_id.name)],limit=1)

            if not container_id:
                raise Warning("Please make sure the selected container is updated in silver treatment.")

            refining_obj = self.env['silver.refining.cost'].search([('sample_ct_id','=',container_id.id),('silver_cost_id','=',self.project_id.id)])
            for refining_line in refining_obj:
                if refining_line.refining_sample_id == self.refining_sample_id:
                    refining_line.analysis_for_certification = vals.get('actual_result')
                elif refining_line.refining_sample_id_1 == self.refining_sample_id:
                    refining_line.reference_sample_analysis = vals.get('actual_result')
                elif refining_line.refining_sample_id_2 == self.refining_sample_id:
                    refining_line.actual_result = vals.get('actual_result')
                else:
                    raise Warning("Please make sure the selected sample is added in Silver treatment costs")
            # get_refining_cost = self.env['silver.refining.cost'].search([('sample_ct_id','=',container_id.id),('silver_cost_id','=',self.project_id.id)],limit=1)
            # if not get_refining_cost:
            #     raise Warning("Please make sure silver treatment costs have these selected container")
            # get_refining_cost.reference_sample_analysis = vals.get('actual_result')

        return res



class GoldAnalysisResult(models.Model):
    _name = "gold.analysis.result"
    _description = "Gold Analysis Result"

    laboratory_id = fields.Many2one(comodel_name='laboratory.report', string="Laboratory Report")

    project_id = fields.Many2one(comodel_name='project.entries', string="Project Entries", related="laboratory_id.project_id")

    container_id = fields.Many2one(comodel_name="refining.containers", string="Container")

    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')

    quantity = fields.Float(string="Taille de l'échantillon", digits=(16,4))
    estimated_result = fields.Float(string="Estimated Result", digits=(16,4))
    actual_result = fields.Float(string="Actual Result", digits=(16,4))


    @api.model
    def create(self, vals):

        if math.ceil(vals.get('quantity'))==0:
            raise Warning("Please add the quantity in gold analysis")

        if math.ceil(vals.get('estimated_result'))==0:
            raise Warning("Please add the Estimated Result in gold analysis")
        
        if math.ceil(vals.get('actual_result'))==0:
            raise Warning("Please add the Actual Result in gold analysis")

        res = super(GoldAnalysisResult, self).create(vals)

        container_id = self.env['project.container'].search([('name','=',res.container_id.name)],limit=1)

        if not container_id:
            raise Warning("Please make sure the selected container is updated in gold treatment.")

        refining_obj = self.env['gold.refining.cost'].search([('sample_ct_id','=',container_id.id),('gold_cost_id','=',res.project_id.id)])
        for refining_line in refining_obj:
            if refining_line.refining_sample_id == res.refining_sample_id:
                refining_line.analysis_for_certification = res.actual_result
            elif refining_line.refining_sample_id_1 == res.refining_sample_id:
                refining_line.reference_sample_analysis = res.actual_result
            elif refining_line.refining_sample_id_2 == res.refining_sample_id:
                refining_line.actual_result = res.actual_result
            else:
                raise Warning("Please make sure the selected sample is added in Gold treatment costs")
        # get_refining_cost = self.env['gold.refining.cost'].search([('sample_ct_id','=',container_id.id),('gold_cost_id','=',res.project_id.id)],limit=1)
        # if not get_refining_cost:
        #     raise Warning("Please make sure gold treatment costs have these selected container")
        # get_refining_cost.reference_sample_analysis = res.actual_result

        return res
    
    def write(self, vals):
        res = super(GoldAnalysisResult, self).write(vals)

        if math.ceil(self.quantity)==0:
            raise Warning("Please add the quantity in gold analysis")

        if math.ceil(self.estimated_result)==0:
            raise Warning("Please add the Estimated Result in gold analysis")
        
        if math.ceil(self.actual_result)==0:
            raise Warning("Please add the Actual Result in gold analysis")

        if vals.get('actual_result'):
            container_id = self.env['project.container'].search([('name','=',self.container_id.name)],limit=1)

            if not container_id:
                raise Warning("Please make sure the selected container is updated in gold treatment.")

            refining_obj = self.env['gold.refining.cost'].search([('sample_ct_id','=',container_id.id),('gold_cost_id','=',self.project_id.id)])
            for refining_line in refining_obj:
                if refining_line.refining_sample_id == self.refining_sample_id:
                    refining_line.analysis_for_certification = vals.get('actual_result')
                elif refining_line.refining_sample_id_1 == self.refining_sample_id:
                    refining_line.reference_sample_analysis = vals.get('actual_result')
                elif refining_line.refining_sample_id_2 == self.refining_sample_id:
                    refining_line.actual_result = vals.get('actual_result')
                else:
                    raise Warning("Please make sure the selected sample is added in Gold treatment costs")

            # get_refining_cost = self.env['gold.refining.cost'].search([('sample_ct_id','=',container_id.id),('gold_cost_id','=',self.project_id.id)],limit=1)
            # if not get_refining_cost:
            #     raise Warning("Please make sure gold treatment costs have these selected container")
            # get_refining_cost.reference_sample_analysis = vals.get('actual_result')

        return res


class PalladiumAnalysisResult(models.Model):
    _name = "palladium.analysis.result"
    _description = "Palladium Analysis Result"

    laboratory_id = fields.Many2one(comodel_name='laboratory.report', string="Laboratory Report")

    project_id = fields.Many2one(comodel_name='project.entries', string="Project Entries", related="laboratory_id.project_id")

    container_id = fields.Many2one(comodel_name="refining.containers", string="Container")

    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')

    quantity = fields.Float(string="Taille de l'échantillon", digits=(16,4))
    estimated_result = fields.Float(string="Estimated Result", digits=(16,4))
    actual_result = fields.Float(string="Actual Result", digits=(16,4))

    @api.model
    def create(self, vals):

        if math.ceil(vals.get('quantity'))==0:
            raise Warning("Please add the quantity in palladium analysis")

        if math.ceil(vals.get('estimated_result'))==0:
            raise Warning("Please add the Estimated Result in palladium analysis")
        
        if math.ceil(vals.get('actual_result'))==0:
            raise Warning("Please add the Actual Result in palladium analysis")


        res = super(PalladiumAnalysisResult, self).create(vals)

        container_id = self.env['project.container'].search([('name','=',res.container_id.name)],limit=1)

        if not container_id:
            raise Warning("Please make sure the selected container is updated in palladium treatment.")

        refining_obj = self.env['palladium.refining.cost'].search([('sample_ct_id','=',container_id.id),('palladium_cost_id','=',res.project_id.id)])
        for refining_line in refining_obj:
            if refining_line.refining_sample_id == res.refining_sample_id:
                refining_line.analysis_for_certification = res.actual_result
            elif refining_line.refining_sample_id_1 == res.refining_sample_id:
                refining_line.reference_sample_analysis = res.actual_result
            elif refining_line.refining_sample_id_2 == res.refining_sample_id:
                refining_line.actual_result = res.actual_result
            else:
                raise Warning("Please make sure the selected sample is added in Palladium treatment costs")

        # get_refining_cost = self.env['palladium.refining.cost'].search([('sample_ct_id','=',container_id.id),('palladium_cost_id','=',res.project_id.id)],limit=1)
        # if not get_refining_cost:
        #     raise Warning("Please make sure palladium treatment costs have these selected container")
        # get_refining_cost.reference_sample_analysis = res.actual_result

        return res
    
    def write(self, vals):
        res = super(PalladiumAnalysisResult, self).write(vals)

        if math.ceil(self.quantity)==0:
            raise Warning("Please add the quantity in palladium analysis")

        if math.ceil(self.estimated_result)==0:
            raise Warning("Please add the Estimated Result in palladium analysis")
        
        if math.ceil(self.actual_result)==0:
            raise Warning("Please add the Actual Result in palladium analysis")

        if vals.get('actual_result'):
            container_id = self.env['project.container'].search([('name','=',self.container_id.name)],limit=1)

            if not container_id:
                raise Warning("Please make sure the selected container is updated in palladium treatment.")

            refining_obj = self.env['palladium.refining.cost'].search([('sample_ct_id','=',container_id.id),('palladium_cost_id','=',self.project_id.id)])
            for refining_line in refining_obj:
                if refining_line.refining_sample_id == self.refining_sample_id:
                    refining_line.analysis_for_certification = vals.get('actual_result')
                elif refining_line.refining_sample_id_1 == self.refining_sample_id:
                    refining_line.reference_sample_analysis = vals.get('actual_result')
                elif refining_line.refining_sample_id_2 == self.refining_sample_id:
                    refining_line.actual_result = vals.get('actual_result')
                else:
                    raise Warning("Please make sure the selected sample is added in Palladium treatment costs")

            # get_refining_cost = self.env['palladium.refining.cost'].search([('sample_ct_id','=',container_id.id),('palladium_cost_id','=',self.project_id.id)],limit=1)
            # if not get_refining_cost:
            #     raise Warning("Please make sure palladium treatment costs have these selected container")
            # get_refining_cost.reference_sample_analysis = vals.get('actual_result')

        return res

class PlatinumAnalysisResult(models.Model):
    _name = "platinum.analysis.result"
    _description = "Platinum Analysis Result"

    laboratory_id = fields.Many2one(comodel_name='laboratory.report', string="Laboratory Report")

    project_id = fields.Many2one(comodel_name='project.entries', string="Project Entries", related="laboratory_id.project_id")

    container_id = fields.Many2one(comodel_name="refining.containers", string="Container")

    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')

    quantity = fields.Float(string="Taille de l'échantillon", digits=(16,4))
    estimated_result = fields.Float(string="Estimated Result", digits=(16,4))
    actual_result = fields.Float(string="Actual Result", digits=(16,4))

    @api.model
    def create(self, vals):

        if math.ceil(vals.get('quantity'))==0:
            raise Warning("Please add the quantity in platinum analysis")

        if math.ceil(vals.get('estimated_result'))==0:
            raise Warning("Please add the Estimated Result in platinum analysis")
        
        if math.ceil(vals.get('actual_result'))==0:
            raise Warning("Please add the Actual Result in paltinum analysis")

        res = super(PlatinumAnalysisResult, self).create(vals)

        container_id = self.env['project.container'].search([('name','=',res.container_id.name)],limit=1)

        if not container_id:
            raise Warning("Please make sure the selected container is updated in platinum treatment.")

        refining_obj = self.env['platinum.refining.cost'].search([('sample_ct_id','=',container_id.id),('platinum_cost_id','=',res.project_id.id)])
        for refining_line in refining_obj:
            if refining_line.refining_sample_id == res.refining_sample_id:
                refining_line.analysis_for_certification = res.actual_result
            elif refining_line.refining_sample_id_1 == res.refining_sample_id:
                refining_line.reference_sample_analysis = res.actual_result
            elif refining_line.refining_sample_id_2 == res.refining_sample_id:
                refining_line.actual_result = res.actual_result
            else:
                raise Warning("Please make sure the selected sample is added in Platinum treatment costs")

        # get_refining_cost = self.env['platinum.refining.cost'].search([('sample_ct_id','=',container_id.id),('platinum_cost_id','=',res.project_id.id)],limit=1)
        # if not get_refining_cost:
        #     raise Warning("Please make sure platinum treatment costs have these selected container")
        # get_refining_cost.reference_sample_analysis = res.actual_result

        return res
    
    def write(self, vals):
        res = super(PlatinumAnalysisResult, self).write(vals)

        if math.ceil(self.quantity)==0:
            raise Warning("Please add the quantity in platinum analysis")

        if math.ceil(self.estimated_result)==0:
            raise Warning("Please add the Estimated Result in platinum analysis")
        
        if math.ceil(self.actual_result)==0:
            raise Warning("Please add the Actual Result in paltinum analysis")

        if vals.get('actual_result'):
            container_id = self.env['project.container'].search([('name','=',self.container_id.name)],limit=1)

            if not container_id:
                raise Warning("Please make sure the selected container is updated in platinum treatment.")

            refining_obj = self.env['platinum.refining.cost'].search([('sample_ct_id','=',container_id.id),('platinum_cost_id','=',self.project_id.id)])
            for refining_line in refining_obj:
                if refining_line.refining_sample_id == self.refining_sample_id:
                    refining_line.analysis_for_certification = vals.get('actual_result')
                elif refining_line.refining_sample_id_1 == self.refining_sample_id:
                    refining_line.reference_sample_analysis = vals.get('actual_result')
                elif refining_line.refining_sample_id_2 == self.refining_sample_id:
                    refining_line.actual_result = vals.get('actual_result')
                else:
                    raise Warning("Please make sure the selected sample is added in Platinum treatment costs")

            # get_refining_cost = self.env['platinum.refining.cost'].search([('sample_ct_id','=',container_id.id),('platinum_cost_id','=',self.project_id.id)],limit=1)
            # if not get_refining_cost:
            #     raise Warning("Please make sure platinum treatment costs have these selected container")
            # get_refining_cost.reference_sample_analysis = vals.get('actual_result')

        return res


class CopperAnalysisResult(models.Model):
    _name = "copper.analysis.result"
    _description = "Copper Analysis Result"

    laboratory_id = fields.Many2one(comodel_name='laboratory.report', string="Laboratory Report")

    project_id = fields.Many2one(comodel_name='project.entries', string="Project Entries", related="laboratory_id.project_id")

    container_id = fields.Many2one(comodel_name="refining.containers", string="Container")

    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')

    quantity = fields.Float(string="Taille de l'échantillon", digits=(16,4))
    estimated_result = fields.Float(string="Estimated Result", digits=(16,4))
    actual_result = fields.Float(string="Actual Result", digits=(16,4))

    @api.model
    def create(self, vals):

        if math.ceil(vals.get('quantity'))==0:
            raise Warning("Please add the quantity in copper analysis")

        if math.ceil(vals.get('estimated_result'))==0:
            raise Warning("Please add the Estimated Result in copper analysis")
        
        if math.ceil(vals.get('actual_result'))==0:
            raise Warning("Please add the Actual Result in copper analysis")

        res = super(CopperAnalysisResult, self).create(vals)

        container_id = self.env['project.container'].search([('name','=',res.container_id.name)],limit=1)

        if not container_id:
            raise Warning("Please make sure the selected container is updated in copper treatment.")

        refining_obj = self.env['copper.refining.cost'].search([('sample_ct_id','=',container_id.id),('copper_cost_id','=',res.project_id.id)])
        for refining_line in refining_obj:
            if refining_line.refining_sample_id == res.refining_sample_id:
                refining_line.analysis_for_certification = res.actual_result
            elif refining_line.refining_sample_id_1 == res.refining_sample_id:
                refining_line.reference_sample_analysis = res.actual_result
            elif refining_line.refining_sample_id_2 == res.refining_sample_id:
                refining_line.actual_result = res.actual_result
            else:
                raise Warning("Please make sure the selected sample is added in Copper treatment costs")

        # get_refining_cost = self.env['copper.refining.cost'].search([('sample_ct_id','=',container_id.id),('copper_cost_id','=',res.project_id.id)],limit=1)
        # if not get_refining_cost:
        #     raise Warning("Please make sure copper treatment costs have these selected container")
        # get_refining_cost.reference_sample_analysis = res.actual_result

        return res
    
    def write(self, vals):
        res = super(CopperAnalysisResult, self).write(vals)

        if math.ceil(self.quantity)==0:
            raise Warning("Please add the quantity in copper analysis")

        if math.ceil(self.estimated_result)==0:
            raise Warning("Please add the Estimated Result in copper analysis")
        
        if math.ceil(self.actual_result)==0:
            raise Warning("Please add the Actual Result in copper analysis")

        if vals.get('actual_result'):
            container_id = self.env['project.container'].search([('name','=',self.container_id.name)],limit=1)

            if not container_id:
                raise Warning("Please make sure the selected container is updated in copper treatment.")

            refining_obj = self.env['copper.refining.cost'].search([('sample_ct_id','=',container_id.id),('copper_cost_id','=',self.project_id.id)])
            for refining_line in refining_obj:
                if refining_line.refining_sample_id == self.refining_sample_id:
                    refining_line.analysis_for_certification = vals.get('actual_result')
                elif refining_line.refining_sample_id_1 == self.refining_sample_id:
                    refining_line.reference_sample_analysis = vals.get('actual_result')
                elif refining_line.refining_sample_id_2 == self.refining_sample_id:
                    refining_line.actual_result = vals.get('actual_result')
                else:
                    raise Warning("Please make sure the selected sample is added in Copper treatment costs")

            # get_refining_cost = self.env['copper.refining.cost'].search([('sample_ct_id','=',container_id.id),('copper_cost_id','=',self.project_id.id)],limit=1)
            # if not get_refining_cost:
            #     raise Warning("Please make sure copper treatment costs have these selected container")
            # get_refining_cost.reference_sample_analysis = vals.get('actual_result')

        return res


class RhodiumAnalysisResult(models.Model):
    _name = "rhodium.analysis.result"
    _description = "Rhodium Analysis Result"

    laboratory_id = fields.Many2one(comodel_name='laboratory.report', string="Laboratory Report")

    project_id = fields.Many2one(comodel_name='project.entries', string="Project Entries", related="laboratory_id.project_id")

    container_id = fields.Many2one(comodel_name="refining.containers", string="Container")

    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')

    quantity = fields.Float(string="Taille de l'échantillon", digits=(16,4))
    estimated_result = fields.Float(string="Estimated Result", digits=(16,4))
    actual_result = fields.Float(string="Actual Result", digits=(16,4))

    @api.model
    def create(self, vals):

        if math.ceil(vals.get('quantity'))==0:
            raise Warning("Please add the quantity in rhodium analysis")

        if math.ceil(vals.get('estimated_result'))==0:
            raise Warning("Please add the Estimated Result in rhodium analysis")
        
        if math.ceil(vals.get('actual_result'))==0:
            raise Warning("Please add the Actual Result in rhodium analysis")


        res = super(RhodiumAnalysisResult, self).create(vals)

        container_id = self.env['project.container'].search([('name','=',res.container_id.name)],limit=1)

        if not container_id:
            raise Warning("Please make sure the selected container is updated in rhodium treatment.")

        refining_obj = self.env['rhodium.refining.cost'].search([('sample_ct_id','=',container_id.id),('rhodium_cost_id','=',res.project_id.id)])
        for refining_line in refining_obj:
            if refining_line.refining_sample_id == res.refining_sample_id:
                refining_line.analysis_for_certification = res.actual_result
            elif refining_line.refining_sample_id_1 == res.refining_sample_id:
                refining_line.reference_sample_analysis = res.actual_result
            elif refining_line.refining_sample_id_2 == res.refining_sample_id:
                refining_line.actual_result = res.actual_result
            else:
                raise Warning("Please make sure the selected sample is added in Rhodium treatment costs")

        # get_refining_cost = self.env['rhodium.refining.cost'].search([('sample_ct_id','=',container_id.id),('rhodium_cost_id','=',res.project_id.id)],limit=1)
        # if not get_refining_cost:
        #     raise Warning("Please make sure rhodium treatment costs have these selected container")
        # get_refining_cost.reference_sample_analysis = res.actual_result

        return res
    
    def write(self, vals):
        res = super(RhodiumAnalysisResult, self).write(vals)

        if math.ceil(self.quantity)==0:
            raise Warning("Please add the quantity in rhodium analysis")

        if math.ceil(self.estimated_result)==0:
            raise Warning("Please add the Estimated Result in rhodium analysis")
        
        if math.ceil(self.actual_result)==0:
            raise Warning("Please add the Actual Result in rhodium analysis")

        if vals.get('actual_result'):
            container_id = self.env['project.container'].search([('name','=',self.container_id.name)],limit=1)

            if not container_id:
                raise Warning("Please make sure the selected container is updated in rhodium treatment.")

            refining_obj = self.env['rhodium.refining.cost'].search([('sample_ct_id','=',container_id.id),('rhodium_cost_id','=',self.project_id.id)])
            for refining_line in refining_obj:
                if refining_line.refining_sample_id == self.refining_sample_id:
                    refining_line.analysis_for_certification = vals.get('actual_result')
                elif refining_line.refining_sample_id_1 == self.refining_sample_id:
                    refining_line.reference_sample_analysis = vals.get('actual_result')
                elif refining_line.refining_sample_id_2 == self.refining_sample_id:
                    refining_line.actual_result = vals.get('actual_result')
                else:
                    raise Warning("Please make sure the selected sample is added in Rhodium treatment costs")

            # get_refining_cost = self.env['rhodium.refining.cost'].search([('sample_ct_id','=',container_id.id),('rhodium_cost_id','=',self.project_id.id)],limit=1)
            # if not get_refining_cost:
            #     raise Warning("Please make sure rhodium treatment costs have these selected container")
            # get_refining_cost.reference_sample_analysis = vals.get('actual_result')

        return res

class RutheniumAnalysisResult(models.Model):
    _name = "ruthenium.analysis.result"
    _description = "Ruthenium Analysis Result"

    laboratory_id = fields.Many2one(comodel_name='laboratory.report', string="Laboratory Report")

    project_id = fields.Many2one(comodel_name='project.entries', string="Project Entries", related="laboratory_id.project_id")

    container_id = fields.Many2one(comodel_name="refining.containers", string="Container")

    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')

    quantity = fields.Float(string="Taille de l'échantillon", digits=(16,4))
    estimated_result = fields.Float(string="Estimated Result", digits=(16,4))
    actual_result = fields.Float(string="Actual Result", digits=(16,4))


    @api.model
    def create(self, vals):

        if math.ceil(vals.get('quantity'))==0:
            raise Warning("Please add the quantity in ruthenium analysis")

        if math.ceil(vals.get('estimated_result'))==0:
            raise Warning("Please add the Estimated Result in ruthenium analysis")
        
        if math.ceil(vals.get('actual_result'))==0:
            raise Warning("Please add the Actual Result in ruthenium analysis")

        res = super(RutheniumAnalysisResult, self).create(vals)

        container_id = self.env['project.container'].search([('name','=',res.container_id.name)],limit=1)

        if not container_id:
            raise Warning("Please make sure the selected container is updated in ruthenium treatment.")

        refining_obj = self.env['ruthenium.refining.cost'].search([('sample_ct_id','=',container_id.id),('ruthenium_cost_id','=',res.project_id.id)])
        for refining_line in refining_obj:
            if refining_line.refining_sample_id == res.refining_sample_id:
                refining_line.analysis_for_certification = res.actual_result
            elif refining_line.refining_sample_id_1 == res.refining_sample_id:
                refining_line.reference_sample_analysis = res.actual_result
            elif refining_line.refining_sample_id_2 == res.refining_sample_id:
                refining_line.actual_result = res.actual_result
            else:
                raise Warning("Please make sure the selected sample is added in Ruthenium treatment costs")

        # get_refining_cost = self.env['ruthenium.refining.cost'].search([('sample_ct_id','=',container_id.id),('ruthenium_cost_id','=',res.project_id.id)],limit=1)
        # if not get_refining_cost:
        #     raise Warning("Please make sure ruthenium treatment costs have these selected container")
        # get_refining_cost.reference_sample_analysis = res.actual_result

        return res
    
    def write(self, vals):
        res = super(RutheniumAnalysisResult, self).write(vals)

        if math.ceil(self.quantity)==0:
            raise Warning("Please add the quantity in ruthenium analysis")

        if math.ceil(self.estimated_result)==0:
            raise Warning("Please add the Estimated Result in ruthenium analysis")
        
        if math.ceil(self.actual_result)==0:
            raise Warning("Please add the Actual Result in ruthenium analysis")

        if vals.get('actual_result'):
            container_id = self.env['project.container'].search([('name','=',self.container_id.name)],limit=1)

            if not container_id:
                raise Warning("Please make sure the selected container is updated in ruthenium treatment.")

            refining_obj = self.env['ruthenium.refining.cost'].search([('sample_ct_id','=',container_id.id),('ruthenium_cost_id','=',self.project_id.id)])
            for refining_line in refining_obj:
                if refining_line.refining_sample_id == self.refining_sample_id:
                    refining_line.analysis_for_certification = vals.get('actual_result')
                elif refining_line.refining_sample_id_1 == self.refining_sample_id:
                    refining_line.reference_sample_analysis = vals.get('actual_result')
                elif refining_line.refining_sample_id_2 == self.refining_sample_id:
                    refining_line.actual_result = vals.get('actual_result')
                else:
                    raise Warning("Please make sure the selected sample is added in Ruthenium treatment costs")

            # get_refining_cost = self.env['ruthenium.refining.cost'].search([('sample_ct_id','=',container_id.id),('ruthenium_cost_id','=',self.project_id.id)],limit=1)
            # if not get_refining_cost:
            #     raise Warning("Please make sure ruthenium treatment costs have these selected container")
            # get_refining_cost.reference_sample_analysis = vals.get('actual_result')

        return res

class IridiumAnalysisResult(models.Model):
    _name = "iridium.analysis.result"
    _description = "Iridium Analysis Result"

    laboratory_id = fields.Many2one(comodel_name='laboratory.report', string="Laboratory Report")

    project_id = fields.Many2one(comodel_name='project.entries', string="Project Entries", related="laboratory_id.project_id")

    container_id = fields.Many2one(comodel_name="refining.containers", string="Container")

    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')

    quantity = fields.Float(string="Taille de l'échantillon", digits=(16,4))
    estimated_result = fields.Float(string="Estimated Result", digits=(16,4))
    actual_result = fields.Float(string="Actual Result", digits=(16,4))

    @api.model
    def create(self, vals):

        if math.ceil(vals.get('quantity'))==0:
            raise Warning("Please add the quantity in iridium analysis")

        if math.ceil(vals.get('estimated_result'))==0:
            raise Warning("Please add the Estimated Result in iridium analysis")
        
        if math.ceil(vals.get('actual_result'))==0:
            raise Warning("Please add the Actual Result in iridium analysis")

        res = super(IridiumAnalysisResult, self).create(vals)

        container_id = self.env['project.container'].search([('name','=',res.container_id.name)],limit=1)

        if not container_id:
            raise Warning("Please make sure the selected container is updated in iridium treatment.")

        refining_obj = self.env['iridium.refining.cost'].search([('sample_ct_id','=',container_id.id),('ididium_cost_id','=',res.project_id.id)])
        for refining_line in refining_obj:
            if refining_line.refining_sample_id == res.refining_sample_id:
                refining_line.analysis_for_certification = res.actual_result
            elif refining_line.refining_sample_id_1 == res.refining_sample_id:
                refining_line.reference_sample_analysis = res.actual_result
            elif refining_line.refining_sample_id_2 == res.refining_sample_id:
                refining_line.actual_result = res.actual_result
            else:
                raise Warning("Please make sure the selected sample is added in Iridium treatment costs")

        # get_refining_cost = self.env['iridium.refining.cost'].search([('sample_ct_id','=',container_id.id),('iridium_cost_id','=',res.project_id.id)],limit=1)
        # if not get_refining_cost:
        #     raise Warning("Please make sure iridium treatment costs have these selected container")
        # get_refining_cost.reference_sample_analysis = res.actual_result

        return res
    
    def write(self, vals):
        res = super(IridiumAnalysisResult, self).write(vals)

        if math.ceil(self.quantity)==0:
            raise Warning("Please add the quantity in iridium analysis")

        if math.ceil(self.estimated_result)==0:
            raise Warning("Please add the Estimated Result in iridium analysis")
        
        if math.ceil(self.actual_result)==0:
            raise Warning("Please add the Actual Result in iridium analysis")
        

        if vals.get('actual_result'):
            container_id = self.env['project.container'].search([('name','=',self.container_id.name)],limit=1)

            if not container_id:
                raise Warning("Please make sure the selected container is updated in iridium treatment.")

            refining_obj = self.env['iridium.refining.cost'].search([('sample_ct_id','=',container_id.id),('iridium_cost_id','=',self.project_id.id)])
            for refining_line in refining_obj:
                if refining_line.refining_sample_id == self.refining_sample_id:
                    refining_line.analysis_for_certification = vals.get('actual_result')
                elif refining_line.refining_sample_id_1 == self.refining_sample_id:
                    refining_line.reference_sample_analysis = vals.get('actual_result')
                elif refining_line.refining_sample_id_2 == self.refining_sample_id:
                    refining_line.actual_result = vals.get('actual_result')
                else:
                    raise Warning("Please make sure the selected sample is added in Iridium treatment costs")

            # get_refining_cost = self.env['iridium.refining.cost'].search([('sample_ct_id','=',container_id.id),('iridium_cost_id','=',self.project_id.id)],limit=1)
            # if not get_refining_cost:
            #     raise Warning("Please make sure iridium treatment costs have these selected container")
            # get_refining_cost.reference_sample_analysis = vals.get('actual_result')

        return res


