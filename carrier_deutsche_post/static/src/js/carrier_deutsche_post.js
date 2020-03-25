odoo.define('nitrokey_carrier_deutsche_post.actionmanager', function (require) {
"use strict";

var ActionManager = require('web.ActionManager');
var config = require('web.config');
var framework = require('web.framework');

ActionManager.include({
    _executeURLAction: function (action, options) {
        var url = action.url;
        if (config.debug && url && url.length && url[0] === '/') {
            url = $.param.querystring(url, {debug: config.debug});
        }
        if (action.target === 'download') {
            framework.redirect(url);
        }
        else if (action.target === 'self') {
            framework.redirect(url);
            return $.Deferred();
        } else {
            var w = window.open(url, '_blank');
            if (!w || w.closed || typeof w.closed === 'undefined') {
                var message = _t('A popup window has been blocked. You ' +
                             'may need to change your browser settings to allow ' +
                             'popup windows for this page.');
                this.do_warn(_t('Warning'), message, true);
            }
        }

        options.on_close();

        return $.when();
    },

});

});
