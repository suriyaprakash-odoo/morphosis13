odoo.define('web_pdf_report_preview', function(require) {
"use strict";
    var ActionManager = require('web.ActionManager');
    var core = require('web.core');
    var framework = require('web.framework');
    var session = require('web.session');
    var _t = core._t;
    var _lt = core._lt;


    ActionManager.include({
        _downloadReport2: function (url) {
            var self = this;
            framework.blockUI();
            var type = 'qweb-' + url.split('/')[2];
            var data =  {
                    data: JSON.stringify([url, type]),
                    token: new Date().getTime(),
                    context: JSON.stringify(session.user_context),
                }
            var url = session.url('/report/download', data);
            window.open(url, 'report', 'width=1000,height=700');
            framework.unblockUI();
        },
        _triggerDownload: function (action, options, type){
            var self = this;
            var reportUrls = this._makeReportUrls(action);
            return this._downloadReport2(reportUrls[type]);
            // return this._downloadReport(reportUrls[type]).then(function () {
            //     if (action.close_on_report_download) {
            //         var closeAction = { type: 'ir.actions.act_window_close' };
            //         return self.doAction(closeAction, _.pick(options, 'on_close'));
            //     } else {
            //         return options.on_close();
            //     }
            // });
        },
    });
});