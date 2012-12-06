/*
 * jQuery plug-in: toggleInputValue
 * Applying this jQuery command to input elements, causes its value to become a
 * default value. This default value is removed when the input gets focus. You
 * know... like it's done all over the intertubes.
 */
$.fn.toggleInputValue = function() {
    return $(this).each(function() {
        var input = $(this);
        var default_value = input.val();

        input.focus(function() {
            if (input.val() == default_value) input.val("");
        }).blur(function(){
            if (input.val().length == 0) input.val(default_value);
        });
    });
};

/*
 * jQuery plug-in: expander
 * Turn the received jQuery elements into expanders. If the element has
 * children, clicking the expander will toggle the children. Otherwise the
 * element's `.next()` element (sibling) is toggled. Passing `{ toggleSibling:
 * true }` will force the element's sibling to be toggled (even if it has
 * children).
 */
$.fn.expander = function(options) {
    if (typeof options !== 'object') options = {};
    return $(this).each(function() {
        var $this = $(this), data = $this.data('expander');

        if (!data || !data.isExpander) {
            if ($this.children().length && !options.toggleSibling) {
                $this.click(function() {
                    $this.children().toggle();
                    return false;
                }).children().hide();
            } else {
                $this.click(function() {
                    $this.next().toggle();
                    return false;
                }).next().hide();
            }
            $this.prepend($(document.createElement('span')).text('+'))
            $this.data('expander', { isExpander: true });
        }
    });
};

/*
 * jQuery plug-in: clientwindow
 * A client window contains the data for a single probed client. The following
 * div-structure is created with the matched element being the root.
 * .client-window
 *   .cwin-titlebar
 *     .cwin-title
 *     .cwin-close
 *     .cwin-reload
 *   .cwin-content
 */
(function($) {
    var methods = {
        init: function(options) {
            var settings = $.extend({ title: '[no title]' }, options);

            return this.each(function() {
                var $this = $(this), data = $this.data('clientwindow');

                if (!data) {
                    // Build the client window (from scratch)
                    $this.children().remove();
                    $this.append(
                        $(document.createElement('div')).addClass('cwin-titlebar').append(
                            $(document.createElement('div')).addClass('cwin-title')
                                .text(settings.title),
                            $(document.createElement('div')).addClass('cwin-close')
                                .append(
                                    $(document.createElement('a'))
                                        .text('x').attr('href', '#')
                                        .click(function() { $this.hide(150); })
                                ),
                            $(document.createElement('div')).addClass('cwin-reload')
                                .append(
                                    $(document.createElement('a'))
                                        .text('⟳').attr('href', '#')
                                        .click(function() { Snoopy.loadClient(settings.title); })
                                )
                        ),
                        $(document.createElement('div')).addClass('cwin-content')
                    );

                    $this.data('clientwindow', { initialised: true });
                }

                if (!$this.hasClass('client-window')) {
                    $this.addClass('client-window');
                }

                $this.width(450).height(400)
                    .draggable({
                        containment: 'parent',
                        handle: '.cwin-titlebar',
                    })
                    .resizable({
                        minWidth: 450, minHeight: 400,
                    });
            });
        }
    };

    $.fn.clientwindow = function(method) {
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' +  method + ' does not exist on jQuery.clientwindow');
        }
    };
})(jQuery);

/*
 * jQuery plug-in: clientDataHandlers
 * Creates one section that is meant to be used in the client window content
 * div. The title should be specified as `{ title: 'Section title' }`. The
 * following div-structure is created with the matched element at the root:
 * .data-section
 *   .section-title
 *   .section-content
 */
(function($) {
    var methods = {
        init: function(options) {
            var settings = $.extend({ title: 'Client data' }, options);

            return this.each(function() {
                var $this = $(this), data = $this.data('datasection');

                if (!data) {
                    var $title = $(document.createElement('div'))
                        .addClass('section-title')
                        .text(settings.title);
                    $this.children().remove();
                    $this.append(
                        $title,
                        $(document.createElement('div'))
                            .addClass('section-content')
                    );
                    $title.expander({ toggleSibling: true });
                    $this.data('datasection', { initialised: true });
                }

                if (!$this.hasClass('data-section')) {
                    $this.addClass('data-section');
                }
            });
        }
    };

    $.fn.clientDataSection = function(method) {
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error('Method ' +  method + ' does not exist on jQuery.clientDataSection');
        }
    };
})(jQuery);

Snoopy = {
    DEBUG: true,
    divs: {},
    clientDivs: {},
    clientDataHandlers: {},

    init: function() {
        this.elems = {
            drones:      $('#drones-list'),
            clientlist:  $('#client-list'),
            clientsarea: $('#clients-area')
        };
        this.elems.drones.change(Snoopy.loadClientMacs);
        this.elems.clientlist.click(Snoopy.loadClient);

        Snoopy.loadPlugins();
        Snoopy.loadDrones();
    },

    error: function(msg) {
        if (msg instanceof Array) {
            for (var i in msg) {
                alert(msg[i]);
            }
        } else if (msg instanceof String) {
            alert('Error: ' + msg);
        }
    },

    loadPlugins: function() {
        $.post('/plugin/list')
            .success(function(response) {
                if (response.success !== true) {
                    if (response.errors) {
                        Snoopy.error(response.errors);
                    } else {
                        Snoopy.error('Error!');
                    }
                    return;
                }

                for (var i=0; i < response.plugins.length; i++) {
                    $.getScript(response.plugins[i].jsurl);
                }
            })
            .error(function(response) {
                Snoopy.error('Error (' + response.status + ')');
            });
    },

    loadDrones: function() {
        var dronesList = Snoopy.elems.drones;
        // TODO Add loading mask
        $.post('/drone/list')
            .success(function(response) {
                if (response.success !== true) {
                    if (response.errors) {
                        if (response.errors.length == 1)
                            Snoopy.error('Error: ' + response.errors[0]);
                        else {
                            var errstr = 'Errors:\n';
                            for (var i=0; i < response.errors.length; i++)
                                errstr += response.errors[i] + '\n';
                            Snoopy.error(errstr);
                        }
                    } else {
                        Snoopy.error('Error!');
                    }
                    return;
                }

                $('option', dronesList).remove();
                dronesList.append(
                    $(document.createElement('option'))
                        .attr({ value: '*' }).css({ display: 'none' }),
                    $(document.createElement('option'))
                        .attr({ value: '*' }).text('All drones')
                );
                for (var i=0; i < response.drones.length; i++) {
                    var droneinfo = response.drones[i];
                    dronesList.append(
                        $(document.createElement('option'))
                            .attr({ value: droneinfo.devname })
                            .text(droneinfo.devname + ' (' + droneinfo.n_macs + ')')
                    );
                }

                if (Snoopy.DEBUG) {
                    dronesList.val('*');
                    Snoopy.loadClientMacs();
                }
            })
            .error(function(response) {
                Snoopy.error('Error (' + response.status + ')');
            });
    },

    loadClientMacs: function() {
        var clientList = Snoopy.elems.clientlist,
            monitor = Snoopy.elems.drones.val();
        // TODO Add loading mask
        $.post('/client/list', {monitor: monitor})
            .success(function(response) {
                if (response.success !== true) {
                    if (response.errors) {
                        Snoopy.error(response.errors);
                    } else {
                        Snoopy.error('Error!');
                    }
                    return;
                }

                $('option', clientList).remove();
                for (var i=0; i < response.clients.length; i++) {
                    var clinfo = response.clients[i];
                    clientList.append(
                        $(document.createElement('option'))
                            .attr({ value: clinfo.mac })
                            .text(clinfo.mac)
                    );
                }

                if (Snoopy.DEBUG) {
                    clientList.val($('option:first-child', clientList).val());
                    Snoopy.loadClient();
                }
            })
            .error(function(response) {
                Snoopy.error('Error (' + response.status + ')');
            });
    },

    loadClient: function() {
        var mac = Snoopy.elems.clientlist.val();
        if (!mac) { return; }

        if (Snoopy.clientDivs.hasOwnProperty(mac)) {
            Snoopy.clientDivs[mac].hide(150);
            Snoopy.clientDivs[mac].show(150);
        } else {
            var clwin = $(document.createElement('div'))
                .clientwindow({ title: mac });
            Snoopy.elems.clientsarea.append(clwin);
            Snoopy.clientDivs[mac] = clwin;
        }
        Snoopy.loadClientData(mac);
    },

    loadClientData: function(mac) {
        var clWin = Snoopy.clientDivs[mac];
        if (!clWin) { return; }

        $.post('/client/data/get', { mac: mac })
            .success(function(response) {
                if (response.success !== true) {
                    if (response.errors) {
                        Snoopy.error(response.errors);
                    } else {
                        Snoopy.error('Error!');
                    }
                    return;
                }
                $('.data-section', clWin).remove();
                for (var secname in response.client_data) {
                    if (!response.client_data.hasOwnProperty(secname)) { continue; }
                    var sectitle = response.client_data[secname].title || secname,
                        $sec = $(document.createElement('div')).clientDataSection({ title: sectitle });
                    Snoopy.handleSectionData(secname, $sec, response.client_data[secname].data);
                    $('.cwin-content', clWin).append($sec);
                }
            })
            .error(function(response) {
                Snoopy.error('Error (' + response.status + ')');
            });
    },

    registerPlugin: function(secname, handler) {
        if (!Snoopy.clientDataHandlers.hasOwnProperty(secname)) {
            Snoopy.clientDataHandlers[secname] = [];
        }
        Snoopy.clientDataHandlers[secname].push(handler);
    },

    handleSectionData: function(secname, $sec, secdata) {
        var handlers = null;
        if (Snoopy.clientDataHandlers.hasOwnProperty(secname)) {
            handlers = Snoopy.clientDataHandlers[secname];
        } else {
            handlers = Snoopy.clientDataHandlers['generic'] || [];
        }
        for (var i=0; i < handlers.length; i++) {
            handlers[i]($sec, secdata);
        }
    },

    util: {
        dateFormat: function(timestamp) {
            var d = new Date(timestamp * 1000),
                month = [
                    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
                ][d.getMonth()];
            return d.getDate() + ' ' + month + ' ' + d.getFullYear() + ', ' +
                d.getHours() + ':' + d.getMinutes();
        },

        periodFormat: function(ts1, ts2) {
            var d1 = new Date(ts1 * 1000),
                d2 = new Date(ts2 * 1000),
                period = Snoopy.util.dateFormat(ts1) + ' - ';
            if (d1.getDate()     != d2.getDate() ||
                d1.getMonth()    != d2.getMonth() ||
                d1.getFullYear() != d2.getFullYear()) {
                period += Snoopy.util.dateFormat(ts2);
            } else {
                period += d2.getHours() + ':' + d2.getMinutes();
            }
            return period;
        },

        loadGoogleMaps: function() {
            if (Snoopy.util.isGoogleMapsLoaded) {
                return true;
            }

            if (Snoopy.util.isGoogleMapsLoading) {
                return false;
            }

            (function() {
                var script = document.createElement("script"),
                    apikey = 'AIzaSyDzWo9dRcCkPnpV6biA6lJUyLCzYZsGfhY';
                script.type = "text/javascript";
                script.src = 'https://maps.googleapis.com/maps/api/js?key=' + apikey + '&sensor=false&callback=Snoopy.util.googleMapsInit&async=2';
                document.body.appendChild(script);
            })();
            Snoopy.util.isGoogleMapsLoading = true;
            return false;
        },

        googleMapsInit: function() {
            Snoopy.util.isGoogleMapsLoading = false;
            Snoopy.util.isGoogleMapsLoaded = true;
        }
    }
};

$(document).ready(function() {
    Snoopy.init();
});
