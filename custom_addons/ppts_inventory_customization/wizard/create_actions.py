from odoo import api, fields, models,_
from datetime import timedelta, datetime
from odoo.exceptions import UserError

class CreateActionWizard(models.TransientModel):
    _name = 'create.action.wizard'

    container_ids = fields.Many2many('project.container', string='Selected Containers')
    container_line = fields.One2many('container.wizard.line','wizard_id',string="Containers")
    action_date = fields.Date("Action Date")
    action_date_end = fields.Date("Action End Date")
    worker_ids = fields.Many2many('hr.employee', string="Assigned Workers",domain="[('is_worker','=', True)]")
    supervisor_id = fields.Many2one("hr.employee", string="Supervisor",domain="[('is_supervisor','=', True)]")

    def action_create_plan(self):
        created_lst = []
        for container in self.container_line:
            if container.container_id.state not in ('new','confirmed'):
                created_lst.append(container.container_id.name)
            else:
                if self.action_date < fields.Datetime.now().date() or  self.action_date_end < fields.Datetime.now().date():
                    raise UserError(_('You can not select previous date for action!'))
                else:
                    if self.action_date > datetime.now().date():
                        container.container_id.write({'state': 'planned'})
                    elif self.action_date == datetime.now().date():
                        container.container_id.write({'state':'in_progress'})
                    else:
                        raise UserError(_('You can not select previous date for action!'))

                    container.container_id.action_date = self.action_date
                    container.container_id.action_date_end = self.action_date_end
                    container.container_id.worker_ids = self.worker_ids
                    container.container_id.supervisor_id = self.supervisor_id
                    # container.container_id.state = 'in_progress'
                    container.container_id.external_action_type = container.external_action_type

                    start_date = datetime.strptime(str(self.action_date), '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
                    stop_date = datetime.strptime(str(self.action_date_end), '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
                    self.env['calendar.event'].create({
                            'name' : container.container_id.name,
                            'start' : start_date,
                            'stop' : stop_date,
                            'duration' : 1,
                            'state' : 'draft',
                            'container_id' : container.container_id.id,
                            'project_id' : container.container_id.project_id.id,
                            'main_product_id' : container.container_id.main_product_id.id,
                            'sub_product_id' : container.container_id.sub_product_id.id,
                            'action_type' : container.container_id.action_type,
                            'external_action_type' : container.container_id.external_action_type,
                            'supervisor_id' : self.supervisor_id.id,
                            'worker_ids' : self.worker_ids.ids,
                            'status' : container.container_id.state,
                            'production_calendar' : True
                        })
        self.env.cr.commit()
        if created_lst:
            cr_lst = 'You can not schedule a new action for planned Containers'+str(created_lst)[1:-1]
            raise UserError(_(cr_lst))

class WizardLine(models.TransientModel):
    _name = 'container.wizard.line'

    wizard_id = fields.Many2one("create.action.wizard")
    container_id = fields.Many2one('project.container', string='Container')
    external_action_type = fields.Selection([('sorting', 'Sorting'),
                                             ('refining', 'Refining')], string="Action Type")


